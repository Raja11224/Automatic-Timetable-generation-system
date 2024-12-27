from flask import Flask, render_template, request, redirect, send_file
from collections import defaultdict
import random
import pandas as pd
from io import BytesIO

app = Flask(__name__)

# Global storage for courses, timetable, and teachers
courses = []
timetable = defaultdict(lambda: defaultdict(list))  # Dictionary to hold the timetable for each day
teachers = []  # List to store unique teachers
generated = False  # Flag to track if timetable has been generated

# Sample rooms for simplicity
rooms = ["CB1-101", "CB1-102", "CB1-103", "CB1-104", "CB1-105", "CB1-106"]
time_slots = ["8:00-9:00", "9:00-10:00", "10:00-11:00", "11:00-12:00", "12:00-1:00"]

@app.route('/')
def index():
    return render_template('index.html', courses=courses, teachers=teachers, timetable=timetable, generated=generated)

@app.route('/add_course', methods=['POST'])
def add_course():
    course_code = request.form['course_code']
    course_title = request.form['course_title']
    section = request.form['section']
    credit_hours = int(request.form['credit_hours'])
    teacher = request.form['teacher']

    # Create the course entry
    course = {
        'course_code': course_code,
        'course_title': course_title,
        'section': section,
        'credit_hours': credit_hours,
        'teacher': teacher
    }

    # Add course to courses list
    courses.append(course)

    # Add teacher to teachers list if not already present
    if teacher not in teachers:
        teachers.append(teacher)

    global generated
    generated = False  # Reset the timetable when a new course is added

    return redirect('/')

@app.route('/assign_resource_person', methods=['POST'])
def assign_resource_person():
    course_code = request.form['course_code']  # Get the selected course code
    teacher = request.form['teacher']  # Get the selected teacher

    # Find the course and assign the resource person (teacher)
    for course in courses:
        if course['course_code'] == course_code:
            course['teacher'] = teacher  # Assign the new teacher to the course
            break
    
    return redirect('/')  # Redirect to the index page to see the updated course list

@app.route('/generate_timetable', methods=['POST'])
def generate_timetable():
    global timetable, generated
    if not generated:  # Only generate the timetable if it hasn't been generated already
        # Schedule the courses and generate the timetable, while preserving the old courses
        for course in courses:
            if not any(timetable[day].get(course['course_code']) for day in timetable):
                schedule_course(course['course_code'], course['course_title'], course['section'], course['teacher'], course['credit_hours'])

        generated = True  # Mark the timetable as generated
    
    return render_template('index.html', courses=courses, teachers=teachers, timetable=timetable, generated=generated)

@app.route('/download_excel')
def download_excel():
    # Prepare data for Excel
    data = []
    for course in courses:
        for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']:
            if course['course_code'] in timetable[day]:
                for session in timetable[day][course['course_code']]:
                    data.append({
                        'Course Code': course['course_code'],
                        'Course Title': course['course_title'],
                        'Section': course['section'],
                        'Credit Hours': course['credit_hours'],
                        'Teacher': course['teacher'],
                        'Day': day,
                        'Time': session['time'],
                        'Room': session['room']
                    })
    
    # Convert the data to a DataFrame
    df = pd.DataFrame(data)

    # Write the DataFrame to a BytesIO buffer
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Timetable')

    # Move buffer position to the beginning
    buffer.seek(0)

    # Return the Excel file as a download
    return send_file(buffer, as_attachment=True, download_name="timetable.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Function to schedule courses without modifying the existing timetable
def schedule_course(course_code, course_title, section, teacher, credit_hours):
    num_sessions = credit_hours
    time_slot_index = 0  # Start from the first time slot

    if credit_hours == 1:
        # Lab course: 1 credit hour, schedule three consecutive hours
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = random.choice(rooms)

        # Check if time slots are available for this day and course, and if the section doesn't have another course at the same time
        for i in range(3):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        # Update the time slot index (skip three slots)
        time_slot_index = (time_slot_index + 3) % len(time_slots)
    
    elif credit_hours == 2:
        # 2 credit hours: schedule both hours in the same room
        day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
        room = random.choice(rooms)

        # Check if both consecutive slots are available, and if the section doesn't have another course at the same time
        for i in range(2):
            time = time_slots[time_slot_index + i]
            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            timetable[day][course_code].append({
                'time': time,
                'room': room
            })
        
        # Update the time slot index (skip two slots)
        time_slot_index = (time_slot_index + 2) % len(time_slots)

    else:
        # For courses with more than 2 credit hours, we schedule one slot at a time
        for _ in range(num_sessions):
            day = random.choice(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'])
            time = time_slots[time_slot_index]
            room = random.choice(rooms)

            if not is_slot_available(day, time, room, section):
                return schedule_course(course_code, course_title, section, teacher, credit_hours)

            timetable[day][course_code].append({
                'time': time,
                'room': room
            })

            time_slot_index = (time_slot_index + 1) % len(time_slots)

# Check if a time slot is available for a course, considering the section's existing courses as well
def is_slot_available(day, time, room, section):
    for course_code in timetable[day]:
        for session in timetable[day][course_code]:
            # Check if the section already has a course scheduled at the same time
            if session['time'] == time and session['room'] == room and any(course['section'] == section for course in courses if course['course_code'] == course_code):
                return False  # Slot is already taken for the same section at the same time
    return True

if __name__ == '__main__':
    app.run(debug=True)
