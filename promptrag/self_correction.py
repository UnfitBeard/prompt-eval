# self_correction.py
import re
import time
import math
import copy
from typing import List, Dict, Any, Optional

from promptrag.prompts import build_eval_user_message

from tqdm import tqdm
from chromadb.config import Settings
from chromadb import PersistentClient

import chromadb
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.messages import HumanMessage, SystemMessage
from utils import extract_json_inside_codeblock, clean_text
from prompts import EVAL_SYSTEM_PROMPT, IMPROVE_SYSTEM_PROMPT, build_eval_user_message, build_improve_user_message
from scorer import load_scorer, score_prompt, apply_vagueness_penalty, TARGETS
import os
import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()


# DEFAULTS / TUNING
DEFAULT_THRESHOLDS = {"overall": 7.0}   # average of 5 metrics
MIN_OVERALL_IMPROVEMENT = 0.3          # accept only if overall improves by this
MIN_METRIC_IMPROVEMENT = 0.4           # or at least two metrics up by this
MAX_CANDIDATES_PER_ROUND = 3
DEFAULT_MAX_RETRIES = 2


def _overall_score_from_final(final_scores: Dict[str, float]) -> float:
    vals = [v for v in (
        final_scores.get("clarity"),
        final_scores.get("context"),
        final_scores.get("relevance"),
        final_scores.get("specificity"),
        final_scores.get("creativity"),
    ) if v is not None]
    if not vals:
        return 0.0
    return sum(vals)/len(vals)


def passes_thresholds(final_scores: Dict[str, float], thresholds: Dict[str, float]) -> bool:
    # if threshold specifies overall, use overall. Otherwise check each metric if present.
    overall_target = thresholds.get("overall")
    if overall_target is not None:
        return _overall_score_from_final(final_scores) >= overall_target
    # per-metric fallback
    for k, v in thresholds.items():
        if final_scores.get(k, 0.0) < v:
            return False
    return True

# Simple acceptance validator: supports two forms:
# 1) checklist text: newline/comma-separated phrases that must appear in the prompt (or candidate) OR
# 2) JSON schema-ish: "keys: a,b,c" (case-insensitive)


def validator_passes(prompt_text: str, acceptance: Optional[str]) -> Dict[str, Any]:
    """
    Returns dict { pass: bool, missing: [..], reason: str }
    """
    if not acceptance or acceptance.strip() == "":
        return {"pass": True, "missing": [], "reason": "no acceptance criteria"}

    text = acceptance.strip()
    # naive parse: if looks like 'keys:' then parse keys
    lower = text.lower()
    if lower.startswith("keys:") or "keys:" in lower:
        # parse comma separated keys
        after = text.split(":", 1)[1]
        keys = [k.strip() for k in after.replace(
            "\n", ",").split(",") if k.strip()]
        missing = []
        for k in keys:
            if k.lower() not in prompt_text.lower():
                missing.append(k)
        return {"pass": len(missing) == 0, "missing": missing, "reason": f"required keys {keys}"}

    # fallback: split into checklist items
    # split by newline or semicolon or comma if many
    items = [s.strip() for s in re.split(r"[\n;]+", text) if s.strip()]
    if len(items) == 1 and "," in items[0]:
        items = [s.strip() for s in items[0].split(",") if s.strip()]

    missing = []
    for it in items:
        if it.lower() not in prompt_text.lower():
            missing.append(it)
    return {"pass": len(missing) == 0, "missing": missing, "reason": "checklist"}


def extract_candidates_from_llm_eval(llm_eval: Dict[str, Any]) -> List[str]:
    """Return candidate prompt strings from LLM eval parsed JSON (rewriteVersions or other keys)."""
    out = []
    if not llm_eval:
        return out
    if isinstance(llm_eval.get("rewriteVersions"), list):
        for v in llm_eval["rewriteVersions"]:
            content = v.get("content") or v.get("prompt") or None
            if content and isinstance(content, str):
                out.append(content)
    # also check for fields like "improved_prompt" or "candidates"
    if isinstance(llm_eval.get("improved_prompt"), str):
        out.append(llm_eval["improved_prompt"])
    if isinstance(llm_eval.get("candidates"), list):
        for c in llm_eval["candidates"]:
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, dict) and "content" in c:
                out.append(c["content"])
    # dedupe and limit
    seen = set()
    res = []
    for s in out:
        if s and s not in seen:
            seen.add(s)
            res.append(s)
    return res


