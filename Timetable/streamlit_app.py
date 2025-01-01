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
            # Check for 3 consecutive time slots availability
            for i in range(len(available_time_slots) - 2):  # Ensure 3 consecutive slots
                slot_1 = available_time_slots[i]
                slot_2 = available_time_slots[i + 1]
                slot_3 = available_time_slots[i + 2]

                # If slots are available, assign the 3-hour block
                st.session_state.timetable[day][course_code].append({
                    'time': f"{slot_1} - {slot_3}",
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
