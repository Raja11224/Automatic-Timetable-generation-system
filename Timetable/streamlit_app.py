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

# Streamlit UI
st.title("Course Timetable Generator")

# Section to add a new course (First Section)
st.header("Add a New Course")

# Check if the timetable is locked (already generated)
if st.session_state.locked:
    st.warning("Timetable is locked. New courses will be added without modifying the existing timetable.")

# Create the form and submit logic for adding new course
with st.form(key='add_course_form'):
    course_code = st.text_input("Course Code", value="")
    course_title = st.text_input("Course Title", value="")
    section = st.text_input("Section", value="")
    credit_hours = st.number_input("Credit Hours", min_value=1, max_value=5, value=1)
    teacher = st.text_input("Teacher", value="")
    
    submit_button = st.form_submit_button(label="Add Course")
    
    if submit_button:
        if course_code and course_title and section and teacher:
            st.session_state.courses.append({
                'course_code': course_code,
                'course_title': course_title,
                'section': section,
                'credit_hours': credit_hours,
                'teacher': teacher
            })
            st.success("Course added successfully!")
        else:
            st.error("Please fill all the fields.")

# Section to manage rooms (Add/Delete Room)

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
            st.error("Please provide a valid room name and type.")

# Delete Room Form
st.header("Delete a Room")

with st.form(key='delete_room_form'):
    if st.session_state.rooms:
        room_to_delete = st.selectbox("Select Room to Delete", list(st.session_state.rooms.keys()))
        delete_room_button = st.form_submit_button(label="Delete Room")
        
        if delete_room_button:
            if room_to_delete in st.session_state.rooms:
                del st.session_state.rooms[room_to_delete]
                st.success(f"Room {room_to_delete} deleted successfully.")
            else:
                st.warning("Room not found.")
    else:
        st.write("No rooms available to delete.")
        delete_room_button = st.form_submit_button(label="Delete Room")  # Still adding a submit button for consistency

# Function to get the available rooms (based on room type) and check for availability
def get_available_room(room_type):
    available_rooms = [room for room, rtype in st.session_state.rooms.items() if rtype == room_type]
    if not available_rooms:
        st.warning(f"No {room_type} rooms available.")
        return None
    return random.choice(available_rooms)

# Function to schedule courses based on credit hours and room type
def schedule_course(course_code, course_title, section, teacher, credit_hours):
    num_sessions = credit_hours
    time_slot_index = 0  # Start from the first time slot

    # Track scheduled times for each section
    section_schedule = defaultdict(list)

    if credit_hours == 1:
        # Lab course: 1 credit hour, schedule three consecutive hours in a Lab room
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Lab")  # Get a lab room

        for i in range(3):  # Schedule three hours
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            # Track section schedule to avoid conflicts
            section_schedule[section].append((day, time, room))
            
            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        time_slot_index = (time_slot_index + 3) % len(time_slots)

    elif credit_hours == 3:
        # 3 credit hours: schedule two 1.5 hour slots in a Theory room
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = get_available_room("Theory")  # Get a theory room

        for i in range(2):  # Schedule two 1.5 hour slots
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            # Track section schedule to avoid conflicts
            section_schedule[section].append((day, time, room))
            
            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        time_slot_index = (time_slot_index + 2) % len(time_slots)

    else:
        # For courses with more than 3 credit hours, schedule one slot at a time
        for _ in range(num_sessions):
            day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
            time = time_slots[time_slot_index]
            room = get_available_room("Theory")  # Get a theory room

            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            # Track section schedule to avoid conflicts
            section_schedule[section].append((day, time, room))
            
            st.session_state.timetable[day][course_code].append({
                'time': time,
                'room': room
            })

            time_slot_index = (time_slot_index + 1) % len(time_slots)

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

# Button to generate timetable
if st.button("Generate Timetable"):
    generate_timetable()
    timetable_data = get_timetable()
    if timetable_data:
        df = pd.DataFrame(timetable_data)
        st.dataframe(df)

# Function to generate timetable
def generate_timetable():
    if not st.session_state.generated:  # Only generate the timetable if it hasn't been generated already
        # Schedule the courses and generate the timetable
        for course in st.session_state.courses:
            if not any(st.session_state.timetable[day].get(course['course_code']) for day in st.session_state.timetable):
                schedule_course(course['course_code'], course['course_title'], course['section'], course['teacher'], course['credit_hours'])
        
        st.session_state.generated = True  # Mark the timetable as generated
        st.session_state.locked = True  # Lock the timetable from further changes

# Function to get timetable
def get_timetable():
    timetable_data = []
    for course in st.session_state.courses:
        course_times = {'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section'],
                        'Teacher': course['teacher']}
        
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            day_schedule = []
            for session in st.session_state.timetable[day].get(course['course_code'], []):
                day_schedule.append(f"{session['time']} (Room: {session['room']})")
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    return timetable_data

# Option to download timetable as Excel file
st.header("Download Timetable")

download_button = st.button("Download Timetable as Excel")

if download_button:
    timetable_data = get_timetable()
    if timetable_data:
        df = pd.DataFrame(timetable_data)
        output = BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        st.download_button(label="Download Excel", data=output, file_name="timetable.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.error("No timetable to download.")
