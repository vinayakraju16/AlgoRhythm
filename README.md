# 🏥 AI-Powered Hospital Risk Prediction System

An intelligent web application to predict hospital **readmission** and **diabetes risk** using machine learning models. Built with Flask, Tailwind CSS, and deployed on Render.

---

## 📌 Features

- Separate portals for **Nurse** and **Doctor**
- Predicts:
  - 🏥 **Hospital Readmission Risk**
  - 💉 **Diabetes Risk**
- Dynamic forms based on selected prediction model
- Unique OP number generation
- Doctor dashboard with patient summary and editable form
- Risk score visualization with color indicators:
  - ✅ Green: 0–30% (Low)
  - ⚠️ Yellow: 31–70% (Moderate)
  - 🔴 Red: 71–100% (High)
- Save and update patient records in separate SQLite databases
- Deployed using **Render**

---

## 🛠 Tech Stack

- Python 3.11
- Flask (Web Framework)
- Tailwind CSS (Frontend Styling)
- SQLite (Database)
- XGBoost (ML Models)
- Pandas, NumPy, Joblib

---

## 📁 Project Structure

```
project/
├── app.py                      # Main Flask app
├── requirements.txt           # Python dependencies
├── render.yaml                # Render deployment config
├── runtime.txt                # Pinned Python version for Render
├── instance/
│   ├── diabetes.db           # Database (created at runtime)
│   └── readmission.db        # Database (created at runtime)
├── model/
│   ├── diabetes_model.pkl     # XGBoost classifier
│   ├── preprocessing.pkl      # sklearn preprocessing pipeline
│   └── heart_model.pkl        # XGBoost classifier
├── static/
│   └── style.css              # (optional styling)
├── templates/
│   ├── login.html             # Login Page (POSTs to /login)
│   ├── nurse.html             # Form for Nurse
│   ├── doctor.html            # Doctor Dashboard
│   ├── all_patients.html      # Doctor: view all patients
│   ├── nurse_all_patients.html# Nurse: view all patients
│   ├── doctor_edit_patient.html
│   └── nurse_edit_patient.html
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/vinayakraju16/AlgoRhythm.git
cd AlgoRhythm
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Locally
```bash
python app.py
```
Visit: `http://localhost:5000`

---

## 🧠 Models Used

### 🏥 Hospital Readmission Model
- Input Features:
  - age, time_in_hospital, n_procedures, n_lab_procedures, etc.
- Model: XGBoost classifier (with sklearn preprocessor)

### 💉 Diabetes Risk Model
- Input Features:
  - race, gender, age, diagnosis codes, A1C results, etc.
- Model: XGBoost classifier

---

## 🔐 Authentication

Credentials are read from environment variables, with development defaults:

| Variable | Default |
| --- | --- |
| `DOCTOR_USERNAME` | `doctor` |
| `DOCTOR_PASSWORD` | `admin123` |
| `NURSE_USERNAME` | `nurse` |
| `NURSE_PASSWORD` | `nurse123` |
| `SECRET_KEY` | `dev-secret-change-me` |

Set real values (especially `SECRET_KEY`) before deploying.

---

## 🧪 Sample User Flow
1. 👩‍⚕️ **Nurse logs in** and selects the prediction model
2. Enters patient details ➡️ **Receives OP Number**
3. 👨‍⚕️ **Doctor logs in** with the OP number
4. Sees summary ➡️ Edits data if needed
5. System **recalculates and updates risk score on save**

---

## 🧠 Future Improvements
- Replace environment-variable credentials with a user table / SSO
- Enable model training via UI
- Export patient reports as PDF
- Integrate cloud databases

---


