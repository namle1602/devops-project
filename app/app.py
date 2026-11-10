
import os
import json
from pathlib import Path
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
    
.release-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
}

.release-table th,
.release-table td {
    padding: 14px 12px;
    border-bottom: 1px solid var(--border);
    text-align: left;
}

.release-table th {
    color: var(--muted);
    font-size: 12px;
    font-weight: 600;
}

.release-table tbody tr:hover {
    background: var(--bg);
}

#release-history {
    overflow-x: auto;
}

        :root {
            --bg: #f4f7fc;
            --surface: #ffffff;
            --text: #14213d;
            --muted: #64748b;
            --blue: #2563eb;
            --border: #e2e8f0;
            --green: #15803d;
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            background: var(--bg);
            color: var(--text);
            font-family: Arial, Helvetica, sans-serif;
            line-height: 1.5;
            background-color: #E3F2FD;
        }

        .container {
            width: min(1100px, calc(100% - 36px));
            margin: 0 auto;
        }

        header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
        }

        .header-inner {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
            padding: 22px 0;
        }

        .brand {
            font-size: 23px;
            font-weight: 750;
            color: var(--blue);
        }

        .subtitle {
            color: var(--muted);
            font-size: 13px;
        }

        .status {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 24px;
            color: var(--green);
            background: #dcfce7;
            font-weight: bold;
            font-size: 13px;
        }

        main { padding: 36px 0 50px; }

        .intro { margin-bottom: 24px; }

        h1 {
            margin: 0 0 8px;
            font-size: 30px;
        }

        h2 {
            margin: 0 0 18px;
            font-size: 20px;
        }

        p { margin: 0; }

        .muted { color: var(--muted); }

        .grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin-bottom: 22px;
        }

        .card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 24px;
            box-shadow: 0 4px 16px rgba(15,23,42,0.035);
        }

        .label {
            color: var(--muted);
            font-size: 13px;
            margin-bottom: 12px;
        }

        .value {
            font-size: 26px;
            font-weight: bold;
            overflow-wrap: anywhere;
        }

        .primary { color: var(--blue); }
        .healthy { color: var(--green); }

        .details { margin-bottom: 22px; }

        .detail-row {
            display: flex;
            justify-content: space-between;
            gap: 20px;
            padding: 13px 0;
            border-bottom: 1px solid var(--border);
        }

        .detail-row:last-child { border-bottom: none; }

        code {
            font-size: 13px;
            overflow-wrap: anywhere;
            word-break: break-word;
        }

        .history-empty {
            padding: 26px;
            text-align: center;
            background: var(--bg);
            border: 1px dashed #cbd5e1;
            border-radius: 10px;
            color: var(--muted);
        }

        .api-links {
            margin-top: 20px;
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
        }

        a {
            color: var(--blue);
            text-decoration: none;
            font-weight: 600;
        }

        a:hover { text-decoration: underline; }

        footer {
            text-align: center;
            color: var(--muted);
            font-size: 12px;
            padding: 0 0 30px;
        }

        @media (max-width: 720px) {
            .grid { grid-template-columns: 1fr; }
            .header-inner { align-items: flex-start; }
            .brand { font-size: 19px; }
            h1 { font-size: 25px; }
            .detail-row {
                flex-direction: column;
                gap: 4px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container header-inner">
            <div>
                <div class="brand">DevOps Release Tracker</div>
                <div class="subtitle">Application Release Dashboard</div>
            </div>
            <span class="status">Application Healthy</span>
        </div>
    </header>

    <main class="container">
        <section class="intro">
            <h1>Release Overview</h1>
            <p class="muted">{{ message }}</p>
        </section>

        <section class="grid" aria-label="Release summary">
            <div class="card">
                <div class="label">Current Version</div>
                <div class="value primary">v{{ version }}</div>
            </div>

            <div class="card">
                <div class="label">Environment</div>
                <div class="value">{{ environment }}</div>
            </div>

            <div class="card">
                <div class="label">Application Status</div>
                <div class="value healthy">Healthy</div>
            </div>
        </section>

        <section class="card details">
            <h2>Current Release Details</h2>

            <div class="detail-row">
                <span class="muted">Application</span>
                <strong>devops-release-tracker</strong>
            </div>

            <div class="detail-row">
                <span class="muted">Version</span>
                <strong>{{ version }}</strong>
            </div>

            <div class="detail-row">
                <span class="muted">Environment</span>
                <strong>{{ environment }}</strong>
            </div>

            <div class="detail-row">
                <span class="muted">Git Commit SHA</span>
                <code>{{ commit }}</code>
            </div>
        </section>

        <section class="card">
            <h2>Release History</h2>
            <div id="release-history" aria-live="polite">
                <div class="history-empty">
                    Loading release history...
                </div>
            </div>

            <nav class="api-links" aria-label="Application APIs">
                <a href="/api/info">Release Info API</a>
                <a href="/api/message">Message API</a>
                <a href="/health">Health API</a>
            </nav>
        </section>
    </main>

    <footer>DevOps Release Tracker · Application Dashboard</footer>

<script>
    async function loadReleaseHistory() {
        const container = document.getElementById("release-history");

        try {
            const response = await fetch("/api/releases");

            if (!response.ok) {
                throw new Error("Release history API unavailable");
            }

            const data = await response.json();

            if (!Array.isArray(data.releases)) {
                throw new Error("Invalid release history response");
            }

            if (data.releases.length === 0) {
                container.innerHTML =
                    '<div class="history-empty">' +
                    'No release history available yet.' +
                    '</div>';
                return;
            }

            const table = document.createElement("table");
            table.className = "release-table";

            const header = document.createElement("thead");
            const headerRow = document.createElement("tr");

            ["Version", "Git Commit", "Deployed At", "Status"]
                .forEach(label => {
                    const th = document.createElement("th");
                    th.textContent = label;
                    headerRow.appendChild(th);
                });

            header.appendChild(headerRow);
            table.appendChild(header);

            const body = document.createElement("tbody");

            data.releases.forEach(release => {
                const row = document.createElement("tr");

                const values = [
                    "v" + (release.version ?? "Unknown"),
                    release.commit
                        ? String(release.commit).slice(0, 10)
                        : "Unknown",
                    release.deployed_at ?? "Not recorded",
                    release.status ?? "Unknown"
                ];

                values.forEach(value => {
                    const td = document.createElement("td");
                    td.textContent = value;
                    row.appendChild(td);
                });

                body.appendChild(row);
            });

            table.appendChild(body);
            container.replaceChildren(table);

        } catch (error) {
            console.error("Release history error:", error);

            container.innerHTML =
                '<div class="history-empty">' +
                'Unable to load release history.' +
                '</div>';
        }
    }

    document.addEventListener("DOMContentLoaded", loadReleaseHistory);
</script>

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


@app.route("/api/releases", methods=["GET"])
def releases():
    history_file = Path(
        os.getenv(
            "RELEASE_HISTORY_FILE",
            "/app/release-history/releases.json"
        )
    )

    if not history_file.is_file():
        return jsonify({"releases": []}), 200

    try:
        with history_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if (
            not isinstance(data, dict)
            or not isinstance(data.get("releases"), list)
        ):
            raise ValueError("Invalid release history format")

        return jsonify({
            "releases": data["releases"]
        }), 200

    except (OSError, ValueError, UnicodeError):
        app.logger.exception("Failed to load release history")
        return jsonify({
            "error": "Release history unavailable"
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
