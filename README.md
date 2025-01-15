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
"/delete-patient" = Delete a Patient from the database
"/update-patient" = Updates an existing patient's information
"/insert-data" = Insert Dummy Data
"/update-treatment-record" = Updates a specific record's information
"/update-user" = Updates User particulars
