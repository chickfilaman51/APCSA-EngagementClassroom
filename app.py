#NOTE: The login portal for the teacher CURRENTLY does not have an actual authentication system or platform, it simply uses the "test" for both username and password. This is to ensure the core funcationality can be shown and tested.

import streamlit as st
import cv2
import time
import matplotlib.pyplot as plt
import uuid
from tracker import process_frame
import io

st.set_page_config(layout="centered", page_title="Engagement Tracker")

for key, default in {
    "mode": "landing",
    "engagement_log": [],
    "timestamps": [],
    "start_time": None,
    "running": False,
    "authenticated": False,
    "session_code": None,
    "teacher_data": {}
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


def go_student_mode():
    st.session_state.mode = "student_code"

def go_teacher_login():
    st.session_state.mode = "teacher_login"

def login():
    if st.session_state.username == "test" and st.session_state.password == "test":
        st.session_state.authenticated = True
        st.session_state.mode = "teacher_dashboard"
        st.session_state.login_error = False
    else:
        st.session_state.login_error = True

def logout():
    st.session_state.authenticated = False
    st.session_state.session_code = None
    st.session_state.mode = "landing"

def back_to_login():
    st.session_state.mode = "teacher_login"

def generate_session_code():

    code = str(uuid.uuid4()).split("-")[0].upper()
    st.session_state.session_code = code


    if code not in st.session_state.teacher_data:
        st.session_state.teacher_data[code] = []


def start_tracking():
    code_input = st.session_state.session_code_input.strip().upper()
    name_input = st.session_state.student_name_input.strip()

    if not code_input:
        st.session_state.start_error = "Please enter a session code"
    elif not name_input:
        st.session_state.start_error = "Please enter your name"
    elif code_input not in st.session_state.teacher_data:
        st.session_state.start_error = "Invalid session code. Please get the code from your teacher."
    else:
        st.session_state.current_session_code = code_input
        st.session_state.current_student_name = name_input
        st.session_state.mode = "student"
        st.session_state.start_error = ""


def go_back_to_landing():
    st.session_state.mode = "landing"
    st.session_state.engagement_log = []
    st.session_state.timestamps = []
    st.session_state.current_session_code = None
    st.session_state.current_student_name = None


if st.session_state.mode == "landing":
    st.markdown("<h1 style='text-align: center;'>📈 Engagement Tracker</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image("title.png", width=400)

    with col2:
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'>Welcome to the engagement tracker, the first ever platform to track student engagement in a virtual classroom!</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; margin-bottom: 20px;'>If you are a teacher, please install this software on your student's devices and get it set up. Please also generate a session code so you can get class started!</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; margin-bottom: 60px;'>If you are a student, simply enter your teacher's session code into the box, and simply click the toggle once class is done!</div>", unsafe_allow_html=True)
        st.button("Student Session", use_container_width=True, on_click=go_student_mode)
        st.button("Teacher Login", use_container_width=True, on_click=go_teacher_login)

elif st.session_state.mode == "teacher_login":
    st.title("Teacher Login")
    st.text_input("Username", key="username")
    st.text_input("Password", type="password", key="password")
    st.button("Login", on_click=login)
    if st.session_state.get("login_error"):
        st.error("Invalid username or password")

elif st.session_state.mode == "teacher_dashboard":
    if not st.session_state.authenticated:
        st.error("Please login first.")
        st.button("Back to login", on_click=back_to_login)
    else:
        st.title("Teacher Dashboard")
        st.button("Generate Unique Session Code", on_click=generate_session_code)
        if st.session_state.session_code:
            st.success(f"Session Code: {st.session_state.session_code}")

        st.markdown("### Collected Student Engagement Data")
        

        for code, records in st.session_state.teacher_data.items():
            st.markdown(f"**Session Code: {code}**")
            for r in records:
                st.markdown(f"- Student: {r['name']}, Data points: {len(r['timestamps'])}")

                
                fig, ax = plt.subplots()
                ax.plot(r['timestamps'], r['engagement_log'], marker='o', color='blue')
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Engagement Score")
                ax.set_title(f"Engagement for {r['name']}")
                ax.grid(True)

                st.pyplot(fig)


                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                buf.seek(0)


                st.download_button(
                    label=f"Download {r['name']}'s Engagement Graph",
                    data=buf,
                    file_name=f"{r['name']}_{code}_engagement.png",
                    mime="image/png"
                )


        st.button("Logout", on_click=logout)

elif st.session_state.mode == "student_code":
    st.title("Enter Session Info")
    st.text_input("Enter Session Code", key="session_code_input")
    st.text_input("Enter Your Name", key="student_name_input")
    st.button("Start Tracking", on_click=start_tracking)
    if st.session_state.get("start_error"):
        st.error(st.session_state.start_error)

elif st.session_state.mode == "student":
    st.title(f"Engagement Tracking for {st.session_state.current_student_name}")
    st.markdown(f"Session Code: {st.session_state.current_session_code}")

    tracking_toggle = st.toggle("Start Engagement Tracking", value=st.session_state.running)
    st.session_state.running = tracking_toggle

    frame_placeholder = st.empty()

    if tracking_toggle:
        if st.session_state.start_time is None:
            st.session_state.start_time = time.time()
            st.session_state.engagement_log = []
            st.session_state.timestamps = []

        cap = cv2.VideoCapture(0)
        st.warning("Tracking started. Toggle OFF to stop and see graph.")

        while st.session_state.running:
            ret, frame = cap.read()
            if not ret:
                st.error("Camera error")
                break

            frame = cv2.flip(frame, 1)
            status, score = process_frame(frame)

            cv2.putText(frame, f"Status: {status}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (0, 255, 0), 2)
            cv2.putText(frame, f"Score: {score}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (0, 255, 0), 2)

            elapsed = round(time.time() - st.session_state.start_time, 2)
            st.session_state.engagement_log.append(score)
            st.session_state.timestamps.append(elapsed)

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB")

            if not st.session_state.running:
                break

        cap.release()
        cv2.destroyAllWindows()
        st.session_state.start_time = None

    if not st.session_state.running and st.session_state.timestamps:
        st.success("Tracking stopped. See engagement graph below.")
        st.subheader("Engagement Over Time")

        fig, ax = plt.subplots()
        ax.plot(st.session_state.timestamps, st.session_state.engagement_log,
                marker='o', color='blue')
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Engagement Score")
        ax.set_title("Engagement Level Over Time")
        ax.grid(True)
        st.pyplot(fig)


        data_to_save = {
            "name": st.session_state.current_student_name,
            "timestamps": st.session_state.timestamps.copy(),
            "engagement_log": st.session_state.engagement_log.copy()
        }

        code = st.session_state.current_session_code
        if code not in st.session_state.teacher_data:
            st.session_state.teacher_data[code] = []
        

        if not any(r["name"] == data_to_save["name"] for r in st.session_state.teacher_data[code]):
            st.session_state.teacher_data[code].append(data_to_save)


        st.markdown("### Your engagement data has been sent to your teacher. Thank you!")
        st.button("Back to Main Screen", on_click=go_back_to_landing)
