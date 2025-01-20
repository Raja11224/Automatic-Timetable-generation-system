import streamlit as st
import pandas as pd
from collections import defaultdict
import random

# Initialize session state if not already initialized
if 'courses' not in st.session_state:
    st.session_state.courses = []

if 'rooms' not in st.session_state:
    st.session_state.rooms = []

if 'timetable' not in st.session_state:
    st.session_state.timetable = defaultdict(lambda: defaultdict(list))

if 'timetable_generated' not in st.session_state:
    st.session_state.timetable_generated = False

# Sample days of the week and time slots
days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]

# Function to add a course
def add_course(course_code, course_title, section, room_type, slot_preference):
    st.session_state.courses.append({
        'course_code': course_code,
        'course_title': course_title,
        'section': section,
        'room_type': room_type,
        'slot_preference': slot_preference
    })

# Function to read course information from an XLSX file
def read_courses_from_xlsx(uploaded_file):
    try:
        # Read the XLSX file using pandas
        df = pd.read_excel(uploaded_file)
        
        # Check if necessary columns exist
        required_columns = ['Course Code', 'Course Title', 'Section', 'Room Type', 'Slot Preference']
        if all(col in df.columns for col in required_columns):
            # Add the courses to session state
            for _, row in df.iterrows():
                add_course(row['Course Code'], row['Course Title'], row['Section'], row['Room Type'], row['Slot Preference'])
            st.success("Courses added successfully from the XLSX file!")
        else:
            st.error(f"The uploaded file is missing one or more of the required columns: {', '.join(required_columns)}")
    except Exception as e:
        st.error(f"Error reading the XLSX file: {str(e)}")

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

# Function to check if a room is available
def is_room_available(day, time_slot, room, course_code, section):
    for other_course_code in st.session_state.timetable[day]:
        for session in st.session_state.timetable[day].get(other_course_code, []):
            if other_course_code == course_code and session['section'] != section:
                if session['room'] == room and session['time'] == time_slot:
                    return False
            if session['room'] == room and session['time'] == time_slot:
                return False
    return True

