import streamlit as st
import requests
import pandas as pd

# URL of your Flask API (replace with actual URL if deploying online)
flask_url = "http://127.0.0.1:5000"  # For local testing

# Streamlit User Interface
st.title("Course Timetable Generator")

# Section to add a new course
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
            payload = {
                'course_code': course_code,
                'course_title': course_title,
                'section': section,
                'credit_hours': credit_hours,
                'teacher': teacher
            }
            # Send POST request to Flask to add the course
            response = requests.post(f"{flask_url}/add_course", data=payload)
            if response.status_code == 200:
                st.success("Course added successfully!")
            else:
                st.error("Error adding course.")

# Section to assign a resource person (teacher) to a course
st.header("Assign Teacher to a Course")

with st.form(key='assign_teacher_form'):
    course_code = st.selectbox("Select Course", [course['course_code'] for course in requests.get(f"{flask_url}/get_courses").json()])
    teacher = st.text_input("Teacher")
    
    submit_button = st.form_submit_button(label="Assign Teacher")

    if submit_button:
        payload = {
            'course_code': course_code,
            'teacher': teacher
        }
        # Send POST request to Flask to assign the teacher
        response = requests.post(f"{flask_url}/assign_resource_person", data=payload)
        if response.status_code == 200:
            st.success(f"Teacher {teacher} assigned to course {course_code} successfully!")
        else:
            st.error("Error assigning teacher.")

# Display timetable section
st.header("Generated Timetable")

# Fetch timetable data from Flask API
response = requests.get(f"{flask_url}/get_timetable")

if response.status_code == 200:
    timetable = response.json()  # Assuming Flask API sends JSON response
    if timetable:
        df = pd.DataFrame(timetable)
        st.dataframe(df)
    else:
        st.write("No timetable generated yet.")
else:
    st.error("Failed to load timetable from the server.")

# Option to download timetable as Excel file
st.header("Download Timetable")

download_button = st.button("Download Timetable as Excel")

if download_button:
    # Send request to Flask to generate and download the Excel file
    response = requests.get(f"{flask_url}/download_excel")
    if response.status_code == 200:
        st.download_button(label="Download Excel", data=response.content, file_name="timetable.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("Failed to download the timetable.")
