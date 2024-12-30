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
        days_needed = 2
        time_slots_needed = 1  # 1.5-hour slot per day
    elif slot_preference == "3 Hour consecutive slot":
        # Allocate 1 3-hour consecutive slot
        days_needed = 1
        time_slots_needed = 1  # Just 1 time slot for this preference

    day_count = 0
    for _ in range(days_needed):
        if day_count >= len(days_of_week):
            break
        day = days_of_week[day_count]

        # Check if the room is available for this day
        room = get_available_room(room_type)

        # Assign the correct slot based on preference
        if slot_preference == "1.5 Hour slots":
            time = allocate_1_5_hour_slots(day, room)
        elif slot_preference == "3 Hour consecutive slot":
            time = allocate_3_hour_consecutive_slot(day, room)

        # If time allocation is successful, add to the timetable
        if time:
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})
        
        day_count += 1

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
def allocate_1_5_hour_slots(day, room):
    available_days = [d for d in days_of_week if d != day]  # Avoid same-day allocation
    
    # Try to assign 1.5-hour slots to two different days
    allocated_days = random.sample(available_days, 2)
    time_slot_1 = available_time_slots[random.randint(0, len(available_time_slots) - 2)]
    time_slot_2 = available_time_slots[random.randint(0, len(available_time_slots) - 2)]

    # Ensure that time slots do not overlap
    return f"{allocated_days[0]}: {time_slot_1} (Room: {room}), {allocated_days[1]}: {time_slot_2} (Room: {room})"

# Function to allocate a 3-hour consecutive slot
def allocate_3_hour_consecutive_slot(day, room):
    for i in range(len(available_time_slots) - 2):
        # Check if three consecutive slots are available
        if not is_slot_available(day, available_time_slots[i], room):
            continue
        if not is_slot_available(day, available_time_slots[i + 1], room):
            continue
        if not is_slot_available(day, available_time_slots[i + 2], room):
            continue
        
        # Return the 3-hour consecutive slot
        return f"{available_time_slots[i]} - {available_time_slots[i + 2]} (Room: {room})"

    st.warning(f"No available slots on {day} for 3-hour consecutive preference.")
    return None

# Check if a time slot is available for a course
def is_slot_available(day, time, room):
    for scheduled_day, scheduled_time, scheduled_room in st.session_state.timetable[day].get(room, []):
        if scheduled_time == time:
            return False  # Conflict: same room, same time
    
    return True

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

# Section to generate timetable
if st.button("Generate Timetable"):
    for course in st.session_state.courses:
        schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
    
    timetable_data = get_timetable()
    df = pd.DataFrame(timetable_data)
    st.dataframe(df)
    st.success("Timetable generated successfully!")
