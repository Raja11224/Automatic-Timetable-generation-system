import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from io import BytesIO

# Initialize Streamlit session state
if 'courses' not in st.session_state:
    st.session_state.courses = []  # List to store courses
if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))  # Dictionary to hold timetable
if 'teachers' not in st.session_state:
    st.session_state.teachers = []  # List to store teachers
if 'generated' not in st.session_state:
    st.session_state.generated = False  # Flag to track if timetable is generated

# Sample rooms and time slots
rooms = ["CB1-101", "CB1-102", "CB1-103", "CB1-104", "CB1-105", "CB1-106"]
time_slots = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00"]

# Function to get the timetable data
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if course['course_code'] in st.session_state.timetable[day]:
                for session in st.session_state.timetable[day][course['course_code']]:
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
    for course in st.session_state.courses:
        if course['course_code'] == course_code:
            course['teacher'] = teacher
            break

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
            st.session_state.courses.append({
                'course_code': course_code,
                'course_title': course_title,
                'section': section,
                'credit_hours': credit_hours,
                'teacher': teacher
            })
            st.success("Course added successfully!")
        else:
            st.error("Please fill all the fields.")

# Section to show the added courses
st.header("Added Courses")

if st.session_state.courses:
    # Display list of added courses
    courses_df = pd.DataFrame(st.session_state.courses)
    st.dataframe(courses_df)
else:
    st.write("No courses added yet.")

# Section to assign a resource person (teacher) to a course
st.header("Assign Teacher to a Course")

with st.form(key='assign_teacher_form'):
    if st.session_state.courses:
        course_code = st.selectbox("Select Course", [course['course_code'] for course in st.session_state.courses])
        teacher = st.text_input("Teacher")
        
        submit_button = st.form_submit_button(label="Assign Teacher")
        
        if submit_button:
            assign_resource_person(course_code, teacher)
            st.success(f"Teacher {teacher} assigned to course {course_code} successfully!")
    else:
        st.write("Please add courses before assigning teachers.")

# Section to generate timetable
st.header("Generate Timetable")

generate_button = st.button("Generate Timetable")

if generate_button:
    if st.session_state.courses:
        # Here, you would implement the logic to generate a timetable
        # For now, let's just randomly assign times and rooms for simplicity
        if not st.session_state.generated:
            for course in st.session_state.courses:
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
                    time = random.choice(time_slots)
                    room = random.choice(rooms)
                    st.session_state.timetable[day][course['course_code']].append({
                        'time': time,
                        'room': room
                    })
            st.session_state.generated = True
            st.success("Timetable generated successfully!")
        else:
            st.warning("Timetable has already been generated.")
    else:
        st.error("Please add courses before generating the timetable.")

# Fetch timetable data
timetable_data = get_timetable()

# Display timetable section
st.header("Generated Timetable")

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
