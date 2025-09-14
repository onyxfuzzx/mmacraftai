import cv2
import av
import math
import time
from collections import deque
import mediapipe as mp
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration, WebRtcMode
import plotly.express as px

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

# ---------------- HELPERS ----------------
def angle(a, b, c):
    ang = math.degrees(
        math.atan2(c.y - b.y, c.x - b.x) -
        math.atan2(a.y - b.y, a.x - b.x)
    )
    ang = abs(ang)
    return 360 - ang if ang > 180 else ang

def avg_motion(buf):
    if len(buf) < 2:
        return 0, 0
    dx, dy = 0, 0
    for i in range(1, len(buf)):
        px, py = buf[i - 1]
        cx, cy = buf[i]
        dx += cx - px
        dy += cy - py
    return dx / (len(buf) - 1), dy / (len(buf) - 1)

# ---------------- RULES ----------------
def check_guard_up(landmarks):
    lw_y = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y
    rw_y = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y
    chin_y = (landmarks[mp_pose.PoseLandmark.MOUTH_LEFT.value].y +
              landmarks[mp_pose.PoseLandmark.MOUTH_RIGHT.value].y) / 2
    guard_threshold = chin_y + 0.15
    if lw_y < guard_threshold and rw_y < guard_threshold:
        return True, ("[OK] Guard", (0, 200, 0))
    else:
        return False, ("[!] Guard Down", (0, 0, 255))

def detect_punch_type(landmarks, lw_buf, rw_buf, last_time, cooldown=0.4):
    lw = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
    rw = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
    le = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value]
    re = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value]
    ls = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    rs = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

    now = time.time()
    left_elb_angle = angle(ls, le, lw)
    right_elb_angle = angle(rs, re, rw)
    ldx, ldy = avg_motion(lw_buf)
    rdx, rdy = avg_motion(rw_buf)

    # Jab
    if lw.z < le.z and left_elb_angle > 145 and lw.z - le.z < -0.02 and (now - last_time["jab"]) > cooldown:
        last_time["jab"] = now
        return "[OK] Jab", (0, 200, 0)

    # Cross
    if rw.z < re.z and right_elb_angle > 145 and rw.z - re.z < -0.02 and (now - last_time["cross"]) > cooldown:
        last_time["cross"] = now
        return "[OK] Cross", (0, 200, 0)

    # Hook
    if ((60 < left_elb_angle < 120 and abs(ldx) > abs(ldy) * 1.5 and abs(ldx) > 0.02) or
        (60 < right_elb_angle < 120 and abs(rdx) > abs(rdy) * 1.5 and abs(rdx) > 0.02)) \
        and (now - last_time["hook"]) > cooldown:
        last_time["hook"] = now
        return "[OK] Hook", (0, 200, 0)

    # Uppercut (stricter)
    if ((left_elb_angle < 110 and lw.y > landmarks[mp_pose.PoseLandmark.NOSE.value].y
         and -ldy > abs(ldx) * 2 and -ldy > 0.05) or
        (right_elb_angle < 110 and rw.y > landmarks[mp_pose.PoseLandmark.NOSE.value].y
         and -rdy > abs(rdx) * 2 and -rdy > 0.05)) \
        and (now - last_time["upper"]) > cooldown:
        last_time["upper"] = now
        return "[OK] Uppercut", (0, 200, 0)

    return None

# ---------------- VIDEO PROCESSOR ----------------
class PoseProcessor(VideoProcessorBase):
    def __init__(self):
        self.pose = mp_pose.Pose(min_detection_confidence=0.3,
                                 min_tracking_confidence=0.3)
        self.lw_buf = deque(maxlen=3)
        self.rw_buf = deque(maxlen=3)
        self.last_punch = None
        self.last_time = 0
        self.display_time = 1.0
        self.cooldowns = {"jab": 0, "cross": 0, "hook": 0, "upper": 0}

        # Stats
        self.total_punches = 0
        self.valid_punches = 0
        self.guard_warnings = 0
        self.punch_counts = {"Jab": 0, "Cross": 0, "Hook": 0, "Uppercut": 0}

        # State
        self.guard_ok_prev = True
        self.last_counted_punch = None
        self.last_count_time = 0.0
        self.count_cooldown = 0.5

    def _extract_name(self, msg_text):
        return msg_text.partition('] ')[2] if '] ' in msg_text else msg_text

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = self.pose.process(img_rgb)
        feedback = []

        if results.pose_landmarks:
            mp_drawing.draw_landmarks(img, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            lw = results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST]
            rw = results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST]
            self.lw_buf.append((lw.x, lw.y))
            self.rw_buf.append((rw.x, rw.y))

            guard_ok, guard_msg = check_guard_up(results.pose_landmarks.landmark)
            feedback.append(guard_msg)

            if not guard_ok and self.guard_ok_prev:
                self.guard_warnings += 1
            self.guard_ok_prev = guard_ok

            if guard_ok:
                punch = detect_punch_type(results.pose_landmarks.landmark,
                                          self.lw_buf, self.rw_buf,
                                          self.cooldowns, cooldown=0.4)
                now = time.time()
                if punch:
                    msg_text, color = punch
                    name = self._extract_name(msg_text)

                    self.last_punch = punch
                    self.last_time = now

                    if (now - self.last_count_time) > self.count_cooldown or name != self.last_counted_punch:
                        self.total_punches += 1
                        self.valid_punches += 1
                        if name in self.punch_counts:
                            self.punch_counts[name] += 1
                        self.last_counted_punch = name
                        self.last_count_time = now

                if self.last_punch and (time.time() - self.last_time < self.display_time):
                    feedback.append(self.last_punch)

            y_offset = 30
            for msg, color in feedback:
                cv2.putText(img, msg, (10, y_offset), cv2.FONT_HERSHEY_DUPLEX,
                            0.7, color, 2, cv2.LINE_AA)
                y_offset += 30

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# ---------------- STREAMLIT APP ----------------

