import streamlit as st
import random
import pandas as pd  # Ensure pandas is imported
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
    st.session_state.rooms = [
        {"name": "Room 1", "type": "Theory"},
        {"name": "Room 2", "type": "Theory"},
        {"name": "Room 3", "type": "Theory"},
        {"name": "Room 4", "type": "Lab"},
        {"name": "Room 5", "type": "Lab"}
    ]

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

# Function to get available room
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

# Function to allocate 1.5-hour slots on two different days (Theory)
def allocate_theory_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Randomly pick two different days for 1.5-hour blocks
        available_days = days_of_week.copy()
        day1, day2 = random.sample(available_days, 2)

        # Randomly pick 1.5-hour time slots for both days
        time_slot_1 = random.choice(available_time_slots)
        time_slot_2 = random.choice(available_time_slots)

        # Assign the slots
        st.session_state.timetable[day1][course_code].append({'time': time_slot_1, 'room': room})
        st.session_state.timetable[day2][course_code].append({'time': time_slot_2, 'room': room})

# Function to allocate a 3-hour consecutive block (Lab)
def allocate_lab_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose a random day for the lab (only one day)
        available_days = days_of_week.copy()
        random.shuffle(available_days)  # Shuffle days to get a random choice
        
        for day in available_days:
            for i in range(len(available_time_slots) - 1):  # Check if 2 consecutive slots are available for the lab
                # Get 2 consecutive time slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]

                # Assign the 3-hour block to this day
                if not any(session['room'] == room and session['time'] == f"{slot_1} - {slot_2}" for session in st.session_state.timetable[day].get(course_code, [])):
                    st.session_state.timetable[day][course_code].append({
                        'time': f"{slot_1} - {slot_2}",  # Combine the 2 consecutive slots into one 3-hour block
                        'room': room
                    })
                    break  # Stop after scheduling on one day

# Function to add a room
def add_room(room_name, room_type):
    st.session_state.rooms.append({"name": room_name, "type": room_type})
    st.success(f"Room {room_name} added successfully!")

# Function to delete a room
def delete_room(room_name):
    rooms = [room for room in st.session_state.rooms if room['name'] != room_name]
    if len(rooms) == len(st.session_state.rooms):
        st.warning(f"Room {room_name} not found!")
    else:
        st.session_state.rooms = rooms
        st.success(f"Room {room_name} deleted successfully!")

# Display Added Courses
if st.session_state.courses:
    st.subheader("Added Courses:")
    
    try:
        # Ensure courses are structured properly for DataFrame creation
        courses_data = [{
            'Course Code': course.get('course_code', ''),
            'Course Title': course.get('course_title', ''),
            'Section': course.get('section', ''),
            'Room Type': course.get('room_type', ''),
            'Slot Preference': course.get('slot_preference', '')
        } for course in st.session_state.courses]
        
        # Only create DataFrame if there is data
        if courses_data:
            courses_df = pd.DataFrame(courses_data)
            st.dataframe(courses_df)
        else:
            st.warning("No courses available to display.")
    except Exception as e:
        st.error(f"Error while displaying courses: {str(e)}")

# Room Management Section
st.header("Room Management")

# Add Room Form
with st.form(key='add_room_form'):
    room_name = st.text_input("Room Name (e.g., Room 6)")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    add_room_button = st.form_submit_button(label="Add Room")
    
    if add_room_button:
        if room_name:
            add_room(room_name, room_type)
        else:
            st.error("Please provide a room name.")

# Delete Room Form
with st.form(key='delete_room_form'):
    room_to_delete = st.selectbox("Select Room to Delete", [room["name"] for room in st.session_state.rooms])
    delete_room_button = st.form_submit_button(label="Delete Room")
    
    if delete_room_button:
        delete_room(room_to_delete)

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
        for course in st.session_state.courses:
            schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])

        timetable_data = get_timetable()
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)
        st.success("Timetable updated successfully!")
