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
- XGBoost & RandomForest (ML Models)
- Pandas, NumPy, Joblib

---

## 📁 Project Structure

```
project/
├── app.py                      # Main Flask app
├── requirements.txt           # Python dependencies
├── render.yaml                # Render deployment config
├── instances/
│   ├── diabetes.db           # Database
│   └── readmission.db        # Database
├── model/
│   ├── diabetes_model.pkl     # Random forest
│   ├── preprocessing.pkl      # Pre-Processing file
│   └── heart_model.pkl        # MLP Model 
├── static/
│   └── style.css              # (optional styling)
├── templates/
│   ├── login.html             # Login Page
│   ├── nurse.html             # Form for Nurse
│   ├── doctor.html            # Doctor Dashboard
│   └── all_patients.html      # View All Patients
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/hospital-risk-predictor.git
cd hospital-risk-predictor
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
- Model: Random Forest (with preprocessor)

### 💉 Diabetes Risk Model
- Input Features:
  - race, gender, age, diagnosis codes, A1C results, etc.
- Model: Trained XGBoost model

---

## 🧪 Sample User Flow
1. 👩‍⚕️ **Nurse logs in** and selects the prediction model
2. Enters patient details ➡️ **Receives OP Number**
3. 👨‍⚕️ **Doctor logs in** with the OP number
4. Sees summary ➡️ Edits data if needed
5. System **recalculates and updates risk score**

---

```yaml
services:
  - type: web
    name: hospital-app
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python app.py"
    autoDeploy: true
```

---

## 🧠 Future Improvements
- Add authentication and user roles
- Enable model training via UI
- Export patient reports as PDF
- Integrate cloud databases

---


