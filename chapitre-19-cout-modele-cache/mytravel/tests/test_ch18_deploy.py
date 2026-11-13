"""Chapter 18: the files Cloud Run and the CI need."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_dockerfile_listens_on_cloud_run_port():
    dockerfile = (ROOT / "Dockerfile").read_text()
    assert "uvicorn server:app" in dockerfile
    assert "${PORT" in dockerfile


def test_ci_runs_the_tests():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
    assert "pytest" in ci


def test_secrets_stay_out_of_the_image():
    ignored = (ROOT / ".dockerignore").read_text().split()
    assert ".env" in ignored and "*.db" in ignored
