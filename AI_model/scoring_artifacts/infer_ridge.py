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
from fastembed import TextEmbedding

app = Flask(__name__)
CORS(app)


def load_scorer():
    with open(f"meta.json") as f:
        meta = json.load(f)

    # a small ONNX model fastembed
    model_name = meta.get(
        "fastembed_name", "sentence-transformers/all-MiniLM-L6-v2")
    embedder = TextEmbedding(model_name)
    reg = joblib.load(f"regressor.joblib")
    targets = meta["targets"]
    version = meta.get("version", "unknown")
    return embedder, reg, targets, version


def score_prompt(text: str):
    vec = np.asarray(list(EMBEDDER.embed([text])))[0]
    vec = vec.reshape(1, -1)
    p = REG.predict(vec)[0]
    p = np.clip(p, 1.0, 10.0)
    return dict(zip(TARGETS, [round(float(x), 1) for x in p]))


t0 = time.time()

EMBEDDER, REG, TARGETS, VERSION = load_scorer()
_ = list(EMBEDDER.embed(["warmup"]))


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
        scores = score_prompt(text)

        return scores
    finally:
        print('Evaluation complete')


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
