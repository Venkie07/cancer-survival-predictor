from flask import Flask, render_template, request
import pandas as pd
import joblib
from functools import lru_cache

app = Flask(__name__)

MODEL_PATH = "survival_model.pkl"

# -------------------------------------------------
# Load model once per worker (safe for Gunicorn)
# -------------------------------------------------
@lru_cache(maxsize=1)
def load_model():
    return joblib.load(MODEL_PATH)

# -------------------------------------------------
# Prediction helper
# -------------------------------------------------
def predict_survival(patient_data):
    model = load_model()  # ALWAYS load safely

    df_input = pd.DataFrame([patient_data])

    # Stage mapping
    stage_mapping = {'I': 1, 'II': 2, 'III': 3, 'IV': 4}
    df_input['Stage'] = df_input['Stage'].map(stage_mapping)

    # One-hot encode categorical features
    df_input = pd.get_dummies(
        df_input,
        columns=['Gender', 'Cancer_Type', 'Treatment'],
        drop_first=True
    )

    # Align columns with training data
    training_columns = model.feature_names_in_
    for col in training_columns:
        if col not in df_input.columns:
            df_input[col] = 0

    df_input = df_input[training_columns]

    prediction = model.predict(df_input)[0]
    return round(float(prediction), 1)

# -------------------------------------------------
# Routes
# -------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    predicted_months = None

    # Dropdown options
    genders = ['M', 'F']
    stages = ['I', 'II', 'III', 'IV']
    cancer_types = [
        'Colon', 'Breast', 'Leukemia', 'Brain', 'Skin',
        'Ovarian', 'Pancreatic', 'Liver', 'Lung', 'Prostate'
    ]
    treatments = [
        'Chemotherapy', 'Palliative',
        'Hormone Therapy', 'Radiation', 'Surgery'
    ]

    if request.method == "POST":
        patient_data = {
            "Age": float(request.form["Age"]),
            "Gender": request.form["Gender"],
            "Cancer_Type": request.form["Cancer_Type"],
            "Tumor_Size (cm)": float(request.form["Tumor_Size"]),
            "Stage": request.form["Stage"],
            "Treatment": request.form["Treatment"]
        }

        predicted_months = predict_survival(patient_data)

    return render_template(
        "index.html",
        prediction=predicted_months,
        genders=genders,
        stages=stages,
        cancer_types=cancer_types,
        treatments=treatments
    )

# -------------------------------------------------
# Local run only (Gunicorn ignores this)
# -------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
