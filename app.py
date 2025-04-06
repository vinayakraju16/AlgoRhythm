from flask import Flask, request, jsonify, render_template
import tensorflow as tf
import numpy as np
import joblib
import pandas as pd
import os
from flask_sqlalchemy import SQLAlchemy
import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
db = SQLAlchemy(app)

# Load model and preprocessing tools
# model = joblib.load('model/xgboost_readmission_model.pkl')
# preprocessor = joblib.load('.model/xgboost_preprocessor.pkl')

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
model_path = os.path.join(BASE_DIR, "model", "xgboost_readmission_model.pkl")
preprocessor_path = os.path.join(BASE_DIR, "model", "xgboost_preprocessor.pkl")

# Load the model and preprocessor
model = joblib.load(model_path)
preprocessor = joblib.load(preprocessor_path)


# Database Model config
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    op_number = db.Column(db.String(20), unique=True)
    name = db.Column(db.Text)
    age = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    location = db.Column(db.String(100))
    problem = db.Column(db.Text)
    available_doctors = db.Column(db.Text)
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
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Run once to create the table
with app.app_context():
    db.create_all()

# for checking the column namesfrom flask import Flask, request, jsonify, render_template, redirect, url_for
import tensorflow as tf
import numpy as np
import joblib
import pandas as pd
import os
from flask_sqlalchemy import SQLAlchemy
import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///patients.db'
db = SQLAlchemy(app)

# Load model and preprocessing tools
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
model_path = os.path.join(BASE_DIR, "model", "xgboost_readmission_model.pkl")
preprocessor_path = os.path.join(BASE_DIR, "model", "xgboost_preprocessor.pkl")

model = joblib.load(model_path)
preprocessor = joblib.load(preprocessor_path)

# Database Model config
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    op_number = db.Column(db.String(20), unique=True)
    name = db.Column(db.Text)
    age = db.Column(db.String(20))
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    location = db.Column(db.String(100))
    problem = db.Column(db.Text)
    available_doctors = db.Column(db.Text)
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
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/nurse')
def nurse_portal():
    return render_template('nurse.html')

@app.route('/nurse/all_patients')
def nurse_all_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('nurse_all_patients.html', patients=patients)

@app.route('/nurse/edit/<op_number>')
def edit_patient(op_number):
    patient = Patient.query.filter_by(op_number=op_number).first()
    if not patient:
        return "Patient not found", 404
    return render_template('nurse_edit_patient.html', patient=patient)

@app.route('/nurse/update', methods=['POST'])
def update_patient_nurse():
    data = request.form
    op_number = data['op_number']
    patient = Patient.query.filter_by(op_number=op_number).first()

    if patient:
        patient.name = data['name']
        patient.age = data['age']
        patient.height = float(data['height'])
        patient.weight = float(data['weight'])
        patient.location = data['location']
        patient.problem = data['problem']
        patient.available_doctors = data['available_doctors']
        db.session.commit()
        return redirect(url_for('nurse_all_patients'))
    return "Patient not found", 404

