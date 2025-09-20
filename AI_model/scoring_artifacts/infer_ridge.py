import time
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
import uuid
import os
import json
import joblib
import numpy as np
from sentence_transformers import SentenceTransformer

app = Flask(__name__)
CORS(app)


def load_scorer(art_dir="scoring_artifacts"):
    with open(f"{art_dir}/meta.json") as f:
        meta = json.load(f)
    embedder = SentenceTransformer(meta["embedder_name"])
    reg = joblib.load(f"{art_dir}/regressor.joblib")
    return embedder, reg, meta["targets"], meta["version"]


def score_prompt(text: str, embedder, reg, targets):
    v = embedder.encode([text], normalize_embeddings=True,
                        show_progress_bar=False)
    p = reg.predict(v)[0]
    p = np.clip(p, 1.0, 10.0)
    return dict(zip(targets, [round(float(x), 1) for x in p]))


t0 = time.time()

EMBEDDER, REG, TARGETS, VERSION = load_scorer()


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"ok": True}), 200


@app.route('/evaluate', methods=['POST'])
def evaluate():
    payload = request.get_json(silent=True)

    if isinstance(payload, dict):
        prompt = payload.get("prompt")
    else:
        prompt = payload

    if not prompt or not isinstance(prompt, str):
        return jsonify({'error': 'Missing prompt'}), 400

    try:
        print("version:", VERSION)
        text = prompt
        scores = score_prompt(text, EMBEDDER, REG, TARGETS)

        return scores
    finally:
        print('Evaluation complete')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
