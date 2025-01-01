import random
import streamlit as st
from collections import defaultdict
import pandas as pd

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
        
        for day in days_of_week:
            day_schedule = []
            for session in st.session_state.timetable[day].get(course['course_code'], []):
                day_schedule.append(f"{session['time']} (Room: {session['room']})")
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    return timetable_data

# Function to get available room
def get_available_room(room_type):
    available_rooms = [room for room in st.session_state.rooms if room["type"] == room_type]
    return random.choice(available_rooms) if available_rooms else None

# Function to check if the room is available for a particular day and time slot
def is_room_available(day, time_slot, room, course_code):
    for course in st.session_state.timetable[day].values():
        for session in course:
            if session['time'] == time_slot and session['room'] == room:
                return False  # Room is already occupied for this time slot
    return True  # Room is available

# Function to allocate Theory course (1.5-hour blocks on two different days)
def allocate_theory_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose random days for the theory course (two different days)
        available_days = days_of_week.copy()
        random.shuffle(available_days)

        assigned_slots = 0
        for day in available_days:
            if assigned_slots >= 2:  # Assign only on two different days
                break
            # Check for 1.5-hour time slot availability
            for i in range(len(available_time_slots)):
                slot_1 = available_time_slots[i]
                if is_room_available(day, slot_1, room, course_code):
                    st.session_state.timetable[day][course_code].append({
                        'time': slot_1,
                        'room': room
                    })
                    assigned_slots += 1
                    break  # Once assigned to this day, stop and go to the next day

# Function to allocate Lab course (two consecutive 1.5-hour blocks on the same day)
def allocate_lab_course(course_code, course_title, section, room_type):
    room = get_available_room(room_type)
    if room:
        # Choose a random day for the lab course (one day only)
        available_days = days_of_week.copy()
        random.shuffle(available_days)
        
        for day in available_days:
            # Check for 2 consecutive 1.5-hour time slots availability
            for i in range(len(available_time_slots) - 1):  # Ensure two consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]
                
                if is_room_available(day, slot_1, room, course_code) and is_room_available(day, slot_2, room, course_code):
                    # Assign the two consecutive time slots for the lab course
                    st.session_state.timetable[day][course_code].append({
                        'time': f"{slot_1} - {slot_2}",
                        'room': room
                    })
                    break  # Once scheduled on one day, stop
            break  # Stop after assigning on one day

# Function to schedule a course (Theory or Lab)
def schedule_course(course_code, course_title, section, room_type, slot_preference):
    # Check if the course has already been scheduled
    if course_code in st.session_state.timetable:
        st.warning(f"Course {course_code} is already scheduled. Skipping allocation.")
        return

    # Proceed with scheduling the course if not already scheduled
    if room_type == "Theory" and slot_preference == "1.5 Hour blocks":
        allocate_theory_course(course_code, course_title, section, room_type)
    elif room_type == "Lab" and slot_preference == "3 Hour consecutive block":
        allocate_lab_course(course_code, course_title, section, room_type)

# Section to update timetable (only allowed after generation and locked)
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

# Ensure the timetable isn't overwritten
if st.session_state.generated:
    st.warning("The timetable has already been generated. To make changes, please click 'Update Timetable'.")
    return

# Add Course Form
if st.button("Add Course"):
    course_code = st.text_input("Course Code")
    course_title = st.text_input("Course Title")
    section = st.text_input("Section")
    room_type = st.selectbox("Room Type", ["Theory", "Lab"])
    slot_preference = st.selectbox("Slot Preference", ["1.5 Hour blocks", "3 Hour consecutive block"])

    if course_code and course_title and section:
        add_course(course_code, course_title, section, room_type, slot_preference)
        st.success(f"Course {course_code} added successfully!")

# Display generated timetable
if st.session_state.generated:
    timetable_data = get_timetable()
    df = pd.DataFrame(timetable_data)
    st.dataframe(df)
