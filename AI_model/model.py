from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io
import uuid
import os

app = Flask(__name__)
CORS(app)


@app.route('/get-results', methods=['POST'])
def getResults():
    data = request.get_json(silent=True)
    return jsonify({"prompt": data,
                    "values": {"clarity": 9, "relevance": 7, "specificity": 8, "creativity": 9, "context": 10}})


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
        return jsonify(
            {"clarity": 9, "relevance": 7, "specificity": 8,
                "creativity": 9, "context": 10}
        )
    finally:
        print('Evaluation complete')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