def score_and_final(prompt_text: str):
    """Return (base_scores, final_scores) using your scorer & vagueness penalty"""
    base_scores = score_prompt(
        prompt_text, EMBEDDER_SCORER, REG, SCALER, TARGETS_SCORER)
    final_scores = apply_vagueness_penalty(base_scores, prompt_text)
    return base_scores, final_scores


def select_best_candidate(candidates_info: List[Dict[str, Any]], current_best_final: Dict[str, float]):
    """
    Choose the candidate with highest overall score; require minimal improvement if present.
    candidates_info: list of { prompt, base_scores, final_scores, validator_result, llm_eval }
    returns (best_info, improved_bool)
    """
    best = None
    best_overall = _overall_score_from_final(
        current_best_final) if current_best_final else -1.0
    improved = False
    for c in candidates_info:
        ov = _overall_score_from_final(c["final_scores"])
        if best is None or ov > best_overall and ov > _overall_score_from_final(best["final_scores"] if best else {"clarity": 0}):
            best = c
            best_overall = ov
    if best:
        improved = (best_overall - _overall_score_from_final(current_best_final)
                    ) >= MIN_OVERALL_IMPROVEMENT
    return best, improved


def self_correct(
    original_prompt: str,
    form: Optional[Dict[str, Any]] = None,
    k: int = 6,
    max_retries: int = DEFAULT_MAX_RETRIES,
    thresholds: Optional[Dict[str, float]] = None,
    acceptance: Optional[str] = None,
    max_candidates_per_round: int = MAX_CANDIDATES_PER_ROUND,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Returns dict with:
      success: bool
      best: { prompt, base_scores, final_scores, validator_result, llm_eval }
      attempts: [ ... ]
    """
    thresholds = thresholds or DEFAULT_THRESHOLDS
    attempts = []
    start_time = time.time()

    # 0) initial score & retrieve & eval
    base_scores, final_scores = score_and_final(original_prompt)
    retrieved = _retrieve_similar(original_prompt, k=k)
    # LLM evaluator
    sys_msg = SystemMessage(content=SYSTEM_PROMPT)
    user_msg = HumanMessage(
        content=build_eval_user_message(original_prompt, retrieved))
    llm_resp = llm.invoke([sys_msg, user_msg])
    parsed_eval = _parse_json_response(llm_resp.content)

    validator_res = validator_passes(original_prompt, acceptance)
    attempt0 = {
        "round": 0,
        "prompt": original_prompt,
        "base_scores": base_scores,
        "final_scores": final_scores,
        "validator": validator_res,
        "llm_evaluation": parsed_eval,
        "retrieved_count": len(retrieved),
        "timestamp": time.time()
    }
    attempts.append(attempt0)

    # quick accept
    if passes_thresholds(final_scores, thresholds) and validator_res["pass"]:
        return {"success": True, "best": attempt0, "attempts": attempts, "elapsed": time.time()-start_time}

    # gather initial candidates from the llm eval
    candidates = extract_candidates_from_llm_eval(
        parsed_eval)[:max_candidates_per_round]

    # if none, produce candidates by calling IMPROVE_SYSTEM_PROMPT
    if not candidates:
        sys_msg2 = SystemMessage(content=IMPROVE_SYSTEM_PROMPT)
        user_msg2 = HumanMessage(
            content=build_improve_user_message(original_prompt, retrieved))
        r2 = llm.invoke([sys_msg2, user_msg2])
        p2 = _parse_json_response(r2.content)
        candidates = extract_candidates_from_llm_eval(
            p2)[:max_candidates_per_round]
        # record raw improve
        attempts.append({
            "round": 0.5,
            "action": "generate_initial_candidates",
            "raw_llm": r2.content,
            "parsed": p2,
            "timestamp": time.time()
        })

    # keep track of the best so far (start = original)
    best_so_far = {
        "prompt": original_prompt,
        "base_scores": base_scores,
        "final_scores": final_scores,
        "validator": validator_res,
        "llm_evaluation": parsed_eval
    }

    # main retry loop
    for retry in range(max_retries):
        round_idx = retry + 1
        if verbose:
            print(
                f"[self_correct] retry {round_idx}, candidates={len(candidates)}")

        cand_infos = []
        for cand in candidates[:max_candidates_per_round]:
            c_base, c_final = score_and_final(cand)
            c_validator = validator_passes(cand, acceptance)
            # quick accept check
            info = {
                "prompt": cand,
                "base_scores": c_base,
                "final_scores": c_final,
                "validator": c_validator,
                "timestamp": time.time()
            }
            cand_infos.append(info)
            attempts.append({"round": round_idx, "candidate_info": info})

            # if passes thresholds and validator & shows reasonable improvement, accept immediately
            if passes_thresholds(c_final, thresholds) and c_validator["pass"]:
                # check improvement heuristic
                if _overall_score_from_final(c_final) - _overall_score_from_final(best_so_far["final_scores"]) >= MIN_OVERALL_IMPROVEMENT:
                    best_so_far = info
                    return {"success": True, "best": best_so_far, "attempts": attempts, "elapsed": time.time()-start_time}
                else:
                    # accept if strictly higher and meets thresholds
                    if _overall_score_from_final(c_final) > _overall_score_from_final(best_so_far["final_scores"]):
                        best_so_far = info
                        # continue to try to find even better; but can return if you prefer immediate
        # end candidate loop

        # pick best candidate from this round (highest overall)
        round_best, improved = select_best_candidate(
            cand_infos, best_so_far["final_scores"])
        if round_best and improved:
            best_so_far = round_best
            return {"success": True, "best": best_so_far, "attempts": attempts, "elapsed": time.time()-start_time}

        # else produce new candidates using IMPROVE prompt with different temperature / hint
        # We adapt by asking the LLM to "focus on missing items: <missing>" and increase temperature
        # Compose improvement user message with context + failures
        missing = []
        # use missing from best_so_far.validator if present
        if best_so_far.get("validator") and isinstance(best_so_far["validator"].get("missing"), list):
            missing = best_so_far["validator"]["missing"]

        hint = ""
        if missing:
            hint = "MISSING_ITEMS: " + "; ".join(missing) + "."
        hint += " Try to be concise and explicitly include acceptance items."

        sys_msg3 = SystemMessage(content=IMPROVE_SYSTEM_PROMPT)
        # Append hint to the user message to guide improvements
        user_msg3_text = build_improve_user_message(
            original_prompt + "\n\n" + hint, retrieved)
        user_msg3 = HumanMessage(content=user_msg3_text)
        # vary temperature: 0.0, 0.2, 0.4 across retries
        temp = 0.0 if retry == 0 else (0.2 if retry == 1 else 0.4)
        # NOTE: adapt how you set temperature in your llm client; here we assume you can pass it via kwargs
        try:
            # if llm.invoke supports temperature param, pass it; else remove
            # adjust to pass temperature if supported
            r3 = llm.invoke([sys_msg3, user_msg3])
        except Exception as e:
            # if LLM call fails, break and return best_so_far
            attempts.append(
                {"error": str(e), "round": round_idx, "timestamp": time.time()})
            break
        p3 = _parse_json_response(r3.content)
        new_candidates = extract_candidates_from_llm_eval(
            p3)[:max_candidates_per_round]
        attempts.append({"round": round_idx + 0.5, "generated": new_candidates,
                        "raw_llm": r3.content, "parsed": p3})
        # dedupe candidates, prefer ones not seen before
        seen_prompts = {a["candidate_info"]["prompt"]
                        for a in attempts if a.get("candidate_info")}
        filtered = [c for c in new_candidates if c not in seen_prompts]
        if not filtered:
            # if nothing new, keep previous candidates (but avoid infinite loop)
            candidates = new_candidates
        else:
            candidates = filtered

    # exhausted retries -> return best so far (even if not passing)
    return {"success": False, "best": best_so_far, "attempts": attempts, "elapsed": time.time()-start_time}
