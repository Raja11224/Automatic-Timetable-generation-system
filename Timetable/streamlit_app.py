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

def is_room_available(day, time_slot, room, course_code, section, course_type):
    """
    Check if a room is available for a specific course section at a given time.
    """
    for other_course_code in st.session_state.timetable[day]:
        for session in st.session_state.timetable[day].get(other_course_code, []):
            # Avoid conflicts for the same course section
            if other_course_code == course_code and session['section'] != section:
                if session['room'] == room and session['time'] == time_slot:
                    return False  # Room is already occupied at the time
            # Ensure no conflict with Lab and Theory courses for the same time
            if session['room'] == room and session['time'] == time_slot:
                return False  # Room is already occupied at the time
    return True  # Room is available

# Function to allocate a Lab course (2 consecutive 1.5-hour blocks on a single day)
def allocate_lab_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)  # Get an available room for the lab course
    if room:
        # Choose a random day for the lab (only one day)
        available_days = days_of_week.copy()
        random.shuffle(available_days)

        # Iterate over the shuffled days and try to assign the lab to one day
        for day in available_days:
            # Check for 2 consecutive time slots availability (1.5 hours each)
            for i in range(len(available_time_slots) - 1):  # Ensure 2 consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]

                # If the room is available, assign the 3-hour block
                if is_room_available(day, f"{slot_1} - {slot_2}", room, course_code, section, "Lab"):
                    st.session_state.timetable[day][course_code].append({
                        'time': f"{slot_1} - {slot_2}",
                        'room': room,
                        'section': section  # Add the section information
                    })
                    break  # Once scheduled, stop and break
            break  # Once scheduled, stop after assigning to one day

# Function to allocate Theory course (1.5-hour blocks on two different days)
def allocate_theory_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)  # Get an available room for the theory course
    if room:
        # Choose random days for the theory course (two different days)
        available_days = days_of_week.copy()
        random.shuffle(available_days)

        # Track how many slots we've assigned
        assigned_slots = 0
        for day in available_days:
            if assigned_slots >= 2:  # We can only assign two different days
                break

            # Try to find an available time slot for the first or second 1.5-hour block
            for i in range(len(available_time_slots)):
                slot_1 = available_time_slots[i]

                # Ensure no consecutive scheduling for Theory courses
                if is_room_available(day, slot_1, room, course_code, section, "Theory"):
                    st.session_state.timetable[day][course_code].append({
                        'time': slot_1,
                        'room': room,
                        'section': section  # Add the section information
                    })
                    assigned_slots += 1
                    break  # Once assigned to this day, move to the next day

        # Ensure the second 1.5-hour block is assigned to a different day
        if assigned_slots == 1:
            for day in available_days:
                if day not in st.session_state.timetable:
                    continue
                for i in range(len(available_time_slots)):
                    slot_2 = available_time_slots[i]

                    if is_room_available(day, slot_2, room, course_code, section, "Theory"):
                        st.session_state.timetable[day][course_code].append({
                            'time': slot_2,
                            'room': room,
                            'section': section  # Add the section information
                        })
                        break

# Function to schedule a course (Theory or Lab)
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    """
    Assign time and room to a course section based on the course type.
    """
    # Check if the course section has already been scheduled
    if any(course['course_code'] == course_code and course['section'] == section and 'scheduled' in course for course in st.session_state.courses):
        return  # Skip allocation if already scheduled

    # Proceed with scheduling the course section if not already scheduled
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
