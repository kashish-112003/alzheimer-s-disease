import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
from streamlit_option_menu import option_menu
import re
import base64
from fpdf import FPDF
import mysql.connector

# ✅ Database Connection
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="KASHISH@11",
        database="Alzheimers",
        port=3306,
        auth_plugin='mysql_native_password'
    )
    print("Database connection successful")
except mysql.connector.Error as err:
    print("Error connecting to database:", err)
    exit(1)

mycursor = mydb.cursor()

# ✅ Load Model
model = tf.keras.models.load_model('my_model.h5')
class_labels = ['Mild Demented', 'Moderate Demented', 'Non Demented', 'Very Mild Demented']

# ✅ Functions
def preprocess_image(img):
    img = img.convert('RGB').resize((176, 176))
    return np.expand_dims(np.array(img) / 255.0, axis=0)

def validate_phone_number(phone_number):
    if not re.match(r'^\d{10}$', str(phone_number)):
        st.error('Please enter a valid 10-digit contact number!')
        return False
    return True

def validate_name(name):
    if not all(char.isalpha() or char.isspace() for char in name):
        st.error("Name should only contain letters and spaces.")
        return False
    return True

def validate_input(name, age, contact, file):
    if not name or not age or not contact or not file:
        st.error("All fields are required!")
        return False
    return True

def insert_data(name, age, gender, contact, prediction):
    try:
        mycursor.execute(
            "INSERT INTO predictions (Patient_Name, Age, Gender, Contact, Prediction) VALUES (%s, %s, %s, %s, %s)",
            (name, age, gender, contact, prediction)
        )
        mydb.commit()
        print("Record inserted")
    except mysql.connector.Error as err:
        print("Error inserting record:", err)

# ✅ Sidebar Menu
selected = option_menu(None, ["Home", "Alzheimer Detection", "About Us"], icons=["house", "brain", "info-circle"], menu_icon="cast", default_index=0, orientation="horizontal")

# ✅ Home Page
if selected == 'Home':
    st.title("Alzheimer's Disease Detection")
    st.write("""
        This app uses deep learning to detect Alzheimer's from MRI scans.
        The classification stages are:
        - **Mild Demented**
        - **Moderate Demented**
        - **Non Demented**
        - **Very Mild Demented**
    """)

# ✅ About Us Page
if selected == 'About Us':
    st.title("About Us")
    st.write("Developed by **group15**, this app helps detect Alzheimer's disease using MRI scans.")

# ✅ Alzheimer Detection Page
if selected == 'Alzheimer Detection':
    st.title('Alzheimer Detection Web App')
    st.write('Please enter your details and upload an MRI scan.')

    with st.form(key='myform', clear_on_submit=True):
        name = st.text_input('Patient Name')
        age = st.number_input('Age', min_value=1, max_value=150, value=40)
        gender = st.radio('Gender', ('Male', 'Female', 'Other'))
        contact = st.text_input('Contact Number', key='contact')
        file = st.file_uploader('Upload MRI Scan', type=['jpg', 'jpeg', 'png'])
        submit = st.form_submit_button("Submit")  

        # ✅ Check `submit` inside the form
        if submit:
            if validate_input(name, age, contact, file) and validate_phone_number(contact) and validate_name(name):
                st.success('Your details have been recorded.', icon="✅")

                img = Image.open(file)
                png_image = img.convert('RGBA')
                st.image(img, caption='Uploaded MRI Scan', width=200)

                # ✅ Display user details
                st.write(f'**Name:** {name}')
                st.write(f'**Age:** {age}')
                st.write(f'**Gender:** {gender}')
                st.write(f'**Contact:** {contact}')

                # ✅ Predict Alzheimer's stage
                processed = preprocess_image(img)
                prediction = model.predict(processed)
                predicted_class = class_labels[np.argmax(prediction)]
                st.success(f'Prediction: {predicted_class}')

                # ✅ Insert record into database
                insert_data(name, age, gender, contact, predicted_class)

                # ✅ Save prediction results for PDF
                st.session_state["prediction"] = {
                    "name": name,
                    "age": age,
                    "gender": gender,
                    "contact": contact,
                    "predicted_class": predicted_class,
                    "png_image": png_image
                }

# ✅ PDF Report Download Button
if "prediction" in st.session_state:
    export_as_pdf = st.button("Export Report")

    if export_as_pdf:
        data = st.session_state["prediction"]

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(200, 10, 'Alzheimer Detection Report', ln=True, align='C')

        pdf.set_font('Arial', '', 12)
        pdf.cell(200, 10, f'Name: {data["name"]}', ln=True)
        pdf.cell(200, 10, f'Age: {data["age"]}', ln=True)
        pdf.cell(200, 10, f'Gender: {data["gender"]}', ln=True)
        pdf.cell(200, 10, f'Contact: {data["contact"]}', ln=True)
        pdf.cell(200, 10, f'Prediction: {data["predicted_class"]}', ln=True)

        # ✅ Save Image for PDF
        png_file = "uploaded_image.png"
        data["png_image"].save(png_file, "PNG")
        pdf.image(png_file, x=40, y=100, w=50, h=50)

        st.download_button("Download Report", pdf.output(dest="S").encode("latin-1"), "Alzheimer_Report.pdf", "application/pdf")
