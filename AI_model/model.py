from flask import Flask, request, jsonify
import base64
import io
import uuid
import os

app = Flask(__name__)

@app.route('/get-results', methods=['POST'])
def getResults():
    data = request.get_json()
    return jsonify({"prompt": data,
                    "values": {"clarity": 9, "relevance": 7, "specificity": 8, "creativity": 9, "context": 10}})


@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json()
    if not data:
        return jsonify({'error':'Missing prompt'}), 400
    
    try:
        return jsonify(
            {"clarity": 9, "relevance": 7, "specificity": 8, "creativity": 9, "context": 10}
        )
    finally:
        print('Evaluation complete')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