@app.route('/nurse/add_patient', methods=['POST'])
def add_patient():
    try:
        data = request.form
        features = {
            'age': data['age'],
            'time_in_hospital': data['time_in_hospital'],
            'n_procedures': data['n_procedures'],
            'n_lab_procedures': data['n_lab_procedures'],
            'n_medications': data['n_medications'],
            'n_outpatient': data['n_outpatient'],
            'n_inpatient': data['n_inpatient'],
            'n_emergency': data['n_emergency'],
            'medical_specialty': data['medical_specialty'],
            'diag_1': data['diag_1'],
            'diag_2': data['diag_2'],
            'diag_3': data['diag_3'],
            'glucose_test': data['glucose_test'],
            'A1Ctest': data['A1Ctest'],
            'change': data['change'],
            'diabetes_med': data['diabetes_med']
        }
        input_df = pd.DataFrame([features])
        processed_input = preprocessor.transform(input_df)
        risk = model.predict_proba(processed_input)[0][1]

        op_number = f"OP{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"

        patient = Patient(
            op_number=op_number,
            name=data['name'],
            age=data['age'],
            height=float(data['height']),
            weight=float(data['weight']),
            location=data['location'],
            problem=data['problem'],
            available_doctors=data['available_doctors'],
            time_in_hospital=int(data['time_in_hospital']),
            n_procedures=int(data['n_procedures']),
            n_lab_procedures=int(data['n_lab_procedures']),
            n_medications=int(data['n_medications']),
            n_outpatient=int(data['n_outpatient']),
            n_inpatient=int(data['n_inpatient']),
            n_emergency=int(data['n_emergency']),
            medical_specialty=data['medical_specialty'],
            diag_1=data['diag_1'],
            diag_2=data['diag_2'],
            diag_3=data['diag_3'],
            glucose_test=data['glucose_test'],
            A1Ctest=data['A1Ctest'],
            change=data['change'],
            diabetes_med=data['diabetes_med'],
            risk_score=risk
        )

        db.session.add(patient)
        db.session.commit()

        return jsonify({'status': 'success', 'op_number': op_number})
    except Exception as e:
        print("Error adding patient:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/doctor')
def doctor_portal():
    return render_template('doctor.html')

@app.route('/doctor/patient/<op_number>')
def get_patient_by_op(op_number):
    patient = Patient.query.filter_by(op_number=op_number).first()
    if patient:
        return jsonify({
            'status': 'success',
            'patient': {
                'op_number': patient.op_number,
                'name': patient.name,
                'age': patient.age,
                'height': patient.height,
                'weight': patient.weight,
                'location': patient.location,
                'problem': patient.problem,
                'available_doctors': patient.available_doctors,
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
                'diagnosis': patient.diagnosis,
                'treatment': patient.treatment,
                'notes': patient.notes
            }
        })
    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

@app.route('/doctor/edit/<op_number>')
def doctor_edit_patient(op_number):
    patient = Patient.query.filter_by(op_number=op_number).first()
    if not patient:
        return "Patient not found", 404
    return render_template("doctor_edit_patient.html", patient=patient)

@app.route('/doctor/update', methods=['POST'])
def update_patient():
    data = request.form
    op_number = data['op_number']
    diagnosis = data['diagnosis']
    treatment = data['treatment']
    notes = data['notes']

    patient = Patient.query.filter_by(op_number=op_number).first()
    if patient:
        patient.diagnosis = diagnosis
        patient.treatment = treatment
        patient.notes = notes
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

@app.route('/patients')
def get_all_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    results = [
        {
            'op_number': p.op_number,
            'name': p.name,
            'age': p.age,
            'height': p.height,
            'weight': p.weight,
            'location': p.location,
            'problem': p.problem,
            'available_doctors': p.available_doctors,
            'time_in_hospital': p.time_in_hospital,
            'num_lab_procedures': p.num_lab_procedures,
            'risk_score': round(p.risk_score, 2) if p.risk_score is not None else None,
            'diagnosis': p.diagnosis,
            'treatment': p.treatment,
            'notes': p.notes,
            'created_at': p.created_at.strftime("%Y-%m-%d %H:%M")
        } for p in patients
    ]
    return jsonify(results)

@app.route('/doctor/all_patients')
def view_all_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('all_patients.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)

#with app.app_context():
#    columns = Patient.__table__.columns
#    for column in columns:
#        print(column.name)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/nurse')
def nurse_portal():
    return render_template('nurse.html')

@app.route('/nurse/add_patient', methods=['POST'])
def add_patient():
    try:
        data = request.form

        features = {
            'age': data['age'],
            'time_in_hospital': data['time_in_hospital'],
            'n_procedures': data['n_procedures'],
            'n_lab_procedures': data['n_lab_procedures'],
            'n_medications': data['n_medications'],
            'n_outpatient': data['n_outpatient'],
            'n_inpatient': data['n_inpatient'],
            'n_emergency': data['n_emergency'],
            'medical_specialty': data['medical_specialty'],
            'diag_1': data['diag_1'],
            'diag_2': data['diag_2'],
            'diag_3': data['diag_3'],
            'glucose_test': data['glucose_test'],
            'A1Ctest': data['A1Ctest'],
            'change': data['change'],
            'diabetes_med': data['diabetes_med']
        }

        # Preprocess input
        input_df = pd.DataFrame([features])  # <-- pass a dictionary inside a list
        processed_input = preprocessor.transform(input_df)
        risk = model.predict_proba(processed_input)[0][1]

        # Generate OP number
        op_number = f"OP{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(100, 999)}"

        patient = Patient(
            op_number=op_number,
            name=data['name'],
            age=data['age'],
            height=float(data['height']),
            weight=float(data['weight']),
            location=data['location'],
            problem=data['problem'],
            available_doctors=data['available_doctors'],
            time_in_hospital=int(data['time_in_hospital']),
            n_procedures=int(data['n_procedures']),
            n_lab_procedures=int(data['n_lab_procedures']),
            n_medications=int(data['n_medications']),
            n_outpatient=int(data['n_outpatient']),
            n_inpatient=int(data['n_inpatient']),
            n_emergency=int(data['n_emergency']),
            medical_specialty=data['medical_specialty'],
            diag_1=data['diag_1'],
            diag_2=data['diag_2'],
            diag_3=data['diag_3'],
            glucose_test=data['glucose_test'],
            A1Ctest=data['A1Ctest'],
            change=data['change'],
            diabetes_med=data['diabetes_med'],
            risk_score=risk
        )

        db.session.add(patient)
        db.session.commit()

        return jsonify({'status': 'success', 'op_number': op_number})
    except Exception as e:
        print("Error adding patient:", e)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/doctor')
def doctor_portal():
    return render_template('doctor.html')

@app.route('/doctor/patient/<op_number>')
def get_patient_by_op(op_number):
    patient = Patient.query.filter_by(op_number=op_number).first()
    if patient:
        patient_data = {
            'op_number': patient.op_number,
            'name': patient.name,
            'age': patient.age,
            'height': patient.height,
            'weight': patient.weight,
            'location': patient.location,
            'problem': patient.problem,
            'available_doctors': patient.available_doctors,
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
            'diagnosis': patient.diagnosis,
            'treatment': patient.treatment,
            'notes': patient.notes
        }

        print("📋 Fetched Patient Data:", patient_data)  # ✅ Clean debug output

        return jsonify({
            'status': 'success',
            'patient': patient_data
        })

    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404


@app.route('/doctor/update', methods=['POST'])
def update_patient():
    data = request.form
    op_number = data['op_number']
    patient = Patient.query.filter_by(op_number=op_number).first()

    if patient:
        # Update all editable fields
        patient.name = data['name']
        patient.age = data['age']
        patient.height = float(data['height'])
        patient.weight = float(data['weight'])
        patient.location = data['location']
        patient.problem = data['problem']
        patient.available_doctors = data['available_doctors']
        patient.time_in_hospital = int(data['time_in_hospital'])
        patient.n_procedures = int(data['n_procedures'])
        patient.n_lab_procedures = int(data['n_lab_procedures'])
        patient.n_medications = int(data['n_medications'])
        patient.n_outpatient = int(data['n_outpatient'])
        patient.n_inpatient = int(data['n_inpatient'])
        patient.n_emergency = int(data['n_emergency'])
        patient.medical_specialty = data['medical_specialty']
        patient.diag_1 = data['diag_1']
        patient.diag_2 = data['diag_2']
        patient.diag_3 = data['diag_3']
        patient.glucose_test = data['glucose_test']
        patient.A1Ctest = data['A1Ctest']
        patient.change = data['change']
        patient.diabetes_med = data['diabetes_med']
        patient.diagnosis = data['diagnosis']
        patient.treatment = data['treatment']
        patient.notes = data['notes']

        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Patient not found'}), 404

@app.route('/patients')
def get_all_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    results = [
        {
            'op_number': p.op_number,
            'name': p.name,
            'age': p.age,
            'height': p.height,
            'weight': p.weight,
            'location': p.location,
            'problem': p.problem,
            'available_doctors': p.available_doctors,
            'time_in_hospital': p.time_in_hospital,
            'num_lab_procedures': p.num_lab_procedures,
            'risk_score': round(p.risk_score, 2) if p.risk_score is not None else None,
            'diagnosis': p.diagnosis,
            'treatment': p.treatment,
            'notes': p.notes,
            'created_at': p.created_at.strftime("%Y-%m-%d %H:%M")
        } for p in patients
    ]
    return jsonify(results)

@app.route('/doctor/all_patients')
def view_all_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return render_template('all_patients.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)