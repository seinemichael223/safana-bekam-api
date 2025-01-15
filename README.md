# safana-bekam-api
Safana Bekam API 

routes.py:

"/" = index
"/signup" = Sign up
"/login" = Login and set cookies
"/logout" = Logs out and deletes cookies
"/secret" = Checks for cookies, if found then you can access
"/export-users" = Exports ALL Users
"/register-patient" = Register a Patient
"/export-patients" = Export the information of ALL patients or 1 specific Patient
"/submit-treatment" = Submit Treatment Record for a Patient
"/export-patient-record" = Export ALL of a specific patient's record
"/export-patient-record-visit" = Export a specific record from a patient
"/export-patient-simplify" = Export ALL of a specific patient's record but only their ID, Frequency, Created Date and Package

"/delete-record" = Delete a specific treatment record
expected FormData:
"record_id=123"

"/delete-patient" = Delete a Patient from the database
expected FormData:
"patient_id=123"

"/update-patient" = Updates an existing patient's information
expected JSON Payload:
{
    "patient_id": 1,
    "name": "Updated Name",
    "mykad": "123456789",
    "gender": "Female",
    "ethnicity": "Malay",
    "p_mobile_no": "0123456789",
    "p_email": "updated_email@example.com",
    "postcode": "54321",
    "state": "Johor",
    "address": "Updated Address",
    "occupation": "Updated Occupation",
    "medical_history": [
        {"condition": "Hypertension", "medicine": "Lisinopril"},
        {"condition": "Asthma", "medicine": "Inhaler"},
        {"condition": "Diabetes", "medicine": "Metformin"}
    ]
}

"/update-treatment-record" = Updates a specific record's information
expected JSON Payload:
{
    "record_id": 1,
    "created_date": "2025-01-11",
    "frequency": 3,
    "blood_pressure_before": "120/80",
    "blood_pressure_after": "115/75",
    "package": "Standard",
    "health_complications": "None",
    "comments": "Patient responded well to treatment",
    "acupuncture_point": [
        {"body_part": "Arm", "coordinate_x": 1.0, "coordinate_y": 2.0, "skin_reaction": 1, "blood_quantity": 2},
        {"body_part": "Leg", "coordinate_x": 3.0, "coordinate_y": 4.0, "skin_reaction": 2, "blood_quantity": 3}
    ]
}

"/update-user" = Update User's information
Expected Formdata:
"user_id=1&email=updatedemail@example.com&username=new_username&mobile_no=1234567890&address=New Address&role=admin&role=therapists"

"/check-patients-monthly" = Checks the number of patients registered in the past 30 days
"/check-patients-daily" = Checks the number of patients registered in the past 24 hours
"/total-patients" = Returns the number of total patients in the database
"/treatment-records-daily" = Returns the number of treatment records created in the last 24 hours
"/insert-data" = Insert Dummy Data
