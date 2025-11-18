# scorer.py
import os
import re
import json
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

TARGETS = ["clarity", "context", "relevance", "specificity", "creativity"]
GENERIC_VERBS = {"make", "do", "write", "create", "build", "explain",
                 "describe", "talk", "summarize", "implement", "design", "draft"}
DETAIL_CUES = {"with", "including", "using", "for", "against", "step", "steps", "feature", "features", "requirements", "constraints", "kpi", "kpis", "diagram", "architecture",
               "lesson", "objectives", "assessment", "example", "template", "criteria", "strategy", "plan", "code", "review", "bug", "fix", "debug", "deployment", "performance", "security"}


def vagueness_score(text: str) -> float:
    t = text.lower().strip()
    words = re.findall(r"[a-z]+", t)
    wc = len(words)
    if wc == 0:
        return 1.0
    uniq = len(set(words))
    unique_ratio = uniq / wc
    gen_ratio = sum(1 for w in words if w in GENERIC_VERBS) / wc
    has_detail = any(c in t for c in DETAIL_CUES)
    has_digits = bool(re.search(r"\d", t))
    short_component = 1.0 if wc <= 4 else 0.0
    repetition_component = float(unique_ratio < 0.6)
    base = 0.4 * gen_ratio + 0.3 * (not has_detail) + 0.2 * (not has_digits)
    base += 0.3 * short_component + 0.2 * repetition_component
    return float(max(0.0, min(1.0, base)))


def apply_vagueness_penalty(scores: dict, text: str, strength: float = 4.5) -> dict:
    v = vagueness_score(text)
    out = {k: float(np.clip(scores[k] - strength * v, 1.0, 10.0))
           for k in TARGETS}
    return {k: round(val, 1) for k, val in out.items()}


def load_scorer(art_dir: str):
    with open(os.path.join(art_dir, "meta.json")) as f:
        meta = json.load(f)
    embedder = SentenceTransformer(meta["embedder_name"])
    reg = joblib.load(os.path.join(art_dir, "regressor.joblib"))
    scaler = joblib.load(os.path.join(art_dir, "feats_scaler.joblib"))
    targets = meta["targets"]
    version = meta.get("version", "unknown")
    return embedder, reg, scaler, targets, version


def prompt_features(text: str) -> np.ndarray:
    t = text.lower().strip()
    words = re.findall(r"[a-z]+", t)
    wc = len(words)
    uniq = len(set(words))
    unique_ratio = (uniq / wc) if wc else 0.0
    has_digits = 1.0 if re.search(r"\d", t) else 0.0
    has_detail = 1.0 if any(c in t for c in DETAIL_CUES) else 0.0
    gen_ratio = sum(1 for w in words if w in GENERIC_VERBS) / wc if wc else 1.0
    length_norm = min(wc, 64) / 64.0
    return np.array([length_norm, unique_ratio, has_digits, has_detail, gen_ratio], dtype=np.float32)


def score_prompt(text: str, embedder, reg, scaler, targets):
    v_embed = embedder.encode(
        [text], normalize_embeddings=True, show_progress_bar=False)
    v_feats = prompt_features(text).reshape(1, -1)
    v_feats_std = scaler.transform(v_feats)
    v = np.hstack([v_embed, v_feats_std])
    p = reg.predict(v)[0]
    p = np.clip(p, 1.0, 10.0)
    return {t: round(float(x), 1) for t, x in zip(targets, p)}
