import streamlit as st
import pandas as pd
from collections import defaultdict
import random
from io import BytesIO

# Initialize session state for courses, rooms, timetable, and other variables
if 'courses' not in st.session_state:
    st.session_state.courses = []

if 'generated' not in st.session_state:
    st.session_state.generated = False

if 'locked' not in st.session_state:
    st.session_state.locked = False

if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

# Initialize an empty dictionary for rooms
if 'rooms' not in st.session_state:
    st.session_state.rooms = {}

# Function to generate timetable
def generate_timetable():
    if not st.session_state.generated:  # Only generate the timetable if it hasn't been generated already
        for course in st.session_state.courses:
            if not any(st.session_state.timetable[day].get(course['course_code']) for day in st.session_state.timetable):
                schedule_course(course['course_code'], course['course_title'], course['section'], course['credit_hours'], course['room_type'], course['slot_preference'])
        st.session_state.generated = True
        st.session_state.locked = True

# Function to get timetable (excluding teacher details)
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        course_times = {'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section']}
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            day_schedule = []
            for session in st.session_state.timetable[day].get(course['course_code'], []):
                day_schedule.append(f"{session['time']} (Room: {session['room']})")
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    return timetable_data

# Function to schedule courses based on credit hours and room type
def schedule_course(course_code, course_title, section, credit_hours, room_type, slot_preference):
    num_sessions = credit_hours
    time_slot_index = 0  # Start from the first time slot
    section_schedule = defaultdict(list)

    if slot_preference == "3 consecutive 1-hour slots":
        # Assign a lab room for 3 consecutive slots
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Lab")  # Get a lab room
        for i in range(3):  # Schedule three 1-hour slots
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, credit_hours, room_type, slot_preference)
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})
        time_slot_index = (time_slot_index + 3) % len(time_slots)

    elif slot_preference == "2 consecutive 1.5-hour slots":
        # Assign a theory room for 2 consecutive 1.5-hour slots
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Theory")  # Get a theory room
        for i in range(2):  # Schedule two 1.5-hour slots
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, credit_hours, room_type, slot_preference)
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})
        time_slot_index = (time_slot_index + 2) % len(time_slots)

    else:
        for _ in range(num_sessions):
            day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
            time = time_slots[time_slot_index]
            room = get_available_room(room_type)  # Get the appropriate room type
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, credit_hours, room_type, slot_preference)
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})
            time_slot_index = (time_slot_index + 1) % len(time_slots)

# Check if a time slot is available for a course
def is_slot_available(day, time, room, section):
    for scheduled_day, scheduled_time, scheduled_room in st.session_state.timetable[day].get(section, []):
        if scheduled_time == time:
            return False  # Conflict: same section, same time
    
    for scheduled_day, scheduled_time, scheduled_room in st.session_state.timetable[day].get(room, []):
        if scheduled_time == time:
            return False  # Conflict: same room, same time
    
    return True

# Function to get available rooms (based on room type) and check for availability
def get_available_room(room_type):
    available_rooms = [room for room, rtype in st.session_state.rooms.items() if rtype == room_type]
    if not available_rooms:
        st.warning(f"No {room_type} rooms available.")
        return None
    return random.choice(available_rooms)

# Streamlit UI
st.title("Course Timetable Generator")

# Add a new course form (First Section)
st.header("Add a New Course")

if st.session_state.locked:
    st.warning("Timetable is locked. New courses will be added without modifying the existing timetable.")

with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code", value="")
    course_title = st.text_input("Course Title", value="")
    section = st.text_input("Section", value="")
    credit_hours = st.number_input("Credit Hours", min_value=1, max_value=5, value=1)
    slot_preference = st.selectbox("Slot Preference", ["3 consecutive 1-hour slots", "2 consecutive 1.5-hour slots", "Normal 1-hour slots"])
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    
    submit_button = st.form_submit_button(label="Add Course")
    
    if submit_button:
        if course_code and course_title and section:
            st.session_state.courses.append({
                'course_code': course_code,
                'course_title': course_title,
                'section': section,
                'credit_hours': credit_hours,
                'room_type': room_type,
                'slot_preference': slot_preference
            })
            st.success("Course added successfully!")
        else:
            st.error("Please fill all the fields.")

# Manage Rooms Section (Add/Delete Room)
st.header("Manage Rooms")

# Add Room Form
with st.form(key='add_room_form'):
    room_name = st.text_input("Room Name (e.g., CB1-107)")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    
    add_room_button = st.form_submit_button(label="Add Room")
    
    if add_room_button:
        if room_name and room_type:
            if room_name not in st.session_state.rooms:
                st.session_state.rooms[room_name] = room_type
                st.success(f"Room {room_name} added successfully as a {room_type} room.")
            else:
                st.warning(f"Room {room_name} already exists.")
        else:
            st.error("Please fill in both room name and room type.")

# Delete Room Form
with st.form(key='delete_room_form'):
    room_to_delete = st.selectbox("Select Room to Delete", list(st.session_state.rooms.keys()))
    
    delete_room_button = st.form_submit_button(label="Delete Room")
    
    if delete_room_button:
        if room_to_delete:
            del st.session_state.rooms[room_to_delete]
            st.success(f"Room {room_to_delete} deleted successfully.")
            st.rerun()  # Refresh the page to update the room list
        else:
            st.warning("No room selected for deletion.")

# Generate Timetable Button
if st.button("Generate Timetable"):
    generate_timetable()
    timetable_data = get_timetable()
    if timetable_data:
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)

