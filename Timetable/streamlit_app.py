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

# Function to get available room
def get_available_room(room_type):
    available_rooms = []
    for room in st.session_state.rooms:
        if room_type == room["type"]:
            available_rooms.append(room["name"])

    if available_rooms:
        return random.choice(available_rooms)
    else:
        st.warning(f"No available rooms for {room_type} type.")
        return None

# Function to allocate a 3-hour consecutive block (Lab)
def allocate_lab_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose a random day for the lab (only one day)
        available_days = days_of_week.copy()
        scheduled = any(course_code in st.session_state.timetable[day] for day in available_days)

        if scheduled:
            st.warning(f"Course {course_code} is already scheduled for the week. Skipping allocation.")
            return
        
        random.shuffle(available_days)  # Shuffle days to get a random choice

        # Iterate over the shuffled days and try to assign the lab to one day
        for day in available_days:
            # Check for 2 consecutive time slots availability (1.5 hour x 2)
            for i in range(len(available_time_slots) - 1):  # Ensure 2 consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]

                # If slots are available, assign the 3-hour block
                if not any(session['room'] == room and session['time'] == f"{slot_1} - {slot_2}" for session in st.session_state.timetable[day].get(course_code, [])):
                    st.session_state.timetable[day][course_code].append({
                        'time': f"{slot_1} - {slot_2}",
                        'room': room
                    })
                    break  # Once scheduled on one day, stop
            break  # Stop after assigning on one day

# Function to schedule a course (Theory or Lab)
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    # Check if the course has already been scheduled
    if any(course_code in st.session_state.timetable[day] for day in days_of_week):
        st.warning(f"Course {course_code} is already scheduled. Skipping allocation.")
        return

    # Proceed with scheduling the course if not already scheduled
    if room_type == "Theory" and slot_preference == "1.5 Hour blocks":
        allocate_theory_course(course_code, course_title, section, room_type)
    elif room_type == "Lab" and slot_preference == "3 Hour consecutive block":
        allocate_lab_course(course_code, course_title, section, room_type)

# Room Management Functions
def add_room(room_name, room_type):
    if not any(room["name"] == room_name for room in st.session_state.rooms):
        st.session_state.rooms.append({"name": room_name, "type": room_type})
        st.success(f"Room {room_name} added successfully!")
    else:
        st.warning(f"Room {room_name} already exists.")

def delete_room(room_name):
    if any(room["name"] == room_name for room in st.session_state.rooms):
        st.session_state.rooms = [room for room in st.session_state.rooms if room["name"] != room_name]
        st.success(f"Room {room_name} deleted successfully!")
    else:
        st.warning(f"Room {room_name} does not exist.")

# Set the app's title
st.title("Timetable Generator")

# Add Course Section
st.header("Add Course")

with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code (e.g., CS101)")
    course_title = st.text_input("Course Title (e.g., Computer Science 101)")
    section = st.text_input("Section (e.g., A)")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    slot_preference = st.selectbox("Slot Preference", ["1.5 Hour blocks", "3 Hour consecutive block"])
    add_course_button = st.form_submit_button(label="Add Course")
    
    if add_course_button:
        if course_code and course_title and section:
            add_course(course_code, course_title, section, room_type, slot_preference)
            st.success(f"Course {course_code} added successfully!")
        else:
            st.error("Please provide all course details.")

# Displaying Added Courses
st.subheader("Added Courses")
if st.session_state.courses:
    courses_data = [{
        'Course Code': course['course_code'],
        'Course Title': course['course_title'],
        'Section': course['section'],
        'Room Type': course['room_type'],
        'Slot Preference': course['slot_preference']
    } for course in st.session_state.courses]
    
    courses_df = pd.DataFrame(courses_data)
    st.dataframe(courses_df)

# Room Management Section
st.header("Room Management")

# Form to add a room
with st.form(key='add_room_form'):
    room_name = st.text_input("Room Name (e.g., Room 6)")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    add_room_button = st.form_submit_button(label="Add Room")
    
    if add_room_button:
        if room_name:
            add_room(room_name, room_type)
        else:
            st.error("Please provide a room name.")

# Form to delete a room
with st.form(key='delete_room_form'):
    room_to_delete = st.selectbox("Select Room to Delete", [room["name"] for room in st.session_state.rooms])
    delete_room_button = st.form_submit_button(label="Delete Room")
    
    if delete_room_button:
        if room_to_delete:
            delete_room(room_to_delete)
        else:
            st.warning("Please select a room to delete.")

# Timetable Section (Generate & Update)
if st.session_state.generated and st.session_state.locked:
    st.header("Update Timetable")
    if st.button("Update Timetable"):
        # Schedule only those courses that have not been scheduled already
        for course in st.session_state.courses:
            # Ensure the course is scheduled if not already done
            schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
        
        # Get the updated timetable and display it
        timetable_data = get_timetable()
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)
        st.success("Timetable updated successfully!")

# Generate Timetable Button (First time scheduling)
if not st.session_state.generated:
    st.header("Generate Timetable")
    if st.button("Generate Timetable"):
        # Generate timetable only if courses have been added
        if st.session_state.courses:
            for course in st.session_state.courses:
                schedule_course(course['course_code'], course['course_title'], course['section'], course['room_type'], course['slot_preference'])
            st.session_state.generated = True
            st.success("Timetable generated successfully!")
        else:
            st.warning("Please add some courses before generating the timetable.")
