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

# Function to check if a room is available at a specific time slot
def is_room_available(day, slot, room, course_code, section):
    # Check if the room is already booked at the given time slot and day
    for scheduled_course in st.session_state.timetable[day].get(course_code, []):
        if scheduled_course['time'] == slot and scheduled_course['room'] == room:
            # Room is already booked for this course at this time slot
            return False
    return True

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
            
            # If no sessions found for the day, mark as "Not scheduled"
            course_times[day] = ", ".join(day_schedule) if day_schedule else "Not scheduled"
        
        timetable_data.append(course_times)
    
    # Log timetable data for debugging
    st.write("Generated Timetable Data: ", timetable_data)  # Add this for debugging

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

# Function to generate timetable
def generate_timetable():
    if backtrack_schedule(st.session_state.courses):
        st.success("Timetable generated successfully!")
    else:
        st.warning("Failed to generate timetable. Trying a different configuration.")

# Function to update timetable by adding new courses
def update_timetable():
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
        
        # Debugging line to check the timetable data
        st.write("Timetable Data: ", timetable_data)

        if timetable_data:
            # Transpose the data so days are columns
            timetable_df = pd.DataFrame(timetable_data)
            
            # Log the shape of the DataFrame
            st.write("Timetable DataFrame shape: ", timetable_df.shape)

            timetable_df = timetable_df.set_index('Course Code').transpose()  # Set course code as index and transpose
            
            # Ensure columns match days_of_week length
            if timetable_df.shape[1] == len(days_of_week):
                timetable_df.columns = days_of_week
            else:
                st.warning(f"Mismatch in columns: Expected {len(days_of_week)}, but got {timetable_df.shape[1]}")
            
            st.dataframe(timetable_df, width=1200, height=800)  # Increase vertical height
        
            st.session_state.generated = True
            st.session_state.locked = True
            st.success("Timetable generated and locked!")

with col2:
    if st.button("Update Timetable"):
        update_timetable()
        timetable_data = get_timetable()
        
        if timetable_data:
            # Transpose the data
            timetable_df = pd.DataFrame(timetable_data)
            
            # Ensure columns match days_of_week length
            if timetable_df.shape[1] == len(days_of_week):
                timetable_df.columns = days_of_week
            else:
                st.warning(f"Mismatch in columns: Expected {len(days_of_week)}, but got {timetable_df.shape[1]}")
            
            st.dataframe(timetable_df, width=1200, height=800)  # Increase vertical height
