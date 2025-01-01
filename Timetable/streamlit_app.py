import random
import pandas as pd
import streamlit as st
from collections import defaultdict

# Initialize session state
if 'courses' not in st.session_state:
    st.session_state.courses = []

if 'rooms' not in st.session_state:
    st.session_state.rooms = []

if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

# Sample data
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]

# Function to add courses
def add_course(course_code, course_title, section, room_type, slot_preference):
    st.session_state.courses.append({
        'course_code': course_code,
        'course_title': course_title,
        'section': section,
        'room_type': room_type,
        'slot_preference': slot_preference
    })

# Function to get available room based on type (Theory/Lab)
def get_available_room(room_type):
    available_rooms = [room['name'] for room in st.session_state.rooms if room['type'] == room_type]
    if available_rooms:
        return random.choice(available_rooms)
    return None

# Function to allocate 1.5-hour blocks for theory courses
def allocate_1_5_hour_slots(course_code, room_type):
    room = get_available_room(room_type)
    if room:
        available_days = days_of_week.copy()
        selected_days = random.sample(available_days, 2)  # Pick two different days
        for day in selected_days:
            time_slot = random.choice(available_time_slots)
            st.session_state.timetable[day][course_code].append({'time': time_slot, 'room': room})

# Function to allocate a 3-hour consecutive block for lab courses
def allocate_3_hour_consecutive_slot(course_code, room_type):
    room = get_available_room(room_type)
    if room:
        available_days = days_of_week.copy()
        for day in available_days:
            # Try to assign a 3-hour consecutive block
            for i in range(len(available_time_slots) - 2):  # Look for 3 consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]
                slot_3 = available_time_slots[i + 2]
                # Assign the 3-hour block
                st.session_state.timetable[day][course_code].append({
                    'time': f"{slot_1} - {slot_3}",
                    'room': room
                })
                break
            else:
                continue

# Function to generate the timetable for all courses
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        course_times = {'Course Code': course['course_code'], 'Course Title': course['course_title'], 'Section': course['section']}
        
        for day in days_of_week:
            day_schedule = []
            for session in st.session_state.timetable[day].get(course['course_code'], []):
                day_schedule.append(f"{session['time']} (Room: {session['room']})")
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    return timetable_data

# Streamlit User Interface
st.title("Course Timetable Generator")

# Add courses
st.header("Add a New Course")
with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code")
    course_title = st.text_input("Course Title")
    section = st.text_input("Section")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    slot_preference = st.selectbox("Slot Preference", ["1.5 Hour slots", "3 Hour consecutive slot"])

    add_course_button = st.form_submit_button(label="Add Course")
    if add_course_button:
        if course_code and course_title and section:
            add_course(course_code, course_title, section, room_type, slot_preference)
            st.success(f"Course {course_code} added successfully!")
        else:
            st.error("Please fill in all fields.")

# Show all added courses
if st.session_state.courses:
    st.header("Added Courses")
    course_data = []
    for course in st.session_state.courses:
        course_data.append({
            'Course Code': course['course_code'],
            'Course Title': course['course_title'],
            'Section': course['section'],
            'Room Type': course['room_type'],
            'Slot Preference': course['slot_preference']
        })
    df_courses = pd.DataFrame(course_data)
    st.dataframe(df_courses)

# Manage rooms (Add rooms)
st.header("Manage Rooms")
with st.form(key="add_room_form"):
    room_name = st.text_input("Room Name")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    add_room_button = st.form_submit_button(label="Add Room")
    if add_room_button and room_name:
        st.session_state.rooms.append({'name': room_name, 'type': room_type})
        st.success(f"Room {room_name} added successfully!")

# Generate timetable
if st.button("Generate Timetable"):
    # Allocate courses based on their preferences
    for course in st.session_state.courses:
        if course['slot_preference'] == "1.5 Hour slots":
            allocate_1_5_hour_slots(course['course_code'], course['room_type'])
        elif course['slot_preference'] == "3 Hour consecutive slot":
            allocate_3_hour_consecutive_slot(course['course_code'], course['room_type'])
    
    timetable_data = get_timetable()
    df = pd.DataFrame(timetable_data)
    st.dataframe(df)
    st.success("Timetable generated successfully!")

# Update timetable (if generated)
if st.session_state.courses:
    st.header("Update Timetable")
    if st.button("Update Timetable"):
        # Reassign timetable based on any new updates
        for course in st.session_state.courses:
            if course['slot_preference'] == "1.5 Hour slots":
                allocate_1_5_hour_slots(course['course_code'], course['room_type'])
            elif course['slot_preference'] == "3 Hour consecutive slot":
                allocate_3_hour_consecutive_slot(course['course_code'], course['room_type'])
        
        timetable_data = get_timetable()
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)
        st.success("Timetable updated successfully!")
