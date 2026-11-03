
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen


NAMESPACE = os.environ["PRODUCTION_NS"]
IMAGE = os.environ["DEPLOY_IMAGE"]
VERSION = os.environ["IMAGE_TAG"]
RELEASE_ID = os.environ["PRODUCTION_RELEASE_ID"]
CD_BUILD = int(os.environ["BUILD_NUMBER"])
CONFIGMAP = "flask-release-history"


def kubectl(*args):
    return subprocess.check_output(
        ["kubectl", *args],
        text=True
    ).strip()


def validate_production():
    deployment = json.loads(
        kubectl(
            "get", "deployment", "flask-deployment",
            "-n", NAMESPACE, "-o", "json"
        )
    )

    template = deployment["spec"]["template"]

    container = next(
        c for c in template["spec"]["containers"]
        if c["name"] == "flask-app"
    )

    actual_release = (
        template.get("metadata", {})
        .get("annotations", {})
        .get("devops.example.com/release-id")
    )

    # Verify Production image and release ownership
    if container["image"] != IMAGE:
        raise RuntimeError("Production image mismatch")

    if actual_release != RELEASE_ID:
        raise RuntimeError("Production release ownership mismatch")

    status = deployment.get("status", {})

    if status.get("readyReplicas", 0) != 2:
        raise RuntimeError("Production is not 2/2 Ready")

    # Verify that the rollout has fully converged
    if (
        status.get("updatedReplicas") != 2
        or status.get("availableReplicas") != 2
        or status.get("observedGeneration", 0)
        != deployment["metadata"]["generation"]
    ):
        raise RuntimeError("Production rollout is not fully converged")

    # Verify actual Production pods
    pods = json.loads(
        kubectl(
            "get", "pods",
            "-n", NAMESPACE,
            "-l", "app=flask-app",
            "-o", "json"
        )
    )["items"]

    ready_pods = [
        p for p in pods
        if not p["metadata"].get("deletionTimestamp")
        and any(
            c["name"] == "flask-app"
            and c.get("ready") is True
            for c in p.get("status", {}).get("containerStatuses", [])
        )
        and any(
            c["name"] == "flask-app"
            and c["image"] == IMAGE
            for c in p["spec"]["containers"]
        )
    ]

    if len(ready_pods) != 2:
        raise RuntimeError(
            "Expected two ready Production pods"
        )

    # Read the Git SHA from the Production API
    info_url = os.environ["PRODUCTION_INFO_URL"]

    with urlopen(info_url, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(
                "Production info API returned non-200"
            )

        info = json.load(response)

    if info.get("application") != "devops-release-tracker":
        raise RuntimeError("Unexpected application")

    if str(info.get("version")) != VERSION:
        raise RuntimeError("Production API version mismatch")

    if info.get("environment") != "production":
        raise RuntimeError("Production environment mismatch")

    commit = info.get("commit", "")

    if (
        not isinstance(commit, str)
        or len(commit) != 40
        or any(c not in "0123456789abcdef" for c in commit)
    ):
        raise RuntimeError("Invalid production Git SHA")

    return commit


def record_release(commit):
    release = {
        "version": VERSION,
        "commit": commit,
        "image": IMAGE,
        "environment": "production",
        "status": "success",
        "deployed_at": datetime.now(timezone.utc).isoformat(),
        "cd_build": CD_BUILD,
        "release_id": RELEASE_ID,
    }

    for attempt in range(3):
        cm = json.loads(
            kubectl(
                "get", "configmap", CONFIGMAP,
                "-n", NAMESPACE, "-o", "json"
            )
        )

        history = json.loads(cm["data"]["releases.json"])

        if history.get("schema_version") != 1:
            raise RuntimeError(
                "Unsupported history schema"
            )

        releases = history.get("releases")

        if not isinstance(releases, list):
            raise RuntimeError("Invalid releases list")

        # Do not record the same release twice
        if any(
            r.get("release_id") == RELEASE_ID
            for r in releases
        ):
            print("RELEASE_ALREADY_RECORDED")
            return

        # Reject a version associated with a different SHA
        if any(
            str(r.get("version")) == VERSION
            and r.get("commit") != commit
            for r in releases
        ):
            raise RuntimeError(
                "Version already has a different Git SHA"
            )

        history["releases"] = [release] + releases

        updated = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
                "name": CONFIGMAP,
                "namespace": NAMESPACE,
                "resourceVersion": cm["metadata"]["resourceVersion"],
            },
            "data": {
                **cm["data"],
                "releases.json": json.dumps(
                    history,
                    indent=2
                ),
            },
        }

        # Update ConfigMap using its resourceVersion
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "configmap.json"

            path.write_text(
                json.dumps(updated),
                encoding="utf-8"
            )

            result = subprocess.run(
                ["kubectl", "replace", "-f", str(path)],
                capture_output=True,
                text=True
            )

        if result.returncode == 0:
            print(
                "RELEASE_HISTORY_RECORDED:",
                VERSION,
                commit
            )
            return

        # Retry only when Kubernetes reports a conflict
        if "Conflict" not in result.stderr:
            raise RuntimeError(result.stderr)

        time.sleep(1)

    raise RuntimeError(
        "ConfigMap update conflict after retries"
    )


if __name__ == "__main__":
    sha = validate_production()
    record_release(sha)
