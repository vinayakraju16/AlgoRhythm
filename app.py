from flask import (
    Flask, request, jsonify, render_template, session, redirect, url_for, abort
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
import functools
import json
import joblib
import pandas as pd
import os
import datetime
import secrets

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Database configuration with multiple binds
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'  # default (can be unused)
app.config['SQLALCHEMY_BINDS'] = {
    'readmission': 'sqlite:///readmission.db',
    'diabetes': 'sqlite:///diabetes.db'
}

db = SQLAlchemy(app)

# Load models
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
readmission_model = joblib.load(os.path.join(BASE_DIR, "model", "heart_model.pkl"))
readmission_preprocessor = joblib.load(os.path.join(BASE_DIR, "model", "preprocessing.pkl"))
diabetes_model = joblib.load(os.path.join(BASE_DIR, "model", "diabetes_model.pkl"))

# Credentials for the two staff roles, overridable via environment variables.
DOCTOR_USERNAME = os.environ.get('DOCTOR_USERNAME', 'doctor')
DOCTOR_PASSWORD = os.environ.get('DOCTOR_PASSWORD', 'admin123')
NURSE_USERNAME = os.environ.get('NURSE_USERNAME', 'nurse')
NURSE_PASSWORD = os.environ.get('NURSE_PASSWORD', 'nurse123')


def to_int(value, default=0):
    """Coerce a value to int, falling back to `default`."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def coerce_like(current, value):
    """Coerce `value` to the type of `current`; keep the raw value otherwise."""
    if current is None or isinstance(current, str):
        return value
    try:
        return type(current)(value)
    except (TypeError, ValueError):
        return value


def generate_op_number(model):
    """Return an OP number that is not yet used by `model`.

    Uses a 6-digit random suffix (a much wider space than the previous
    3-digit one) and re-rolls on the rare collision.
    """
    date_part = datetime.datetime.now().strftime('%Y%m%d')
    for _ in range(20):
        op_number = f"OP{date_part}{secrets.randbelow(1_000_000):06d}"
        if model.query.filter_by(op_number=op_number).first() is None:
            return op_number
    # Last resort: millisecond-derived suffix, still unique in practice.
    return f"OP{date_part}{int(datetime.datetime.now().timestamp() * 1000) % 10**9:09d}"


def _authenticate(username, password):
    """Return the role for a valid credential pair, else None."""
    if username == DOCTOR_USERNAME and secrets.compare_digest(password, DOCTOR_PASSWORD):
        return 'doctor'
    if username == NURSE_USERNAME and secrets.compare_digest(password, NURSE_PASSWORD):
        return 'nurse'
    return None


def login_required(*roles):
    """Require a logged-in session, optionally restricted to specific roles."""
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get('user'):
                return redirect(url_for('login', next=request.path))
            if roles and session.get('role') not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


# Readmission Model
class ReadmissionData(db.Model):
    __bind_key__ = 'readmission'
    __tablename__ = 'readmission_data'

    id = db.Column(db.Integer, primary_key=True)
    op_number = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    age = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    location = db.Column(db.String(100))
    problem = db.Column(db.Text)
    available_doctors = db.Column(db.String(100))
    time_in_hospital = db.Column(db.Integer)
    n_procedures = db.Column(db.Integer)
    n_lab_procedures = db.Column(db.Integer)
    n_medications = db.Column(db.Integer)
    n_outpatient = db.Column(db.Integer)
    n_inpatient = db.Column(db.Integer)
    n_emergency = db.Column(db.Integer)
    medical_specialty = db.Column(db.String(100))
    diag_1 = db.Column(db.String(100))
    diag_2 = db.Column(db.String(100))
    diag_3 = db.Column(db.String(100))
    glucose_test = db.Column(db.String(50))
    A1Ctest = db.Column(db.String(50))
    change = db.Column(db.String(10))
    diabetes_med = db.Column(db.String(10))
    risk_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Diabetes Model
class DiabetesData(db.Model):
    __bind_key__ = 'diabetes'
    __tablename__ = 'diabetes_data'

    id = db.Column(db.Integer, primary_key=True)
    op_number = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(100))
    age = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    location = db.Column(db.String(100))
    problem = db.Column(db.Text)
    available_doctors = db.Column(db.String(100))
    number_inpatient = db.Column(db.Integer)
    number_emergency = db.Column(db.Integer)
    discharge_disposition_id = db.Column(db.String(50))
    number_diagnoses = db.Column(db.Integer)
    time_in_hospital = db.Column(db.Integer)
    num_medications = db.Column(db.Integer)
    diabetesMed = db.Column(db.String(10))
    metformin = db.Column(db.String(20))
    num_lab_procedures = db.Column(db.Integer)
    change = db.Column(db.String(10))
    risk_score = db.Column(db.Float)
    # Full 44-feature vector used for the stored risk score, so edits can be
    # scored against the patient's real features instead of placeholders.
    model_features = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


def initialize_db():
    """Create tables and backfill columns missing from older SQLite files."""
    with app.app_context():
        db.create_all()
        engine = db.engines.get('diabetes')
        if engine is None:
            return
        inspector = inspect(engine)
        if 'diabetes_data' not in inspector.get_table_names():
            return
        columns = {col['name'] for col in inspector.get_columns('diabetes_data')}
        if 'model_features' not in columns:
            with engine.begin() as conn:
                conn.execute(text('ALTER TABLE diabetes_data ADD COLUMN model_features TEXT'))


initialize_db()

# Feature order expected by the diabetes model.
DIABETES_FEATURE_COLUMNS = [
    'race', 'gender', 'age', 'admission_type_id', 'discharge_disposition_id', 'admission_source_id',
    'time_in_hospital', 'num_lab_procedures', 'num_procedures', 'num_medications',
    'number_outpatient', 'number_emergency', 'number_inpatient',
    'diag_1', 'diag_2', 'diag_3', 'number_diagnoses',
    'max_glu_serum', 'A1Cresult',
    'metformin', 'repaglinide', 'nateglinide', 'chlorpropamide', 'glimepiride', 'acetohexamide',
    'glipizide', 'glyburide', 'tolbutamide', 'pioglitazone', 'rosiglitazone', 'acarbose', 'miglitol',
    'troglitazone', 'tolazamide', 'examide', 'citoglipton', 'insulin', 'glyburide-metformin',
    'glipizide-metformin', 'glimepiride-pioglitazone', 'metformin-rosiglitazone',
    'metformin-pioglitazone', 'change', 'diabetesMed'
]

# Patient columns that are also model features; refreshed on edit before rescoring.
PERSISTED_DIABETES_FEATURES = (
    'time_in_hospital', 'num_lab_procedures', 'num_medications', 'number_inpatient',
    'number_emergency', 'number_diagnoses', 'discharge_disposition_id', 'metformin',
    'change', 'diabetesMed'
)


def diabetes_features_from_form(data):
    """Build the full diabetes feature vector from submitted form data."""
    return {
        'race': data.get('race', 'Caucasian'),
        'gender': data.get('gender', 'Female'),
        'age': data.get('age', '[70-80]'),
        'admission_type_id': to_int(data.get('admission_type_id')),
        'discharge_disposition_id': data.get('discharge_disposition_id', 'Home'),
        'admission_source_id': to_int(data.get('admission_source_id')),
        'time_in_hospital': to_int(data.get('time_in_hospital')),
        'num_lab_procedures': to_int(data.get('num_lab_procedures')),
        'num_procedures': to_int(data.get('num_procedures')),
        'num_medications': to_int(data.get('num_medications')),
        'number_outpatient': to_int(data.get('number_outpatient')),
        'number_emergency': to_int(data.get('number_emergency')),
        'number_inpatient': to_int(data.get('number_inpatient')),
        'diag_1': data.get('diag_1', '250.83'),
        'diag_2': data.get('diag_2', '250.01'),
        'diag_3': data.get('diag_3', '250.8'),
        'number_diagnoses': to_int(data.get('number_diagnoses')),
        'max_glu_serum': data.get('max_glu_serum', 'None'),
        'A1Cresult': data.get('A1Cresult', 'None'),
        'metformin': data.get('metformin', 'No'),
        'repaglinide': data.get('repaglinide', 'No'),
        'nateglinide': data.get('nateglinide', 'No'),
        'chlorpropamide': data.get('chlorpropamide', 'No'),
        'glimepiride': data.get('glimepiride', 'No'),
        'acetohexamide': data.get('acetohexamide', 'No'),
        'glipizide': data.get('glipizide', 'No'),
        'glyburide': data.get('glyburide', 'No'),
        'tolbutamide': data.get('tolbutamide', 'No'),
        'pioglitazone': data.get('pioglitazone', 'No'),
        'rosiglitazone': data.get('rosiglitazone', 'No'),
        'acarbose': data.get('acarbose', 'No'),
        'miglitol': data.get('miglitol', 'No'),
        'troglitazone': data.get('troglitazone', 'No'),
        'tolazamide': data.get('tolazamide', 'No'),
        'examide': data.get('examide', 'No'),
        'citoglipton': data.get('citoglipton', 'No'),
        'insulin': data.get('insulin', 'No'),
        'glyburide-metformin': data.get('glyburide_metformin', 'No'),
        'glipizide-metformin': data.get('glipizide_metformin', 'No'),
        'glimepiride-pioglitazone': data.get('glimepiride_pioglitazone', 'No'),
        'metformin-rosiglitazone': data.get('metformin_rosiglitazone', 'No'),
        'metformin-pioglitazone': data.get('metformin_pioglitazone', 'No'),
        'change': data.get('change', 'no'),
        'diabetesMed': data.get('diabetesMed', 'yes')
    }


def predict_diabetes_risk(features):
    """Score a full diabetes feature vector."""
    input_df = pd.DataFrame([features])[DIABETES_FEATURE_COLUMNS]
    for col in input_df.select_dtypes(include='object').columns:
        input_df[col] = input_df[col].astype('category')
    return float(diabetes_model.predict_proba(input_df)[0][1])


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip().lower()
        password = request.form.get('password') or ''
        role = _authenticate(username, password)
        if role is None:
            return render_template('login.html', error='Invalid username or password.'), 401

        session.clear()
        session['user'] = username
        session['role'] = role

        next_url = request.args.get('next') or request.form.get('next') or ''
        # Only allow same-site relative redirects.
        if not next_url.startswith('/') or next_url.startswith('//'):
            next_url = url_for('doctor_portal') if role == 'doctor' else url_for('nurse_portal')
        return redirect(next_url)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/doctor')
@login_required('doctor')
def doctor_portal():
    return render_template('doctor.html')


@app.route('/nurse')
@login_required('nurse')
def nurse_portal():
    return render_template('nurse.html')


@app.route('/nurse/add_readmission_patient', methods=['POST'])
@login_required('nurse')
def add_readmission():
    try:
        data = request.form
        op_number = generate_op_number(ReadmissionData)

        features = {
            'age': data.get('age'),
            'time_in_hospital': int(data.get('time_in_hospital') or 0),
            'n_procedures': int(data.get('n_procedures') or 0),
            'n_lab_procedures': int(data.get('n_lab_procedures') or 0),
            'n_medications': int(data.get('n_medications') or 0),
            'n_outpatient': int(data.get('n_outpatient') or 0),
            'n_inpatient': int(data.get('n_inpatient') or 0),
            'n_emergency': int(data.get('n_emergency') or 0),
            'medical_specialty': data.get('medical_specialty'),
            'diag_1': data.get('diag_1'),
            'diag_2': data.get('diag_2'),
            'diag_3': data.get('diag_3'),
            'glucose_test': data.get('glucose_test'),
            'A1Ctest': data.get('A1Ctest'),
            'change': data.get('change'),
            'diabetes_med': data.get('diabetes_med')
        }

        input_df = pd.DataFrame([features])
        processed = readmission_preprocessor.transform(input_df)
        risk = readmission_model.predict_proba(processed)[0][1]

        record = ReadmissionData(
            op_number=op_number,
            name=data.get('name'),
            height=float(data.get('height') or 0),
            weight=float(data.get('weight') or 0),
            location=data.get('location'),
            problem=data.get('problem'),
            available_doctors=data.get('available_doctors'),
            risk_score=risk,
            **features
        )

        db.session.add(record)
        db.session.commit()

        return jsonify({'status': 'success', 'op_number': op_number})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/nurse/add_diabetes_patient', methods=['POST'])
@login_required('nurse')
def add_diabetes():
    try:
        data = request.form
        op_number = generate_op_number(DiabetesData)

        features = diabetes_features_from_form(data)
        risk = predict_diabetes_risk(features)

        record = DiabetesData(
            op_number=op_number,
            name=data.get('name'),
            age=data.get('age'),
            height=float(data.get('height', 0)),
            weight=float(data.get('weight', 0)),
            location=data.get('location'),
            problem=data.get('problem'),
            available_doctors=data.get('available_doctors'),
            risk_score=risk,
            model_features=json.dumps(features),
            number_inpatient=to_int(data.get('number_inpatient')),
            number_emergency=to_int(data.get('number_emergency')),
            discharge_disposition_id=data.get('discharge_disposition_id'),
            number_diagnoses=to_int(data.get('number_diagnoses')),
            time_in_hospital=to_int(data.get('time_in_hospital')),
            num_medications=to_int(data.get('num_medications')),
            diabetesMed=data.get('diabetesMed'),
            metformin=data.get('metformin'),
            num_lab_procedures=to_int(data.get('num_lab_procedures')),
            change=data.get('change')
        )

        db.session.add(record)
        db.session.commit()
        return jsonify({'status': 'success', 'op_number': op_number})

    except Exception as e:
        print("Diabetes Prediction Error:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/doctor/all_patients')
@login_required('doctor')
def all_patients():
    model = request.args.get("model", "readmission")
    if model == "diabetes":
        patients = DiabetesData.query.order_by(DiabetesData.created_at.desc()).all()
    else:
        patients = ReadmissionData.query.order_by(ReadmissionData.created_at.desc()).all()

    return render_template("all_patients.html", patients=patients, selected_model=model)


@app.route('/nurse/all_patients')
@login_required('nurse')
def nurse_all_patients():
    model = request.args.get("model", "readmission")
    if model == "diabetes":
        patients = DiabetesData.query.order_by(DiabetesData.created_at.desc()).all()
    else:
        patients = ReadmissionData.query.order_by(ReadmissionData.created_at.desc()).all()

    return render_template("nurse_all_patients.html", patients=patients, selected_model=model)


# Doctor route: Get patient details
@app.route('/doctor/get_patient')
@login_required('doctor')
def get_patient():
    model = request.args.get('model')
    op_number = request.args.get('op_number')

    if model == 'readmission':
        patient = ReadmissionData.query.filter_by(op_number=op_number).first()
    elif model == 'diabetes':
        patient = DiabetesData.query.filter_by(op_number=op_number).first()
    else:
        return jsonify({'status': 'error', 'message': 'Invalid model type'}), 400

    if not patient:
        return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

    return jsonify({'status': 'success', 'patient': {col.name: getattr(patient, col.name) for col in patient.__table__.columns}})


@app.route('/doctor/edit/<op_number>')
@login_required('doctor')
def doctor_edit_patient(op_number):
    model = request.args.get('model', 'readmission')
    if model == 'diabetes':
        patient = DiabetesData.query.filter_by(op_number=op_number).first()
    else:
        patient = ReadmissionData.query.filter_by(op_number=op_number).first()

    return render_template(
        "doctor_edit_patient.html", patient=patient, selected_model=model
    )


# Doctor route: Update patient
@app.route('/doctor/update_patient', methods=['POST'])
@login_required('doctor')
def update_patient():
    model = request.args.get('model')
    data = request.form

    try:
        if model == 'readmission':
            patient = ReadmissionData.query.filter_by(op_number=data.get('op_number')).first()
        elif model == 'diabetes':
            patient = DiabetesData.query.filter_by(op_number=data.get('op_number')).first()
        else:
            return jsonify({'status': 'error', 'message': 'Invalid model'}), 400

        if not patient:
            return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

        # Update editable fields
        for key, value in data.items():
            if key in ['id', 'created_at', 'risk_score', 'op_number']:
                continue
            if hasattr(patient, key):
                setattr(patient, key, coerce_like(getattr(patient, key), value))

        if model == 'diabetes':
            # Restore the feature vector captured when the record was created and
            # refresh it with the patient's current clinical values before scoring.
            features = None
            if patient.model_features:
                try:
                    features = json.loads(patient.model_features)
                except (TypeError, ValueError):
                    features = None

            if features is not None:
                for name in PERSISTED_DIABETES_FEATURES:
                    value = getattr(patient, name, None)
                    if value is not None:
                        features[name] = value
                patient.risk_score = predict_diabetes_risk(features)
            # Records created before feature capture have no real vector stored;
            # leaving their score untouched is preferable to rescoring against
            # placeholder race/gender/diagnosis values.

        elif model == 'readmission':
            features = {
                'age': patient.age,
                'time_in_hospital': patient.time_in_hospital,
                'n_procedures': patient.n_procedures,
                'n_lab_procedures': patient.n_lab_procedures,
                'n_medications': patient.n_medications,
                'n_outpatient': patient.n_outpatient,
                'n_inpatient': patient.n_inpatient,
                'n_emergency': patient.n_emergency,
                'medical_specialty': patient.medical_specialty,
                'diag_1': patient.diag_1,
                'diag_2': patient.diag_2,
                'diag_3': patient.diag_3,
                'glucose_test': patient.glucose_test,
                'A1Ctest': patient.A1Ctest,
                'change': patient.change,
                'diabetes_med': patient.diabetes_med,
            }
            input_df = pd.DataFrame([features])
            processed = readmission_preprocessor.transform(input_df)
            patient.risk_score = readmission_model.predict_proba(processed)[0][1]

        db.session.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        print(f"Update Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/doctor/update', methods=['POST'])
@login_required('doctor')
def doctor_update_patient_form():
    """HTML form target used by doctor_edit_patient.html."""
    model = request.args.get('model', 'readmission')
    data = request.form
    if model == 'diabetes':
        patient = DiabetesData.query.filter_by(op_number=data.get('op_number')).first()
    else:
        patient = ReadmissionData.query.filter_by(op_number=data.get('op_number')).first()

    if not patient:
        return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

    try:
        for key, value in data.items():
            if key in ['id', 'created_at', 'risk_score', 'op_number']:
                continue
            if hasattr(patient, key):
                setattr(patient, key, coerce_like(getattr(patient, key), value))
        db.session.commit()
    except Exception as e:
        print(f"Update Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return redirect(url_for('doctor_edit_patient', op_number=patient.op_number, model=model))


@app.route('/nurse/edit/<op_number>')
@login_required('nurse')
def nurse_edit_patient(op_number):
    model = request.args.get('model', 'readmission')
    if model == 'diabetes':
        patient = DiabetesData.query.filter_by(op_number=op_number).first()
    else:
        patient = ReadmissionData.query.filter_by(op_number=op_number).first()

    return render_template(
        "nurse_edit_patient.html", patient=patient, selected_model=model
    )


@app.route('/nurse/update', methods=['POST'])
@login_required('nurse')
def nurse_update_patient():
    """HTML form target used by nurse_edit_patient.html."""
    data = request.form
    op_number = data.get('op_number')
    patient = ReadmissionData.query.filter_by(op_number=op_number).first() or \
        DiabetesData.query.filter_by(op_number=op_number).first()

    if not patient:
        return render_template('nurse_edit_patient.html', patient=None), 404

    try:
        for key, value in data.items():
            if key in ['id', 'created_at', 'risk_score', 'op_number']:
                continue
            if hasattr(patient, key):
                setattr(patient, key, coerce_like(getattr(patient, key), value))
        db.session.commit()
    except Exception as e:
        print(f"Update Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return redirect(url_for('nurse_all_patients'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
