import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from io import BytesIO

# Initialize session state for courses and timetable
if 'courses' not in st.session_state:
    st.session_state.courses = []

if 'generated' not in st.session_state:
    st.session_state.generated = False

if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

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
    } for course in st.session_state.courses]

# Function to get the timetable
def get_timetable():
    global st
    timetable_data = []
    for course in st.session_state.courses:
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if course['course_code'] in st.session_state.timetable[day]:
                for session in st.session_state.timetable[day][course['course_code']]:
                    timetable_data.append({
                        'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section'],
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
    course_code = st.text_input("Course Code", key="course_code")
    course_title = st.text_input("Course Title", key="course_title")
    section = st.text_input("Section", key="section")
    credit_hours = st.number_input("Credit Hours", min_value=1, max_value=5, key="credit_hours")
    teacher = st.text_input("Teacher", key="teacher")
    
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
            # Clear the form fields after submission
            st.session_state.course_code = ''
            st.session_state.course_title = ''
            st.session_state.section = ''
            st.session_state.credit_hours = 1
            st.session_state.teacher = ''
        else:
            st.error("Please fill all the fields.")

# Section to assign a resource person (teacher) to a course
st.header("Assign Teacher to a Course")

with st.form(key='assign_teacher_form'):
    course_code = st.selectbox("Select Course", [course['course_code'] for course in get_courses()])
    teacher = st.text_input("Teacher")
    
    submit_button = st.form_submit_button(label="Assign Teacher")

    if submit_button:
        assign_resource_person(course_code, teacher)
        st.success(f"Teacher {teacher} assigned to course {course_code} successfully!")

# Display added courses
st.header("Added Courses")
if st.session_state.courses:
    for course in st.session_state.courses:
        st.write(f"{course['course_code']} - {course['course_title']} (Section: {course['section']}, Teacher: {course['teacher']})")
else:
    st.write("No courses added yet.")

# Function to generate timetable
def generate_timetable():
    if not st.session_state.generated:  # Only generate the timetable if it hasn't been generated already
        # Schedule the courses and generate the timetable, while preserving the old courses
        for course in st.session_state.courses:
            if not any(st.session_state.timetable[day].get(course['course_code']) for day in st.session_state.timetable):
                schedule_course(course['course_code'], course['course_title'], course['section'], course['teacher'], course['credit_hours'])
        
        st.session_state.generated = True  # Mark the timetable as generated

# Function to schedule courses based on credit hours and other constraints
def schedule_course(course_code, course_title, section, teacher, credit_hours):
    num_sessions = credit_hours
    time_slot_index = 0  # Start from the first time slot

    if credit_hours == 1:
        # Lab course: 1 credit hour, schedule three consecutive hours
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = random.choice(rooms)

        # Check if time slots are available for this day and course
        for i in range(3):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        # Update the time slot index (skip three slots)
        time_slot_index = (time_slot_index + 3) % len(time_slots)
    
    elif credit_hours == 2:
        # 2 credit hours: schedule both hours in the same room
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = random.choice(rooms)

        # Check if both consecutive slots are available
        for i in range(2):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        # Update the time slot index (skip two slots)
        time_slot_index = (time_slot_index + 2) % len(time_slots)

    else:
        # For courses with more than 2 credit hours, we schedule one slot at a time
        for _ in range(num_sessions):
            day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
            time = time_slots[time_slot_index]
            room = random.choice(rooms)

            if not is_slot_available(day, time, room):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })

            time_slot_index = (time_slot_index + 1) % len(time_slots)

# Check if a time slot is available for a course
def is_slot_available(day, time, room):
    for course_code in st.session_state.timetable[day]:
        for session in st.session_state.timetable[day][course_code]:
            if session['time'] == time and session['room'] == room:
                return False  # Slot is already taken
    return True

# Button to generate timetable
st.header("Generate Timetable")

generate_button = st.button("Generate Timetable")

if generate_button:
    if st.session_state.courses:
        generate_timetable()
        timetable_data = get_timetable()
        if timetable_data:
            df = pd.DataFrame(timetable_data)
            st.dataframe(df)
    else:
        st.error("Please add courses before generating the timetable.")

# Option to download timetable as Excel file
st.header("Download Timetable")

download_button = st.button("Download Timetable as Excel")

if download_button:
    # Convert the timetable to Excel
    timetable_data = get_timetable()
    if timetable_data:
        df = pd.DataFrame(timetable_data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.download_button(label="Download Excel", data=output, file_name="timetable.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No timetable to download.")
