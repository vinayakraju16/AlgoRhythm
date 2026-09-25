"""Authentication and CSRF behaviour."""
import re

from conftest import DOCTOR, NURSE, csrf_from, login


def test_login_page_renders(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "_csrf_token" in resp.get_data(as_text=True)


def test_login_success_redirects(client):
    resp = login(client, DOCTOR)
    assert resp.status_code == 302
    assert "/doctor" in resp.headers["Location"]


def test_login_wrong_password_rejected(client):
    resp = login(client, {"username": "doctor", "password": "nope"})
    assert resp.status_code == 401
    assert "Invalid" in resp.get_data(as_text=True)


def test_login_unknown_user_rejected(client):
    resp = login(client, {"username": "ghost", "password": "x"})
    assert resp.status_code == 401


def test_login_requires_a_csrf_token(client):
    """A POST without the session token must be refused, never authenticated."""
    client.get("/login")  # establish a session
    resp = client.post("/login", data=DOCTOR)
    assert resp.status_code == 400


def test_login_rejects_a_wrong_csrf_token(client):
    client.get("/login")
    resp = client.post("/login", data={**DOCTOR, "_csrf_token": "not-the-token"})
    assert resp.status_code == 400


def test_protected_route_redirects_when_anonymous(client):
    for path in ("/doctor", "/nurse", "/doctor/all_patients", "/doctor/dashboard"):
        resp = client.get(path, follow_redirects=False)
        assert resp.status_code == 302, path
        assert "/login" in resp.headers["Location"], path


def test_logout_clears_the_session(doctor_client):
    assert doctor_client.get("/doctor").status_code == 200
    doctor_client.get("/logout")
    resp = doctor_client.get("/doctor", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_healthz_is_public_and_reports_checks(client):
    resp = client.get("/healthz")
    assert resp.status_code in (200, 503)
    body = resp.get_json()
    assert "status" in body and "checks" in body
    assert "models_loaded" in body["checks"]
    assert "database" in body["checks"]


def test_csrf_token_is_stable_within_a_session(doctor_client):
    """The same session must not mint a new token on every render."""
    body = doctor_client.get("/doctor").get_data(as_text=True)
    tokens = set(re.findall(r'name="_csrf_token"\s+value="([^"]+)"', body))
    assert len(tokens) == 1
