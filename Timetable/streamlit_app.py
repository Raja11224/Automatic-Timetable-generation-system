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
        selected_room = random.choice(available_rooms)
        st.info(f"Room {selected_room} selected for {room_type} course.")
        return selected_room
    else:
        st.warning(f"No available rooms for {room_type} type.")
        return None


def is_room_available(day, time_slot, room, course_code, section):
    """
    Check if a room is available for a specific course section at a given time.
    """
    # Check if there's a conflict for the same course section
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


# Function to backtrack and allocate rooms and slots with room type and time slot conflict checks
def backtrack_schedule(courses, idx=0):
    if idx == len(courses):  # All courses have been scheduled
        return True
    
    course = courses[idx]
    room_type = course['room_type']
    section = course['section']
    
    # Get available rooms that match the course's room type (Theory or Lab)
    available_rooms = [room["name"] for room in st.session_state.rooms if room["type"] == room_type]
    
    if not available_rooms:
        return False  # No available rooms for this course type
    
    random.shuffle(available_rooms)
    room = available_rooms[0]  # Take the first available room (or try others if needed)

    # Try assigning time slots for this course
    available_days = days_of_week.copy()
    random.shuffle(available_days)

    for day in available_days:
        available_slots = available_time_slots.copy()
        random.shuffle(available_slots)

        for slot in available_slots:
            # Check if the room and time slot are available
            if is_room_available(day, slot, room, course['course_code'], section):
                # Assign this slot and room to the course
                st.session_state.timetable[day][course['course_code']].append({
                    'time': slot,
                    'room': room,
                    'section': section
                })

                # Move to the next course
                if backtrack_schedule(courses, idx + 1):
                    return True

                # If not successful, undo the assignment and try next
                st.session_state.timetable[day][course['course_code']].remove({
                    'time': slot,
                    'room': room,
                    'section': section
                })
        
    return False


# Function to schedule a course (Theory or Lab)
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    """
    Assign time and room to a course section based on the course type.
    """
    # Check if the course section has already been scheduled in the timetable
    if course_code in st.session_state.timetable:
        for scheduled_course in st.session_state.timetable[course_code]:
            if scheduled_course['section'] == section:
                st.warning(f"Course {course_code} ({section}) has already been scheduled.")
                return  # Skip allocation if already scheduled

    st.info(f"Scheduling Course {course_code} ({section})...")  # Debug log

    # Proceed with scheduling the course section if not already scheduled
    if room_type == "Theory" and slot_preference == "1.5 Hour blocks":
        allocate_theory_course(course_code, course_title, section, room_type)
    elif room_type == "Lab" and slot_preference == "3 Hour consecutive block":
        allocate_lab_course(course_code, course_title, section, room_type)

def generate_timetable():
    if backtrack_schedule(st.session_state.courses):
        st.success("Timetable generated successfully!")
    else:
        st.warning("Failed to generate timetable. Trying a different configuration.")

def update_timetable():
    # Retain previous timetable and only add the new courses
    if backtrack_schedule(st.session_state.courses[len(st.session_state.timetable):]):
        st.success("Timetable updated successfully!")
    else:
        st.warning("Failed to update timetable. Try a different configuration.")

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

# Buttons to Generate and Update Timetable
col1, col2 = st.columns(2)
with col1:
    if st.button("Generate Timetable"):
        generate_timetable()
        timetable_data = get_timetable()
        
        # Format the timetable to fit the screen better
        timetable_df = pd.DataFrame(timetable_data)
        st.dataframe(timetable_df, width=800, height=800)  # Increased size
        
        st.session_state.generated = True
        st.session_state.locked = True
        st.success("Timetable generated and locked!")

with col2:
    if st.button("Update Timetable"):
        update_timetable()
        timetable_data = get_timetable()
        
        # Format the timetable to fit the screen better
        timetable_df = pd.DataFrame(timetable_data)
        st.dataframe(timetable_df, width=1200, height=600)  # Increased size
        
        st.session_state.locked = True
        st.success("Timetable updated successfully!")
