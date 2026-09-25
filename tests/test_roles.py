"""Role separation: neither portal may reach the other's routes."""


def test_nurse_cannot_reach_doctor_routes(nurse_client):
    doctor_only = (
        "/doctor",
        "/doctor/all_patients",
        "/doctor/dashboard",
        "/doctor/audit_log",
        "/doctor/export/readmission.csv",
    )
    for path in doctor_only:
        resp = nurse_client.get(path, follow_redirects=False)
        assert resp.status_code == 403, f"{path} -> {resp.status_code}"


def test_doctor_cannot_reach_nurse_routes(doctor_client):
    nurse_only = ("/nurse", "/nurse/all_patients")
    for path in nurse_only:
        resp = doctor_client.get(path, follow_redirects=False)
        assert resp.status_code == 403, f"{path} -> {resp.status_code}"


def test_nurse_cannot_post_to_a_doctor_endpoint(nurse_client):
    resp = nurse_client.post("/doctor/update?model=readmission", data={})
    assert resp.status_code == 403


def test_each_role_can_reach_its_own_portal(doctor_client, nurse_client):
    assert doctor_client.get("/doctor").status_code == 200
    assert nurse_client.get("/nurse").status_code == 200
