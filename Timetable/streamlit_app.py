import streamlit as st
import random
import pandas as pd
from collections import defaultdict

# Initialize session state for courses, timetable, rooms, etc.
if 'courses' not in st.session_state:
    st.session_state.courses = []

if 'generated' not in st.session_state:
    st.session_state.generated = False

if 'locked' not in st.session_state:
    st.session_state.locked = False

if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

if 'rooms' not in st.session_state:
    st.session_state.rooms = []

# Sample days of the week and time slots
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]

# Function to get timetable
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        course_times = {'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section']}
        
        for day in days_of_week:
            day_schedule = []
            for session in st.session_state.timetable[day].get(course['course_code'], []):
                day_schedule.append(f"{session['time']} (Room: {session['room']})")
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    return timetable_data

# Function to add a course
def add_course(course_code, course_title, section, room_type, slot_preference):
    st.session_state.courses.append({
        'course_code': course_code,
        'course_title': course_title,
        'section': section,
        'room_type': room_type,
        'slot_preference': slot_preference
    })

# Function to display the timetable in a readable weekly format
def display_timetable():
    timetable_data = []
    for day in days_of_week:
        for course_code, sessions in st.session_state.timetable[day].items():
            for session in sessions:
                timetable_data.append({
                    'Course Code': course_code,
                    'Day': day,
                    'Time': session['time'],
                    'Room': session['room'],
                    'Section': session['section']
                })
    
    # Display the timetable as a dataframe
    if timetable_data:
        timetable_df = pd.DataFrame(timetable_data)
        timetable_df = timetable_df[['Day', 'Course Code', 'Section', 'Time', 'Room']]
        st.dataframe(timetable_df)
    else:
        st.warning("No timetable generated yet.")

def generate_timetable():
    """
    Try to generate the timetable by scheduling all the courses.
    """
    # Reset the timetable before starting
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

    for course in st.session_state.courses:
        room_type = course['room_type']
        section = course['section']
        if room_type == "Theory":
            if not allocate_theory_course(course['course_code'], course['course_title'], section, room_type):
                st.warning(f"Scheduling failed for {course['course_code']} Section {section}.")
                return

    st.success("Timetable generated successfully!")
    display_timetable()

def allocate_theory_course(course_code, course_title, section, room_type):
    available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]
    days = random.sample(days_of_week, 2)
    selected_slots = random.sample(available_time_slots, 2)
    
    assigned_days = []
    for i, day in enumerate(days):
        selected_slot = selected_slots[i]
        room = get_available_room(room_type)
        
        if is_room_available(day, selected_slot, room, course_code, section):
            st.session_state.timetable[day][course_code].append({
                'time': selected_slot,
                'room': room,
                'section': section
            })
            assigned_days.append((day, selected_slot, room))
            st.info(f"Assigned {course_code} Section {section} to {day} at {selected_slot} in {room}.")
        else:
            st.warning(f"Could not assign {course_code} Section {section} to {day} at {selected_slot}. Trying again.")
            return False

    st.success(f"Theory course {course_code} successfully scheduled on {', '.join([f'{day} at {slot}' for day, slot, room in assigned_days])}.")
    return True


# Streamlit User Interface

st.title("Timetable Generator")

# Section to add a new course
st.header("Add a New Course")

with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code")
    course_title = st.text_input("Course Title")
    section = st.text_input("Section")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    slot_preference = st.selectbox("Slot Preference", ["1.5 Hour blocks", "3 Hour consecutive block"])
    
    add_course_button = st.form_submit_button(label="Add Course")
    
    if add_course_button:
        if course_code and course_title and section:
            add_course(course_code, course_title, section, room_type, slot_preference)
            st.success(f"Course {course_code} added successfully!")
        else:
            st.error("Please fill in all fields.")

# Display Added Courses
if st.session_state.courses:
    st.subheader("Added Courses:")
    courses_df = pd.DataFrame([{
        'Course Code': course['course_code'],
        'Course Title': course['course_title'],
        'Section': course['section'],
        'Room Type': course['room_type'],
        'Slot Preference': course['slot_preference'],
    } for course in st.session_state.courses])
    st.dataframe(courses_df)

# Room Management Section
st.header("Room Management")

# Add Room Form
with st.form(key='add_room_form'):
    room_name = st.text_input("Room Name")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    add_room_button = st.form_submit_button(label="Add Room")

    if add_room_button:
        if room_name and room_type:
            st.session_state.rooms.append({"name": room_name, "type": room_type})
            st.success(f"Room {room_name} added successfully!")
        else:
            st.error("Please fill in all fields.")

# Display Rooms
if st.session_state.rooms:
    st.subheader("Available Rooms:")
    rooms_df = pd.DataFrame(st.session_state.rooms)
    st.dataframe(rooms_df)

# Button to Generate Timetable
if st.button("Generate Timetable"):
    generate_timetable()
