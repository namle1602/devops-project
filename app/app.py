
import os
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
APP_ENV = os.getenv("APP_ENV", "development")
COMMIT_SHA = os.getenv("COMMIT_SHA", "local")

MESSAGE = "Welcome to DevOps Release Tracker!"

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>DevOps Release Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f4f7fb;
            color: #1e293b;
            margin: 0;
            padding: 40px 16px;
        }
        .card {
            max-width: 600px;
            margin: 60px auto;
            padding: 32px;
            background: white;
            border-radius: 14px;
            box-shadow: 0 6px 24px rgba(0,0,0,0.08);
        }
        h1 { color: #2563eb; }
        .version {
            font-size: 28px;
            font-weight: bold;
            color: #2563eb;
        }
        .status { color: #15803d; }
        .meta { color: #64748b; }
    </style>
</head>
<body>
    <div class="card">
        <h1>DevOps Release Tracker</h1>
        <p>Production Demo Application</p>
        <p class="version">Version {{ version }}</p>
        <p class="status">Status: Healthy</p>
        <p>{{ message }}</p>
        <hr>
        <p class="meta">Environment: {{ environment }}</p>
        <p class="meta">Commit: {{ commit }}</p>
        <p class="meta">REST API: /api/info | /api/message</p>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    return render_template_string(
        HTML,
        version=APP_VERSION,
        environment=APP_ENV,
        commit=COMMIT_SHA,
        message=MESSAGE
    ), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/info", methods=["GET"])
def info():
    return jsonify({
        "application": "devops-release-tracker",
        "version": APP_VERSION,
        "environment": APP_ENV,
        "commit": COMMIT_SHA
    }), 200


@app.route("/api/message", methods=["GET"])
def message():
    return jsonify({
        "version": APP_VERSION,
        "message": MESSAGE
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
