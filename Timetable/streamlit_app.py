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

# Function to get available room of a specific type
def get_available_room(room_type):
    available_rooms = [room["name"] for room in st.session_state.rooms if room["type"] == room_type]
    if available_rooms:
        return random.choice(available_rooms)
    else:
        st.warning(f"No available rooms for {room_type} type.")
        return None

# Function to check if room is available at the given time
def is_room_available(day, time_slot, room, course_code):
    # Check if any session for this course is scheduled at the same time in the same room
    for other_course_code in st.session_state.timetable[day]:
        if course_code != other_course_code:
            for session in st.session_state.timetable[day].get(other_course_code, []):
                if session['time'] == time_slot and session['room'] == room:
                    return False  # Room is already occupied at that time
    return True  # Room is available

# Function to allocate a Lab course (2 consecutive 1.5-hour blocks on a single day)
def allocate_lab_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose a random day for the lab (only one day)
        available_days = days_of_week.copy()
        random.shuffle(available_days)

        # Iterate over the shuffled days and try to assign the lab to one day
        for day in available_days:
            # Check for 2 consecutive time slots availability (1.5 hour x 2)
            for i in range(len(available_time_slots) - 1):  # Ensure 2 consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]

                # If the room is available, assign the 3-hour block
                if is_room_available(day, f"{slot_1} - {slot_2}", room, course_code):
                    st.session_state.timetable[day][course_code].append({
                        'time': f"{slot_1} - {slot_2}",
                        'room': room
                    })
                    break  # Once scheduled, stop and break
            break  # Once scheduled, stop after assigning to one day

# Function to allocate Theory course (1.5-hour blocks on two different days)
def allocate_theory_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose random days for the theory course (two different days)
        available_days = days_of_week.copy()
        random.shuffle(available_days)

        # Iterate over the shuffled days and try to assign the theory to two days
        assigned_slots = 0
        for day in available_days:
            if assigned_slots >= 2:  # Assign only on two different days
                break
            # Check for 1.5-hour time slot availability
            for i in range(len(available_time_slots)):
                slot_1 = available_time_slots[i]

                # If the time slot is available, assign the 1.5-hour block
                if is_room_available(day, slot_1, room, course_code):
                    st.session_state.timetable[day][course_code].append({
                        'time': slot_1,
                        'room': room
                    })
                    assigned_slots += 1
                    break  # Once assigned to this day, stop and go to the next day

# Function to schedule a course (Theory or Lab)
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    # Check if the course has already been scheduled
    if course_code in st.session_state.timetable:
        return  # Skip allocation if already scheduled (no warning shown)

    # Proceed with scheduling the course if not already scheduled
    if room_type == "Theory" and slot_preference == "1.5 Hour blocks":
        allocate_theory_course(course_code, course_title, section, room_type)
    elif room_type == "Lab" and slot_preference == "3 Hour consecutive block":
        allocate_lab_course(course_code, course_title, section, room_type)

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
    for course in st.session_state.courses:
        schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
    
    timetable_data = get_timetable()
    timetable_df = pd.DataFrame(timetable_data)
    st.dataframe(timetable_df)
    
    st.session_state.generated = True
    st.session_state.locked = True
    st.success("Timetable generated and locked!")

# Button to Update Timetable
if st.session_state.generated and st.session_state.locked:
    st.header("Update Timetable")
    
    if st.button("Update Timetable"):
        # Only schedule newly added courses
        for course in st.session_state.courses:
            if course['course_code'] not in [c['course_code'] for c in st.session_state.courses]:
                schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
        
        timetable_data = get_timetable()
        timetable_df = pd.DataFrame(timetable_data)
        st.dataframe(timetable_df)
        st.success("Timetable updated successfully!")
