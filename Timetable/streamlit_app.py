import streamlit as st
import random
import pandas as pd

# Global variables
courses = []
timetable = {}
rooms = ["CB1-101", "CB1-102", "CB1-103"]
time_slots = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00"]
locked = False

# Function to generate timetable
def generate_timetable():
    global timetable
    timetable = {"Monday": [], "Tuesday": [], "Wednesday": [], "Thursday": [], "Friday": []}
    
    for course in courses:
        section = course["section"]
        credit_hours = course["credit_hours"]
        assigned_times = set()
        
        # If credit hour is 1, we assign three consecutive hours in the same room
        if credit_hours == 1:
            day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            time = "8:00-9:00"
            room = random.choice(rooms)
            for hour in range(3):
                timetable[day].append({
                    "course_code": course["course_code"],
                    "course_title": course["course_title"],
                    "section": section,
                    "time": time,
                    "room": room,
                })
                time = time_slots[(time_slots.index(time) + 1) % len(time_slots)]
        elif credit_hours == 3:
            # If credit hour is 3, we assign two 1.5-hour slots on the same day
            day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            time1 = "8:00-9:30"
            time2 = "9:30-11:00"
            room = random.choice(rooms)
            timetable[day].append({
                "course_code": course["course_code"],
                "course_title": course["course_title"],
                "section": section,
                "time": time1,
                "room": room,
            })
            timetable[day].append({
                "course_code": course["course_code"],
                "course_title": course["course_title"],
                "section": section,
                "time": time2,
                "room": room,
            })
        else:
            # For credit hour = 2, assign a single 2-hour slot
            day = random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            time = "8:00-10:00"
            room = random.choice(rooms)
            timetable[day].append({
                "course_code": course["course_code"],
                "course_title": course["course_title"],
                "section": section,
                "time": time,
                "room": room,
            })
    
    st.session_state["generated"] = True  # Mark timetable as generated

# Function to display the timetable
def display_timetable():
    if "generated" in st.session_state and st.session_state["generated"]:
        st.write("### Timetable")
        for day, courses_on_day in timetable.items():
            st.write(f"**{day}:**")
            for course in courses_on_day:
                st.write(f"{course['course_code']} - {course['course_title']} | Section: {course['section']} | Time: {course['time']} | Room: {course['room']}")
    else:
        st.write("Please generate the timetable first!")

# Function to check if section has overlapping courses
def check_overlapping_courses():
    global timetable
    for day, courses_on_day in timetable.items():
        sections = {}
        for course in courses_on_day:
            section = course["section"]
            time = course["time"]
            if section not in sections:
                sections[section] = []
            sections[section].append(time)
        
        for section, times in sections.items():
            # Check if any section has multiple courses at the same time
            if len(set(times)) != len(times):  # Duplicate times in the same section
                st.error(f"Section {section} has overlapping courses on {day}.")
                return False
    return True

# Streamlit UI
st.title("Timetable Generator")

# Input course information
with st.form("course_form"):
    course_code = st.text_input("Course Code")
    course_title = st.text_input("Course Title")
    section = st.text_input("Section")
    credit_hours = st.selectbox("Credit Hours", [1, 2, 3])
    submit_button = st.form_submit_button("Add Course")

    if submit_button:
        if locked:
            st.warning("Timetable is locked. You cannot add more courses.")
        else:
            courses.append({
                "course_code": course_code,
                "course_title": course_title,
                "section": section,
                "credit_hours": credit_hours,
            })
            st.success(f"Course {course_code} added!")

# Lock timetable
if st.button("Lock Timetable"):
    locked = True
    st.success("Timetable is now locked.")

# Generate timetable
if st.button("Generate Timetable"):
    if not locked:
        generate_timetable()
        if check_overlapping_courses():
            st.success("Timetable generated successfully!")
    else:
        st.warning("You cannot generate a new timetable because it is locked.")

# Display timetable
display_timetable()

# Update timetable by adding new courses
if st.button("Update Timetable"):
    if locked:
        st.warning("You cannot update a locked timetable.")
    else:
        if courses:
            generate_timetable()
            if check_overlapping_courses():
                st.success("Timetable updated successfully!")
        else:
            st.warning("No new courses added.")
