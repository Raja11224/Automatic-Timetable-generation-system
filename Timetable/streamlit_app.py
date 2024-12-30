import streamlit as st
import pandas as pd
from collections import defaultdict
import random

# Initialize session state
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

# Sample time slots (adjust the slots as needed)
time_slots = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00", "1:00-2:00", "2:00-3:00", "3:00-4:00", "4:00-5:00"]

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
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
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
    time_slot_index = 0  # Start from the first time slot
    section_schedule = defaultdict(list)

    # Scheduling logic based on slot preference
    if slot_preference == "3 consecutive 1-hour slots":
        # Assign a lab room for 3 consecutive slots, for a single day
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Lab")  # Get a lab room for the course
        time_slots_needed = 3  # We need 3 consecutive hours in a single day

        # Schedule the course for 3 consecutive slots on the chosen day
        for i in range(time_slots_needed):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, room_type, slot_preference)  # Retry if slot is not available
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})

        # Move the time_slot_index by 3, as 3 hours have been scheduled
        time_slot_index = (time_slot_index + 3) % len(time_slots)

    elif slot_preference == "2 consecutive 1.5-hour slots":
        # Assign a theory room for 2 consecutive 1.5-hour slots
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Theory")  # Get a theory room for the course
        time_slots_needed = 2  # We need 2 slots of 1.5 hours each

        # Schedule the course for two 1.5-hour blocks on the chosen day
        for i in range(time_slots_needed):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, room_type, slot_preference)  # Retry if slot is not available
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})

        # Move the time_slot_index by 2, as 2 slots have been scheduled
        time_slot_index = (time_slot_index + 2) % len(time_slots)

    else:
        # For Normal 1-hour slots, schedule for one hour
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room(room_type)  # Get the appropriate room type (Theory or Lab)
        time_slots_needed = 1  # Only 1 slot is needed for this preference

        # Schedule for one 1-hour slot
        for _ in range(time_slots_needed):
            time = time_slots[time_slot_index]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, room_type, slot_preference)  # Retry if slot is not available
            section_schedule[section].append((day, time, room))
            st.session_state.timetable[day][course_code].append({'time': time, 'room': room})
            time_slot_index = (time_slot_index + 1) % len(time_slots)

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

# Check if a time slot is available for a course
def is_slot_available(day, time, room, section):
    # Check if the section already has a class scheduled at this time
    for scheduled_day, scheduled_time, scheduled_room in st.session_state.timetable[day].get(section, []):
        if scheduled_time == time:
            return False  # Conflict: same section, same time
    
    # Check if the room is already occupied at this time
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
    slot_preference = st.selectbox("Slot Preference", ["3 consecutive 1-hour slots", "2 consecutive 1.5-hour slots", "1-hour slots"])
    
    add_course_button = st.form_submit_button(label="Add Course")
    
    if add_course_button:
        if course_code and course_title and section:
            add_course(course_code, course_title, section, room_type, slot_preference)
            st.success(f"Course {course_code} added successfully!")
        else:
            st.error("Please fill in all fields.")

# Section to generate timetable (locked after generation)
st.header("Generate or Update Timetable")

if not st.session_state.locked:
    if st.button("Generate Timetable"):
        if st.session_state.courses:
            for course in st.session_state.courses:
                schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])

            timetable_data = get_timetable()
            if timetable_data:
                df = pd.DataFrame(timetable_data)
                st.dataframe(df)
                st.session_state.locked = True  # Lock the timetable after generation
                st.success("Timetable successfully generated and locked!")
            else:
                st.error("No timetable to display.")
        else:
            st.error("No courses available. Please add courses first.")
else:
    st.write("The timetable is locked. To add or modify courses, please unlock it.")
    
    unlock_button = st.button("Unlock Timetable")
    if unlock_button:
        st.session_state.locked = False
        st.success("Timetable unlocked. You can now add courses or rooms.")
        
    if st.button("Update Timetable"):
        if st.session_state.courses:
            for course in st.session_state.courses:
                schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
                
            timetable_data = get_timetable()
            df = pd.DataFrame(timetable_data)
            st.dataframe(df)
            st.success("Timetable updated successfully!")
