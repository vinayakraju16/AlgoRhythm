"""Shared pytest fixtures for the AlgoRhythm test suite.

Environment variables are set *before* `app` is imported, because app.py
configures its SQLAlchemy binds and calls `initialize_db()` at import time.
Pointing the binds at a temp directory keeps tests off the real databases.
"""
import os
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSRF_RE = re.compile(r'name="_csrf_token"\s+value="([^"]+)"')

DOCTOR = {"username": "doctor", "password": "admin123"}
NURSE = {"username": "nurse", "password": "nurse123"}


@pytest.fixture(scope="session")
def app_module(tmp_path_factory):
    """Import the Flask app against throwaway SQLite files."""
    tmp = tmp_path_factory.mktemp("algodb")
    os.environ.update(
        DATABASE_URI=f"sqlite:///{tmp / 'default.db'}",
        READMISSION_DATABASE_URI=f"sqlite:///{tmp / 'readmission.db'}",
        DIABETES_DATABASE_URI=f"sqlite:///{tmp / 'diabetes.db'}",
        SECRET_KEY="test-secret-key",
        DOCTOR_USERNAME="doctor",
        DOCTOR_PASSWORD="admin123",
        NURSE_USERNAME="nurse",
        NURSE_PASSWORD="nurse123",
    )
    import app as app_module  # noqa: E402  (import must follow env setup)

    app_module.app.config.update(TESTING=True)
    return app_module


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


def csrf_from(response) -> str:
    """Pull the CSRF token out of a rendered page."""
    match = CSRF_RE.search(response.get_data(as_text=True))
    assert match, "no CSRF token found in response"
    return match.group(1)


def login(client, creds, endpoint="/login"):
    """Log in, carrying a valid CSRF token through the POST."""
    token = csrf_from(client.get(endpoint))
    return client.post(
        endpoint,
        data={**creds, "_csrf_token": token},
        follow_redirects=False,
    )


@pytest.fixture()
def doctor_client(app_module):
    c = app_module.app.test_client()
    login(c, DOCTOR)
    return c


@pytest.fixture()
def nurse_client(app_module):
    c = app_module.app.test_client()
    login(c, NURSE)
    return c
