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
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday","Saturday"]
available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]

# Function to add a course
def add_course(course_code, course_title, section, room_type, slot_preference):
    st.session_state.courses.append({
        'course_code': course_code,
        'course_title': course_title,
        'section': section,
        'room_type': room_type,
        'slot_preference': slot_preference
    })

# Function to get available room of a specific type
def get_available_room(room_type):
    available_rooms = [room["name"] for room in st.session_state.rooms if room["type"] == room_type]
    
    if available_rooms:
        selected_room = random.choice(available_rooms)
        st.info(f"Room {selected_room} selected for {room_type} course.")
        return selected_room
    else:
        st.warning(f"No available rooms for {room_type} type.")
        return None

# Function to check if a room is available
def is_room_available(day, time_slot, room, course_code, section):
    for other_course_code in st.session_state.timetable[day]:
        for session in st.session_state.timetable[day].get(other_course_code, []):
            if other_course_code == course_code and session['section'] != section:
                if session['room'] == room and session['time'] == time_slot:
                    return False
            if session['room'] == room and session['time'] == time_slot:
                return False
    return True

# Function to display the timetable in a readable weekly format with improved styling
# Function to display the timetable in a readable weekly format with course titles
def display_timetable():
    timetable_data = []
    for day in days_of_week:
        for course_code, sessions in st.session_state.timetable[day].items():
            for session in sessions:
                timetable_data.append({
                    'Course Code': course_code,
                    'Course Title': next(course['course_title'] for course in st.session_state.courses if course['course_code'] == course_code),  # Find the course title
                    'Day': day,
                    'Time': session['time'],
                    'Room': session['room'],
                    'Section': session['section']
                })
    
    # Display the timetable as a dataframe
    if timetable_data:
        timetable_df = pd.DataFrame(timetable_data)
        timetable_df = timetable_df[['Day', 'Course Code', 'Course Title', 'Section', 'Time', 'Room']]
        
        # Add styling to improve the visual appeal
        styled_df = timetable_df.style \
            .set_table_styles([
                {'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-weight', 'bold')]},
                {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#f2f2f2')]},
                {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#ffffff')]},
                {'selector': 'td', 'props': [('padding', '10px'), ('text-align', 'center')]},
                {'selector': 'table', 'props': [('border-collapse', 'collapse'), ('width', '100%')]}
            ]) \
            .hide(axis="index")
        
        st.dataframe(styled_df)
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
        course_code = course['course_code']
        course_title = course['course_title']
        
        if room_type == "Theory" or room_type == "Lab":  # This includes both PF and DLD courses
            if not allocate_course(course_code, course_title, section, room_type):
                st.warning(f"Scheduling failed for {course_code} Section {section}.")
                return

    st.success("Timetable generated successfully!")
    display_timetable()
def allocate_course(course_code, course_title, section, room_type):
    """
    Allocate a course (Theory or Lab) to a time slot and room.
    """
    available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]
    days = random.sample(days_of_week, 2)  # Pick 2 random days for the course
    selected_slots = random.sample(available_time_slots, 2)  # Pick 2 random slots from available slots
    
    assigned_days = []
    for i, day in enumerate(days):
        selected_slot = selected_slots[i]
        room = get_available_room(room_type)  # Get an available room for the course type
        
        # Ensure the room is available for the selected time
        if is_room_available(day, selected_slot, room, course_code, section):
            st.session_state.timetable[day][course_code].append({
                'time': selected_slot,
                'room': room,
                'section': section
            })
            assigned_days.append((day, selected_slot, room))
            st.info(f"Assigned {course_code} Section {section} to {day} at {selected_slot} in {room}.")
        else:
            st.warning(f"Could not assign {course_code} Section {section} to {day} at {selected_slot}. Retrying assignment.")
            # Try a different room or time slot
            retry_success = False
            for attempt in range(3):  # Try 3 times for conflict resolution
                retry_room = get_available_room(room_type)
                if is_room_available(day, selected_slot, retry_room, course_code, section):
                    st.info(f"Retrying: Assigned {course_code} Section {section} to {day} at {selected_slot} in {retry_room}.")
                    st.session_state.timetable[day][course_code].append({
                        'time': selected_slot,
                        'room': retry_room,
                        'section': section
                    })
                    assigned_days.append((day, selected_slot, retry_room))
                    retry_success = True
                    break
                else:
                    st.warning(f"Retry attempt {attempt+1}: Could not assign {course_code} Section {section} to {day} at {selected_slot}.")
            
            if not retry_success:
                st.error(f"Scheduling failed for {course_code} Section {section} after retries.")
                return False

    st.success(f"Course {course_code} successfully scheduled on {', '.join([f'{day} at {slot}' for day, slot, room in assigned_days])}.")
    return True


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
