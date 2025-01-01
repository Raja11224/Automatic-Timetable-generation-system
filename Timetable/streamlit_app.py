import streamlit as st
from collections import defaultdict
import random
import pandas as pd

# Initialize session state for courses, timetable, etc.
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

# Initialize the course-related state variables to None or empty strings
if 'course_code' not in st.session_state:
    st.session_state.course_code = ""

if 'course_title' not in st.session_state:
    st.session_state.course_title = ""

if 'section' not in st.session_state:
    st.session_state.section = ""

# Sample days of the week
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]

# Function to get courses
def get_courses():
    return [{
        'course_code': course['course_code'],
        'course_title': course['course_title'],
        'section': course['section'],
    } for course in st.session_state.courses]

# Function to get the timetable
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        course_times = {'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section']}
        
        # For each day of the week, check if this course has a scheduled time on that day
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

# Function to add a room
def add_room(room_name, room_type):
    st.session_state.rooms.append({'name': room_name, 'type': room_type})

# Function to delete a room
def delete_room(room_name):
    st.session_state.rooms = [room for room in st.session_state.rooms if room['name'] != room_name]

# Function to schedule courses based on slot preference
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    if slot_preference == "1.5 Hour slots":
        # Allocate 2 1.5-hour slots on separate days
        allocate_1_5_hour_slots(course_code, course_title, section, room_type)
    elif slot_preference == "3 Hour consecutive slot":
        # Allocate 1 3-hour consecutive slot
        allocate_3_hour_consecutive_slot(course_code, course_title, section, room_type)

# Helper function to get available room
def get_available_room(room_type):
    available_rooms = []
    for room in st.session_state.rooms:
        if room_type == "Lab" and room["type"] == "Lab":
            available_rooms.append(room["name"])
        elif room_type == "Theory" and room["type"] == "Theory":
            available_rooms.append(room["name"])

    if available_rooms:
        return random.choice(available_rooms)
    else:
        st.warning(f"No available rooms for {room_type} type.")
        return None

# Function to allocate 1.5 hour slots on two different days
def allocate_1_5_hour_slots(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        available_days = days_of_week.copy()  # Available days for assignment
        # Randomly pick two different days for 1.5-hour slots
        day1, day2 = random.sample(available_days, 2)

        # Assign 1.5-hour slots on each day
        time_slot_1 = random.choice(available_time_slots)
        time_slot_2 = random.choice(available_time_slots)

        # Assign the slots
        st.session_state.timetable[day1][course_code].append({'time': time_slot_1, 'room': room})
        st.session_state.timetable[day2][course_code].append({'time': time_slot_2, 'room': room})

# Function to allocate a 3-hour consecutive slot
def allocate_3_hour_consecutive_slot(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Try to assign a 3-hour consecutive slot on any available day
        available_days = days_of_week.copy()
        for day in available_days:
            for i in range(len(available_time_slots) - 2):  # Check if 3 consecutive slots are available
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]
                slot_3 = available_time_slots[i + 2]

                # If these slots are free on this day, assign the 3-hour slot
                st.session_state.timetable[day][course_code].append({
                    'time': f"{slot_1} - {slot_3}",
                    'room': room
                })
                break
            else:
                continue

# Streamlit User Interface
st.title("Course Timetable Generator")

# Section to add a new course
st.header("Add a New Course")

with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code", value=st.session_state.course_code)
    course_title = st.text_input("Course Title", value=st.session_state.course_title)
    section = st.text_input("Section", value=st.session_state.section)
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    slot_preference = st.selectbox("Slot Preference", ["1.5 Hour slots", "3 Hour consecutive slot"])
    
    add_course_button = st.form_submit_button(label="Add Course")
    
    if add_course_button:
        if course_code and course_title and section:
            add_course(course_code, course_title, section, room_type, slot_preference)
            st.success(f"Course {course_code} added successfully!")
        else:
            st.error("Please fill in all fields.")

# Section to manage rooms (Add and Delete rooms)
st.header("Manage Rooms")

# Add Room Section
with st.form(key="add_room_form"):
    room_name = st.text_input("Room Name")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    
    add_room_button = st.form_submit_button(label="Add Room")
    
    if add_room_button:
        if room_name:
            add_room(room_name, room_type)
            st.success(f"Room {room_name} added successfully!")
        else:
            st.error("Please provide a room name.")

# Delete Room Section
room_to_delete = st.selectbox("Select Room to Delete", st.session_state.rooms, format_func=lambda room: room['name'])
delete_room_button = st.button("Delete Room")
if delete_room_button:
    delete_room(room_to_delete)
    st.success(f"Room {room_to_delete} deleted successfully!")

# Section to display the list of added courses at the bottom
st.header("Courses Added")

if st.session_state.courses:
    courses_df = pd.DataFrame(st.session_state.courses)
    st.dataframe(courses_df)
else:
    st.write("No courses added yet.")

# Section to generate timetable
if not st.session_state.locked:
    if st.button("Generate Timetable"):
        for course in st.session_state.courses:
            schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
        
        timetable_data = get_timetable()
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)
        st.session_state.generated = True
        st.session_state.locked = True  # Lock timetable after generation
        st.success("Timetable generated successfully!")

# Section to update timetable (only allowed after generation and locked)
if st.session_state.generated and st.session_state.locked:
    st.header("Update Timetable")
    if st.button("Update Timetable"):
        # Schedule any newly added courses or updated preferences
        for course in st.session_state.courses:
            schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])

        timetable_data = get_timetable()
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)
        st.session_state.locked = True  # Keep the timetable locked
        st.success("Timetable updated successfully!")
