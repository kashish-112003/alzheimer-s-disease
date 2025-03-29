import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
from streamlit_option_menu import option_menu
import re
import base64
from fpdf import FPDF
import mysql.connector

# Connect to the MySQL database
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

# Get a cursor object to execute SQL queries
mycursor = mydb.cursor()

st.markdown("""
<style>
    button.step-up {display: none;}
    button.step-down {display: none;}
    div[data-baseweb] {border-radius: 4px;}
</style>""", unsafe_allow_html=True)

def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = f'''
    <style>
    .stApp {{
    background-image: url("data:image/png;base64,{bin_str}");
    background-position: center;
    background-size: cover;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

# Adjust path if needed
set_background(r"C:\Users\KIIT\Documents\Alzheimers-disease-detection-main\Alzheimers-disease-detection-main\images\bg3.jpg")

# Load the saved model
model = tf.keras.models.load_model('my_model.h5')

# Define the class labels
class_labels = ['Mild Demented', 'Moderate Demented', 'Non Demented', 'Very Mild Demented']

# Define the function to preprocess a single image
def preprocess_image(img):
    img = img.convert('RGB')
    img = img.resize((176, 176))
    img = np.array(img)
    img = img / 255.0
    img = np.expand_dims(img, axis=0)
    return img

def validate_phone_number(phone_number):
    pattern = r'^\d{10}$'
    contact = re.match(pattern, str(phone_number))
    if not contact:
        st.error('Please enter a 10 digit number!')
        return False
    return True

def validate_name(name):
    if not all(char.isalpha() or char.isspace() for char in name):
        st.error("Name should not contain numbers or special characters.")
        return False
    return True

def validate_input(name, age, contact, file):
    if not name:
        st.error('Please enter the patient\'s name!')
        return False
    if not age:
        st.error('Please enter your age!')
        return False
    if not contact:
        st.error('Please enter your contact number!')
        return False
    if not file:
        st.error('Please upload the MRI Scan!')
        return False
    return True

selected = option_menu(
    menu_title=None,
    options=["Home", "Alzhiemer Detection", "About US"],
    icons=["house", "book", "envelope"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
)
if selected =='Home':
    def app():
     st.title("Alzheimer's Disease")
     st.write("Alzheimer disease is the most common type of dementia. It is a progressive disease beginning with mild memory loss and possibly leading to loss of the ability to carry on a conversation and respond to the environment. Alzheimer disease involves parts of the brain that control thought, memory, and language.")
     st.write("Using this website, you can find out that does your MRI scan have Alzheimer's disease. It is classified according to four different stages of Alzheimer's disease.")
     st.write('1. Mild Demented')
     st.write("2. Very Mild Demented")
     st.write("3. Moderate Demented")
     st.write("4. Non Demented")

if selected =='About US':
    def app():
        st.title('Welcome!')
        st.write('This web app uses a CNN model to recognize the presence of Alzheimer diasease in any age group. Leaving behind the traditional method of MRI Scans you can now get yourself checked through our protable web APP and you can get your report within no time.')
        st.write('This web app is a MINi Project made by Shubham Shinde')

if selected == 'Alzhiemer Detection':
    st.title('Alzheimer Detection Web App')
    st.write('Please enter your personal details along with an MRI scan.')

    with st.form(key='myform', clear_on_submit=True):
        name = st.text_input('Name')
        age = st.number_input('Age', min_value=1, max_value=150, value=40)
        gender = st.radio('Gender', ('Male', 'Female', 'Other'))
        contact = st.text_input('Contact Number', value='', key='contact')
        file = st.file_uploader('Upload an image', type=['jpg', 'jpeg', 'png'])
        submit = st.form_submit_button("Submit")  # ✅ Defined inside the form
        

    def insert_data(name, age, gender, contact, prediction):
        try:
          sql = "INSERT INTO predictions (Patient_Name, Age, Gender, Contact, Prediction) VALUES (%s, %s, %s, %s, %s)"
          val = (name, age, gender, contact, prediction)
          mycursor.execute(sql, val)
          mydb.commit()
          print(mycursor.rowcount, "record inserted")
        except mysql.connector.Error as err:
          print("Error inserting record:", err)

    # ✅ Ensure `submit` is checked inside this block
if submit and file and validate_input(name, age, contact, file) and validate_phone_number(contact) and validate_name(name):
    st.success('Your personal information has been recorded.', icon="✅")

    # ✅ Fixed: Open the uploaded image correctly
    img = Image.open(file)  
    png_image = img.convert('RGBA')  # Convert to RGBA for PDF compatibility

    # ✅ Display the image correctly
    st.image(img, caption='Uploaded Image', width=200)

    st.write('Name:', name)
    st.write('Age:', age)
    st.write('Gender:', gender)
    st.write('Contact:', contact)

    # Preprocess and predict
    processed = preprocess_image(img)
    prediction = model.predict(processed)
    prediction = np.argmax(prediction, axis=1)
    
    st.success(f'The predicted class is: {class_labels[prediction[0]]}')
    result_str = 'Name: {}\nAge: {}\nGender: {}\nContact: {}\nPrediction for Alzheimer: {}'.format(
                     name, age, gender, contact, class_labels[prediction[0]])

    # Insert data into the database
    insert_data(name, age, gender, contact, class_labels[prediction[0]])
    

    # ✅ Export PDF button is outside the form (so it remains clickable after form submission)
    export_as_pdf = st.button("Export Report")

    def create_download_link(val, filename):
                    b64 = base64.b64encode(val)  # val looks like b'...'
                    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download file</a>'


if export_as_pdf:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font('Times', 'B', 24)
            pdf.cell(200, 20, 'Alzheimer Detection Report', 0, 1, 'C')

            pdf.set_font('Arial', '', 12)
            pdf.cell(200, 10, f'Name: {name}', 0, 1)
            pdf.cell(200, 10, f'Age: {age}', 0, 1)
            pdf.cell(200, 10, f'Gender: {gender}', 0, 1)
            pdf.cell(200, 10, f'Contact: {contact}', 0, 1)

            # ✅ Fixed: Save uploaded image to a temp file for PDF
            png_file = "uploaded_image.png"
            png_image.save(png_file, "PNG")
            pdf.cell(200, 10, 'MRI scan:', 0, 1)
            pdf.image(png_file, x=40, y=80, w=50, h=50)  

            pdf.cell(200, 10, f'Prediction for Alzheimer: {class_labels[prediction[0]]}', 0, 1)

            st.download_button("Download Report", pdf.output(dest="S").encode("latin-1"), "report.pdf", "application/pdf")