st.set_page_config(page_title="SmartSpar", layout="wide")

# Inject Custom CSS
st.markdown("""
    <style>
    /* Global background */
    html, body, [class*="css"] {
        background-color: #000000 !important;  /* Black background */
        color: #ffffff !important;  /* White text */
        font-family: "Helvetica", "Arial", sans-serif !important; /* Minimal font */
    }

    /* Titles */
    h1, h2, h3 {
        text-align: center !important;
        color: #ff0000 !important;  /* Bright red */
        font-weight: 600 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #111111 !important;
        color: #ffffff !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ff0000 !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background-color: #000000 !important;
        border: 1px solid #ff0000 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        text-align: center !important;
    }
    [data-testid="stMetric"] label {
        color: #bbbbbb !important;
        font-size: 14px !important;
        font-weight: 400 !important;
    }
    [data-testid="stMetric"] div {
        color: #ffffff !important;
        font-size: 20px !important;
        font-weight: 600 !important;
    }

    /* Buttons */
    .stButton>button {
        background-color: #ff0000 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #cc0000 !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚡ SmartSpar - MMA AI Trainer")
st.sidebar.write("Real-time feedback + session stats")

# Main Title
st.title("🥊 SmartSpar - Rule-Based MMA Feedback")

# Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎥 Live Feed")
    ctx = webrtc_streamer(
        key="pose-detection",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTCConfiguration(
            {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
        ),
        video_processor_factory=PoseProcessor,
        media_stream_constraints={"video": True, "audio": False},
    )

with col2:
    st.subheader("📊 Live Counters")
    if ctx and ctx.video_processor:
        proc = ctx.video_processor
        st.metric("Total Punches", proc.total_punches)
        acc = (proc.valid_punches / proc.total_punches * 100) if proc.total_punches else 0
        st.metric("Accuracy %", f"{acc:.1f}%")
        st.metric("Guard Warnings", proc.guard_warnings)

        st.markdown("### 🥊 Punch Breakdown")
        for k, v in proc.punch_counts.items():
            st.write(f"- {k}: {v}")

# End Session
st.markdown("---")
if st.button("🏁 End Session"):
    if ctx and ctx.video_processor:
        proc = ctx.video_processor
        st.subheader("📊 Final Session Report")
        st.metric("Total Punches", proc.total_punches)
        st.metric("Valid Punches", proc.valid_punches)
        st.metric("Guard Warnings", proc.guard_warnings)
        acc = (proc.valid_punches / proc.total_punches * 100) if proc.total_punches else 0
        st.metric("Accuracy %", f"{acc:.1f}%")

        # Chart with theme
        fig = px.bar(
            x=list(proc.punch_counts.keys()),
            y=list(proc.punch_counts.values()),
            color=list(proc.punch_counts.keys()),
            title="Punch Breakdown",
            labels={"x": "Punch Type", "y": "Count"}
        )
        fig.update_layout(
            plot_bgcolor="#000000",
            paper_bgcolor="#000000",
            font=dict(color="white"),
            title_font=dict(color="#e60000", size=20),
            xaxis=dict(color="white"),
            yaxis=dict(color="white")
        )
        st.plotly_chart(fig, use_container_width=True)

        # Reset stats
        proc.total_punches = 0
        proc.valid_punches = 0
        proc.guard_warnings = 0
        proc.punch_counts = {"Jab": 0, "Cross": 0, "Hook": 0, "Uppercut": 0}
        st.success("✅ Session ended and stats reset. Ready for a new session.")
    else:
        st.warning("⚠️ No active session found. Please start sparring first.")
