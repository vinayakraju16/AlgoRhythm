"""Patient flows: creation, OP-number uniqueness, pagination, and search."""
import pytest

from conftest import csrf_from


def _token(client, path="/nurse"):
    return csrf_from(client.get(path))


def test_op_numbers_are_unique_across_repeated_creation(app_module, nurse_client):
    """OP numbers are unique-constrained; repeated creation must not collide.

    This exercises the retry loop in `generate_op_number` directly, which is
    where a naive `random.randint(100, 999)` suffix produced 500s.
    """
    model = app_module.ReadmissionData
    seen = set()
    for _ in range(60):
        op = app_module.generate_op_number(model)
        assert op not in seen, "generate_op_number returned a duplicate"
        seen.add(op)


def test_created_record_gets_an_op_number(app_module, nurse_client):
    """Insert directly (no model scoring) and confirm the row round-trips."""
    with app_module.app.app_context():
        op = app_module.generate_op_number(app_module.ReadmissionData)
        row = app_module.ReadmissionData(op_number=op, name="Test Patient", age="[60-70]")
        app_module.db.session.add(row)
        app_module.db.session.commit()

        fetched = app_module.ReadmissionData.query.filter_by(op_number=op).first()
        assert fetched is not None
        assert fetched.name == "Test Patient"


def test_unique_constraint_rejects_a_duplicate(app_module):
    """The column really is unique — a duplicate insert must raise."""
    from sqlalchemy.exc import IntegrityError

    with app_module.app.app_context():
        op = app_module.generate_op_number(app_module.ReadmissionData)
        app_module.db.session.add(app_module.ReadmissionData(op_number=op, name="First"))
        app_module.db.session.commit()

        app_module.db.session.add(app_module.ReadmissionData(op_number=op, name="Second"))
        with pytest.raises(IntegrityError):
            app_module.db.session.commit()
        app_module.db.session.rollback()


def test_pagination_caps_the_page_size(app_module, doctor_client):
    page = app_module.paginate_patients(app_module.ReadmissionData, 1)
    assert page.per_page == app_module.PATIENTS_PER_PAGE


def test_patient_list_renders(doctor_client):
    resp = doctor_client.get("/doctor/all_patients?model=readmission")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "readmission" in body


def test_patient_list_search_is_accepted(doctor_client):
    resp = doctor_client.get("/doctor/all_patients?model=readmission&q=zzz-no-match")
    assert resp.status_code == 200


def test_invalid_model_in_export_is_404(doctor_client):
    resp = doctor_client.get("/doctor/export/not-a-model.csv")
    assert resp.status_code == 404


def test_export_returns_csv(doctor_client):
    resp = doctor_client.get("/doctor/export/readmission.csv")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["Content-Type"]
    assert "attachment" in resp.headers["Content-Disposition"]


def test_dashboard_requires_doctor_role(nurse_client):
    assert nurse_client.get("/doctor/dashboard").status_code == 403


def test_dashboard_renders_for_doctor(doctor_client):
    assert doctor_client.get("/doctor/dashboard").status_code == 200


def test_audit_log_records_a_login(app_module, doctor_client):
    with app_module.app.app_context():
        entry = (
            app_module.AuditLog.query.filter_by(action="login")
            .order_by(app_module.AuditLog.id.desc())
            .first()
        )
        assert entry is not None
        assert entry.actor == "doctor"
        assert entry.role == "doctor"


def test_audit_log_page_renders(doctor_client):
    assert doctor_client.get("/doctor/audit_log").status_code == 200
