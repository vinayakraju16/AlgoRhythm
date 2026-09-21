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
- **Server-side authentication** with per-role route guards and CSRF protection
- **Pagination + search** on both patient lists
- **Audit log** recording who created/updated which record
- **Doctor dashboard** with volume, high-risk counts, and average risk
- **CSV export** of patient lists
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

## 🛣 Routes

| Method | Path | Role | Purpose |
| --- | --- | --- | --- |
| GET | `/` | any | Redirects to login |
| GET/POST | `/login` | any | Sign in (POST requires CSRF token) |
| GET | `/logout` | signed-in | Sign out |
| GET | `/healthz` | none | Deploy health check: DB + model load status |
| GET | `/nurse` | nurse | Nurse intake portal |
| POST | `/nurse/add_readmission_patient` | nurse | Create a readmission record |
| POST | `/nurse/add_diabetes_patient` | nurse | Create a diabetes record |
| GET | `/nurse/all_patients` | nurse | Paginated + searchable list |
| GET | `/nurse/edit/<op_number>` | nurse | Edit form |
| POST | `/nurse/update` | nurse | Apply an edit |
| GET | `/doctor` | doctor | Doctor portal |
| GET | `/doctor/dashboard` | doctor | Volume / risk overview |
| GET | `/doctor/audit_log` | doctor | Recent audit entries |
| GET | `/doctor/all_patients` | doctor | Paginated + searchable list |
| GET | `/doctor/get_patient` | doctor | Patient JSON by OP number |
| GET | `/doctor/edit/<op_number>` | doctor | Edit form |
| POST | `/doctor/update_patient` | doctor | Apply an edit (JSON response) |
| POST | `/doctor/update` | doctor | Apply an edit (form post) |
| GET | `/doctor/export/<model>.csv` | doctor | CSV export |

Every state-changing POST requires the session CSRF token (as a `_csrf_token`
form field or an `X-CSRF-Token` header).

---

## 🧪 Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers login success/failure, CSRF rejection, role separation between
the two portals, OP-number uniqueness, pagination, CSV export, the audit log, and
`/healthz`. It points the SQLAlchemy binds at temporary SQLite files, so it never
touches your real databases.

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
- Introduce Flask-Migrate/Alembic for schema migrations
- Move to PostgreSQL — Render's free tier has an ephemeral disk, so SQLite data is lost on redeploy
- Enable model training via UI
- Export patient reports as PDF

---


