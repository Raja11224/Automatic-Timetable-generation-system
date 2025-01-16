m is available for both consecutive slots on the same day
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
