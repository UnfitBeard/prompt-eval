# app.py (place this file in: AI_model/scoring_artifacts/app.py)
import time
import re
import json
import os
import joblib
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)

# ---------- constants ----------
HERE = os.path.dirname(os.path.abspath(__file__))
ART_DIR = HERE

GENERIC_VERBS = {
    "make", "do", "write", "create",
    "build", "explain", "describe", "talk", "summarize",
    "implement", "design", "draft"
}

DETAIL_CUES = {
    "with", "including", "using", "for", "against", "step", "steps", "feature", "features",
    "requirements", "constraints", "kpi", "kpis", "diagram", "architecture", "lesson",
    "objectives", "assessment", "example", "template", "criteria", "strategy", "plan",
    "code", "review", "bug", "fix", "debug", "deployment", "performance", "security"
}

TARGETS = ["clarity", "context", "relevance", "specificity", "creativity"]

# ---------- vagueness helpers ----------


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
    out = {}
    for k in TARGETS:
        val = float(scores[k])
        out[k] = float(np.clip(val - strength * v, 1.0, 10.0))
    return {k: round(v, 1) for k, v in out.items()}

# ---------- model loading & scoring ----------


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
    t = str(text).lower().strip()
    words = re.findall(r"[a-z]+", t)
    wc = len(words)
    uniq = len(set(words))
    unique_ratio = (uniq / wc) if wc else 0.0
    has_digits = 1.0 if re.search(r"\d", t) else 0.0
    has_detail = 1.0 if any(c in t for c in DETAIL_CUES) else 0.0
    gen_ratio = (sum(1 for w in words if w in GENERIC_VERBS) /
                 wc) if wc else 1.0
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


# ---------- global init ----------
t0 = time.time()
EMBEDDER, REG, SCALER, TARGETS, VERSION = load_scorer(ART_DIR)
_ = EMBEDDER.encode(["warmup"], normalize_embeddings=True,
                    show_progress_bar=False)
print(
    f"✅ Loaded artifacts from {ART_DIR} in {time.time() - t0:.2f}s, version={VERSION}")

# ---------- routes ----------


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"ok": True, "version": VERSION}), 200


@app.route('/evaluate', methods=['POST'])
def evaluate():
    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({'error': 'Missing payload'}), 400
    prompts = payload.get("prompt") if isinstance(payload, dict) else payload
    if isinstance(prompts, str):
        prompts = [prompts]
    if not isinstance(prompts, list) or not all(isinstance(p, str) for p in prompts):
        return jsonify({'error': 'Prompt(s) must be string or list of strings'}), 400

    results = []
    for prompt in prompts:
        base_scores = score_prompt(prompt, EMBEDDER, REG, SCALER, TARGETS)
        final_scores = apply_vagueness_penalty(
            base_scores, prompt, strength=4.5)
        results.append({
            "prompt": prompt,
            "base_scores": base_scores,
            "final_scores": final_scores
        })
    return jsonify({
        "version": VERSION,
        "results": results,
        "base_scores": base_scores,
        "final_scores": final_scores
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
