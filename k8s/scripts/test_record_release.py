
import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


SCRIPT_PATH = Path(__file__).with_name("record_release.py")

TEST_ENV = {
    "PRODUCTION_NS": "devops-project",
    "DEPLOY_IMAGE": "ghcr.io/namle1602/devops-flask-app:33",
    "IMAGE_TAG": "33",
    "PRODUCTION_RELEASE_ID": "cd-test-33-production",
    "BUILD_NUMBER": "25",
    "PRODUCTION_INFO_URL": "https://example.test/api/info",
}

TEST_SHA = "a" * 40


def load_script():
    with patch.dict(os.environ, TEST_ENV):
        spec = importlib.util.spec_from_file_location(
            "record_release_test_target",
            SCRIPT_PATH
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class TestRecordRelease(unittest.TestCase):

    def setUp(self):
        self.script = load_script()

    def test_record_new_release(self):
        history = {
            "schema_version": 1,
            "releases": [],
        }

        configmap = {
            "metadata": {"resourceVersion": "10"},
            "data": {
                "releases.json": json.dumps(history)
            },
        }

        with patch.object(
            self.script,
            "kubectl",
            return_value=json.dumps(configmap)
        ), patch.object(
            self.script.subprocess,
            "run",
            return_value=Mock(returncode=0, stderr="")
        ) as run_mock:

            self.script.record_release(TEST_SHA)

            self.assertEqual(run_mock.call_count, 1)

            command = run_mock.call_args.args[0]
            self.assertEqual(command[:3], [
                "kubectl", "replace", "-f"
            ])

    def test_duplicate_release_is_not_written(self):
        history = {
            "schema_version": 1,
            "releases": [
                {
                    "version": "33",
                    "release_id": "cd-test-33-production",
                    "commit": TEST_SHA,
                }
            ],
        }

        configmap = {
            "metadata": {"resourceVersion": "10"},
            "data": {
                "releases.json": json.dumps(history)
            },
        }

        with patch.object(
            self.script,
            "kubectl",
            return_value=json.dumps(configmap)
        ), patch.object(
            self.script.subprocess,
            "run"
        ) as run_mock:

            self.script.record_release(TEST_SHA)

            run_mock.assert_not_called()

    def test_production_image_mismatch(self):
        deployment = {
            "metadata": {"generation": 1},
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "devops.example.com/release-id":
                                "cd-test-33-production"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "flask-app",
                                "image": "wrong-image:latest",
                            }
                        ]
                    },
                }
            },
            "status": {
                "readyReplicas": 2,
                "updatedReplicas": 2,
                "availableReplicas": 2,
                "observedGeneration": 1,
            },
        }

        with patch.object(
            self.script,
            "kubectl",
            return_value=json.dumps(deployment)
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Production image mismatch"
            ):
                self.script.validate_production()

    def test_configmap_update_failure(self):
        history = {
            "schema_version": 1,
            "releases": [],
        }

        configmap = {
            "metadata": {"resourceVersion": "10"},
            "data": {
                "releases.json": json.dumps(history)
            },
        }

        with patch.object(
            self.script,
            "kubectl",
            return_value=json.dumps(configmap)
        ), patch.object(
            self.script.subprocess,
            "run",
            return_value=Mock(
                returncode=1,
                stderr="Forbidden: update denied"
            )
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "Forbidden"
            ):
                self.script.record_release(TEST_SHA)

    def test_recorded_json_content(self):
        history = {
            "schema_version": 1,
            "releases": [],
        }

        configmap = {
            "metadata": {"resourceVersion": "10"},
            "data": {
                "releases.json": json.dumps(history)
            },
        }

        captured = {}

        def fake_run(command, **kwargs):
            path = Path(command[3])
            captured["configmap"] = json.loads(
                path.read_text(encoding="utf-8")
            )
            return Mock(returncode=0, stderr="")

        with patch.object(
            self.script,
            "kubectl",
            return_value=json.dumps(configmap)
        ), patch.object(
            self.script.subprocess,
            "run",
            side_effect=fake_run
        ):
            self.script.record_release(TEST_SHA)

        updated = captured["configmap"]

        self.assertEqual(
            updated["metadata"]["resourceVersion"], "10"
        )

        saved_history = json.loads(
            updated["data"]["releases.json"]
        )

        self.assertEqual(saved_history["schema_version"], 1)

        release = saved_history["releases"][0]

        self.assertEqual(release["version"], "33")
        self.assertEqual(release["commit"], TEST_SHA)
        self.assertEqual(
            release["image"],
            "ghcr.io/namle1602/devops-flask-app:33"
        )
        self.assertEqual(
            release["release_id"],
            "cd-test-33-production"
        )
        self.assertEqual(release["cd_build"], 25)
        self.assertEqual(release["status"], "success")
        self.assertIsNotNone(release["deployed_at"])


    def test_configmap_conflict_retries(self):
        history = {
            "schema_version": 1,
            "releases": [],
        }

        versions = iter(["10", "11"])

        def fake_kubectl(*args):
            configmap = {
                "metadata": {
                    "resourceVersion": next(versions)
                },
                "data": {
                    "releases.json": json.dumps(history)
                },
            }
            return json.dumps(configmap)

        captured_versions = []

        def fake_run(command, **kwargs):
            path = Path(command[3])
            data = json.loads(
                path.read_text(encoding="utf-8")
            )

            captured_versions.append(
                data["metadata"]["resourceVersion"]
            )

            if len(captured_versions) == 1:
                return Mock(
                    returncode=1,
                    stderr="Conflict: object has been modified"
                )

            return Mock(returncode=0, stderr="")

        with patch.object(
            self.script,
            "kubectl",
            side_effect=fake_kubectl
        ), patch.object(
            self.script.subprocess,
            "run",
            side_effect=fake_run
        ), patch.object(
            self.script.time,
            "sleep"
        ):
            self.script.record_release(TEST_SHA)

        self.assertEqual(
            captured_versions,
            ["10", "11"]
        )

if __name__ == "__main__":
    unittest.main()
