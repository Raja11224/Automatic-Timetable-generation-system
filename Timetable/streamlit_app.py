import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from io import BytesIO

# Global storage for courses, timetable, and teachers
courses = []
timetable = defaultdict(lambda: defaultdict(list))  # Dictionary to hold the timetable for each day
teachers = []  # List to store unique teachers
generated = False  # Flag to track if timetable has been generated

# Sample rooms for simplicity
rooms = ["CB1-101", "CB1-102", "CB1-103", "CB1-104", "CB1-105", "CB1-106"]
time_slots = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00"]

# Function to get courses
def get_courses():
    return [{
        'course_code': course['course_code'],
        'course_title': course['course_title'],
        'section': course['section'],
        'teacher': course['teacher']
    } for course in courses]

# Function to get the timetable
def get_timetable():
    global timetable
    timetable_data = []
    for course in courses:
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if course['course_code'] in timetable[day]:
                for session in timetable[day][course['course_code']]:
                    timetable_data.append({
                        'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section'],
                        'Credit Hours': course['credit_hours'],
                        'Teacher': course['teacher'],
                        'Day': day,
                        'Time': session['time'],
                        'Room': session['room']
                    })
    return timetable_data

# Function to assign a teacher to a course
def assign_resource_person(course_code, teacher):
    for course in courses:
        if course['course_code'] == course_code:
            course['teacher'] = teacher
            break

# Streamlit User Interface with custom styling
st.markdown("""
    <style>
        .header-section {
            text-align: center;
            margin-bottom: 30px;
        }

        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
            padding: 10px 30px;
            font-size: 16px;
            border-radius: 5px;
            text-decoration: none;
        }

        .btn-primary:hover {
            background-color: #0056b3;
            border-color: #004085;
        }

        .btn-success {
            background-color: #28a745;
            border-color: #28a745;
            padding: 10px 30px;
            font-size: 16px;
            border-radius: 5px;
            text-decoration: none;
        }

        .btn-success:hover {
            background-color: #218838;
            border-color: #1e7e34;
        }

        .container {
            background-color: white;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            border-radius: 10px;
            padding: 30px;
            margin-top: 50px;
            width: 90%;
            max-width: 1200px;
        }

        .table th, .table td {
            text-align: center;
        }

        .table th {
            background-color: #007bff;
            color: white;
        }

        .table tbody tr:hover {
            background-color: #f1f1f1;
        }
    </style>
""", unsafe_allow_html=True)

# Page Title and Header
st.markdown("""
    <div class="header-section">
        <h1>UMT Automated Timetable Generator</h1>
        <p class="lead">System developed by INFS Faculty</p>
        <hr>
    </div>
""", unsafe_allow_html=True)

# Add Course Section
st.header("Add a New Course")

with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code")
    course_title = st.text_input("Course Title")
    section = st.text_input("Section")
    credit_hours = st.number_input("Credit Hours", min_value=1, max_value=5)
    teacher = st.text_input("Teacher")
    
    # Submit button to add course
    submit_button = st.form_submit_button(label="Add Course")
    
    if submit_button:
        if course_code and course_title and section and teacher:
            courses.append({
                'course_code': course_code,
                'course_title': course_title,
                'section': section,
                'credit_hours': credit_hours,
                'teacher': teacher
            })
            st.success("Course added successfully!")
        else:
            st.error("Please fill all the fields.")

# Assign Teacher Section
st.header("Assign Teacher to a Course")

with st.form(key='assign_teacher_form'):
    course_code = st.selectbox("Select Course", [course['course_code'] for course in get_courses()])
    teacher = st.text_input("Teacher")
    
    submit_button = st.form_submit_button(label="Assign Teacher")

    if submit_button:
        assign_resource_person(course_code, teacher)
        st.success(f"Teacher {teacher} assigned to course {course_code} successfully!")

# Display Timetable Section
st.header("Generated Timetable")

# Fetch timetable data
timetable_data = get_timetable()

if timetable_data:
    df = pd.DataFrame(timetable_data)
    st.dataframe(df)
else:
    st.write("No timetable generated yet.")

# Option to download timetable as Excel file
st.header("Download Timetable")

download_button = st.button("Download Timetable as Excel")

if download_button:
    # Convert the timetable to Excel
    if timetable_data:
        df = pd.DataFrame(timetable_data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.download_button(label="Download Excel", data=output, file_name="timetable.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No timetable to download.")