# Function to display the timetable in a readable weekly format with improved styling
def display_timetable():
    timetable_data = []
    for day in days_of_week:
        for course_code, sessions in st.session_state.timetable[day].items():
            for session in sessions:
                timetable_data.append({
                    'Course Code': course_code,
                    'Course Title': next(course['course_title'] for course in st.session_state.courses if course['course_code'] == course_code),
                    'Day': day,
                    'Time': session['time'],
                    'Room': session['room'],
                    'Section': session['section']
                })
    
    # Display the timetable as a dataframe
    if timetable_data:
        timetable_df = pd.DataFrame(timetable_data)
        timetable_df = timetable_df[['Day', 'Course Code', 'Course Title', 'Section', 'Time', 'Room']]
        
        # Add styling to improve the visual appeal
        styled_df = timetable_df.style \
            .set_table_styles([{'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('font-weight', 'bold')]},
                               {'selector': 'tbody tr:nth-child(odd)', 'props': [('background-color', '#f2f2f2')]},
                               {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#ffffff')]},
                               {'selector': 'td', 'props': [('padding', '10px'), ('text-align', 'center')]},
                               {'selector': 'table', 'props': [('border-collapse', 'collapse'), ('width', '100%')]}]) \
            .hide(axis="index")
        
        st.dataframe(styled_df)
    else:
        st.warning("No timetable generated yet.")

def generate_timetable():
    """
    Try to generate the timetable by scheduling all the courses.
    """
    # Generate timetable for newly added courses and append them to the existing timetable
    for course in st.session_state.courses:
        room_type = course['room_type']
        section = course['section']
        course_code = course['course_code']
        course_title = course['course_title']
        
        if room_type == "Theory" or room_type == "Lab":  # This includes both PF and DLD courses
            if not allocate_course(course_code, course_title, section, room_type):
                st.warning(f"Scheduling failed for {course_code} Section {section}.")
                return

    st.session_state.timetable_generated = True  # Mark timetable as generated
    st.success("Timetable generated successfully!")
    display_timetable()

def allocate_course(course_code, course_title, section, room_type):
    """
    Allocate a course (Theory or Lab) to a time slot and room.
    """
    if room_type == "Lab":
        # Lab courses are scheduled once a week with two consecutive slots
        return allocate_lab_course(course_code, course_title, section)
    
    # For theory courses, select random days and slots
    available_time_slots = ["8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"]
    days = random.sample(days_of_week, 2)  # Pick 2 random days for the course
    selected_slots = random.sample(available_time_slots, 2)  # Pick 2 random slots from available slots
    
    assigned_days = []
    for i, day in enumerate(days):
        selected_slot = selected_slots[i]
        room = get_available_room(room_type)  # Get an available room for the course type
        
        # Ensure the room is available for the selected time
        if is_room_available(day, selected_slot, room, course_code, section):
            st.session_state.timetable[day][course_code].append({
                'time': selected_slot,
                'room': room,
                'section': section
            })
            assigned_days.append((day, selected_slot, room))
            st.info(f"Assigned {course_code} Section {section} to {day} at {selected_slot} in {room}.")
        else:
            st.warning(f"Could not assign {course_code} Section {section} to {day} at {selected_slot}. Retrying assignment.")
            # Try a different room or time slot
            retry_success = False
            for attempt in range(3):  # Try 3 times for conflict resolution
                retry_room = get_available_room(room_type)
                if is_room_available(day, selected_slot, retry_room, course_code, section):
                    st.info(f"Retrying: Assigned {course_code} Section {section} to {day} at {selected_slot} in {retry_room}.")
                    st.session_state.timetable[day][course_code].append({
                        'time': selected_slot,
                        'room': retry_room,
                        'section': section
                    })
                    assigned_days.append((day, selected_slot, retry_room))
                    retry_success = True
                    break
                else:
                    st.warning(f"Retry attempt {attempt+1}: Could not assign {course_code} Section {section} to {day} at {selected_slot}.")
            
            if not retry_success:
                st.error(f"Scheduling failed for {course_code} Section {section} after retries.")
                return False

    st.success(f"Course {course_code} successfully scheduled on {', '.join([f'{day} at {slot}' for day, slot, room in assigned_days])}.")
    return True

def allocate_lab_course(course_code, course_title, section):
    """
    Allocate a lab course to two consecutive time slots on the same day.
    """
    available_time_slots = [
        "8:00 - 9:30", "9:30 - 11:00", "11:00 - 12:30", 
        "12:30 - 2:00", "2:00 - 3:30", "3:30 - 5:00", "5:00 - 6:30"
    ]
    
    # Pick a random day for the lab course
    selected_day = random.choice(days_of_week)
    
    # Try to find two consecutive time slots on the selected day
    for i in range(len(available_time_slots) - 1):  # Loop through slots except the last one
        time_slot = available_time_slots[i]
        next_slot = available_time_slots[i + 1]  # The next consecutive slot
        
        # Get a lab room
        room = get_available_room("Lab")  # Lab rooms only
        
        # Ensure the room is available for both consecutive slots on the same day
        if is_room_available(selected_day, time_slot, room, course_code, section) and \
           is_room_available(selected_day, next_slot, room, course_code, section):
            
            # Check for conflicts with other courses (both theory and lab courses)
            for day, sessions in st.session_state.timetable.items():
                for course_key, course_sessions in sessions.items():
                    for session in course_sessions:
                        # Avoid conflict with any other course in the same room and time slot
                        if session['room'] == room and \
                           (session['time'] == time_slot or session['time'] == next_slot):
                            st.warning(f"Conflict: {course_key} is already scheduled in the same room during {time_slot} or {next_slot}. Retrying assignment.")
                            return False  # If there’s a conflict, stop and return false
            
            # Assign the lab course to the selected day and both consecutive slots
            st.session_state.timetable[selected_day][course_code].append({
                'time': f"{time_slot} and {next_slot}",
                'room': room,
                'section': section
            })
            
            st.info(f"Lab {course_code} Section {section} scheduled on {selected_day} at {time_slot} and {next_slot} in {room}.")
            return True
    
    # If no consecutive time slots are available, show a warning
    st.warning(f"Could not find consecutive time slots for Lab {course_code} Section {section} on {selected_day}.")
    return False

# Streamlit User Interface
st.title("UMT Timetable Generator")

# Section to upload the XLSX file with course information
st.header("Upload an XLSX File with Course Information")

uploaded_file = st.file_uploader("Choose an XLSX file", type="xlsx")

if uploaded_file is not None:
    read_courses_from_xlsx(uploaded_file)

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

# Buttons for Timetable Generation and Update
if st.session_state.courses:
    if not st.session_state.timetable_generated:
        if st.button("Generate Timetable"):
            generate_timetable()
    else:
        # Show update button once the timetable is generated
        if st.button("Update Timetable"):
            generate_timetable()  # Will only add new courses, not change existing timetable
        else:
            st.button("Generate Timetable", disabled=True)  # Disable after timetable generation
