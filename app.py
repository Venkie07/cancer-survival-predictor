from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)

# ----------------------------
# Load model once and cache
# ----------------------------
@staticmethod
def load_model():
    global model
    if 'model' not in globals():
        model = joblib.load("survival_model.pkl")
    return model

# ----------------------------
# Helper function to predict
# ----------------------------
def predict_survival(patient_data):
    """
    patient_data: dict with keys
    Age, Gender, Cancer_Type, Tumor_Size (cm), Stage, Treatment
    """
    df_input = pd.DataFrame([patient_data])

    # Stage mapping
    stage_mapping = {'I':1, 'II':2, 'III':3, 'IV':4}
    df_input['Stage'] = df_input['Stage'].map(stage_mapping)

    # One-hot encode categorical columns
    df_input = pd.get_dummies(df_input, columns=['Gender','Cancer_Type','Treatment'], drop_first=True)

    # Get training columns from model
    training_columns = model.feature_names_in_
    for col in training_columns:
        if col not in df_input.columns:
            df_input[col] = 0
    df_input = df_input[training_columns]

    # Predict
    prediction = model.predict(df_input)[0]
    return round(prediction, 1)

# ----------------------------
# Flask Routes
# ----------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    predicted_months = None

    # Dropdown options
    genders = ['M', 'F']
    stages = ['I', 'II', 'III', 'IV']
    cancer_types = ['Colon', 'Breast', 'Leukemia', 'Brain', 'Skin',
                    'Ovarian', 'Pancreatic', 'Liver', 'Lung', 'Prostate']
    treatments = ['Chemotherapy', 'Palliative', 'Hormone Therapy', 'Radiation', 'Surgery']

    if request.method == "POST":
        # Get form data
        patient_data = {
            "Age": float(request.form["Age"]),
            "Gender": request.form["Gender"],
            "Cancer_Type": request.form["Cancer_Type"],
            "Tumor_Size (cm)": float(request.form["Tumor_Size"]),
            "Stage": request.form["Stage"],
            "Treatment": request.form["Treatment"]
        }

        # Predict
        predicted_months = predict_survival(patient_data)

    return render_template("index.html", prediction=predicted_months,
                           genders=genders, stages=stages,
                           cancer_types=cancer_types, treatments=treatments)

# ----------------------------
if __name__ == "__main__":
    model = load_model()  # load once when app starts
    app.run(debug=True)