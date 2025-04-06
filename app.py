from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
import joblib
import pandas as pd
import os
import datetime
import random

# Flask app setup
app = Flask(__name__)

# Database configuration with multiple binds
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///default.db'  # default (can be unused)
app.config['SQLALCHEMY_BINDS'] = {
    'readmission': 'sqlite:///readmission.db',
    'diabetes': 'sqlite:///diabetes.db'
}

db = SQLAlchemy(app)

# Load models
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
readmission_model = joblib.load(os.path.join(BASE_DIR, "model", "xgboost_readmission_model.pkl"))
readmission_preprocessor = joblib.load(os.path.join(BASE_DIR, "model", "xgboost_preprocessor.pkl"))
diabetes_model = joblib.load(os.path.join(BASE_DIR, "model", "diabetes_model.pkl"))

# Utility function to safely convert to int
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

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
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Create tables for both binds
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/doctor')
def doctor_portal():
    return render_template('doctor.html')

@app.route('/nurse')
def nurse_portal():
    return render_template('nurse.html')

@app.route('/nurse/add_readmission_patient', methods=['POST'])
def add_readmission():
    try:
        data = request.form
        op_number = f"OP{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(100,999)}"

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
def add_diabetes():
    try:
        data = request.form
        op_number = f"OP{datetime.datetime.now().strftime('%Y%m%d')}{random.randint(100,999)}"

        # Map string to numerical encoding for categorical features
        def map_categorical(value, mapping, default=0):
            return mapping.get(value, default)

        # Safely convert to int
        def to_int(val, default=0):
            try:
                return int(val)
            except:
                return default

        # All features needed by the model
        full_input = {
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

        # Match feature column order as expected by model
        FEATURE_COLUMNS = [
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

        input_df = pd.DataFrame([full_input])[FEATURE_COLUMNS]

        # Ensure correct data types
        for col in input_df.select_dtypes(include='object').columns:
            input_df[col] = input_df[col].astype('category')

        # Predict risk
        risk = diabetes_model.predict_proba(input_df)[0][1]

        # Save to database
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
def all_patients():
    model = request.args.get("model", "readmission")
    if model == "diabetes":
        patients = DiabetesData.query.order_by(DiabetesData.created_at.desc()).all()
    else:
        patients = ReadmissionData.query.order_by(ReadmissionData.created_at.desc()).all()

    return render_template("all_patients.html", patients=patients, selected_model=model)

# Doctor route: Get patient details
@app.route('/doctor/get_patient')
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

# Doctor route: Update patient
@app.route('/doctor/update_patient', methods=['POST'])
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
            if key in ['id', 'created_at', 'risk_score']:
                continue
            if hasattr(patient, key):
                attr_type = type(getattr(patient, key))
                try:
                    setattr(patient, key, attr_type(value))
                except:
                    setattr(patient, key, value)

        if model == 'diabetes':
            # Full input as expected by the diabetes model
            full_input = {
                'race': 'Caucasian',
                'gender': 'Female',
                'age': patient.age,
                'admission_type_id': 1,
                'discharge_disposition_id': patient.discharge_disposition_id,
                'admission_source_id': 1,
                'time_in_hospital': patient.time_in_hospital,
                'num_lab_procedures': patient.num_lab_procedures,
                'num_procedures': 0,
                'num_medications': patient.num_medications,
                'number_outpatient': 0,
                'number_emergency': patient.number_emergency,
                'number_inpatient': patient.number_inpatient,
                'diag_1': '250.83',
                'diag_2': '250.01',
                'diag_3': '250.8',
                'number_diagnoses': patient.number_diagnoses,
                'max_glu_serum': 'None',
                'A1Cresult': 'None',
                'metformin': patient.metformin,
                'repaglinide': 'No',
                'nateglinide': 'No',
                'chlorpropamide': 'No',
                'glimepiride': 'No',
                'acetohexamide': 'No',
                'glipizide': 'No',
                'glyburide': 'No',
                'tolbutamide': 'No',
                'pioglitazone': 'No',
                'rosiglitazone': 'No',
                'acarbose': 'No',
                'miglitol': 'No',
                'troglitazone': 'No',
                'tolazamide': 'No',
                'examide': 'No',
                'citoglipton': 'No',
                'insulin': 'No',
                'glyburide-metformin': 'No',
                'glipizide-metformin': 'No',
                'glimepiride-pioglitazone': 'No',
                'metformin-rosiglitazone': 'No',
                'metformin-pioglitazone': 'No',
                'change': patient.change,
                'diabetesMed': patient.diabetesMed
            }

            input_df = pd.DataFrame([full_input])

            # Convert all string columns to category
            for col in input_df.select_dtypes(include='object').columns:
                input_df[col] = input_df[col].astype('category')

            # Predict new risk score
            patient.risk_score = diabetes_model.predict_proba(input_df)[0][1]

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)





