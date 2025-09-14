import cv2
import math
import time
import threading
from collections import deque
from flask import Flask, render_template, Response, jsonify, request, session
from mediapipe import solutions as mp_solutions

mp_pose = mp_solutions.pose
mp_drawing = mp_solutions.drawing_utils

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

    # --- JAB ---
    if lw.z < le.z and left_elb_angle > 145 and lw.z - le.z < -0.02 and (now - last_time["jab"]) > cooldown:
        last_time["jab"] = now
        return "[OK] Jab", (0, 200, 0)

    # --- CROSS ---
    if rw.z < re.z and right_elb_angle > 145 and rw.z - re.z < -0.02 and (now - last_time["cross"]) > cooldown:
        last_time["cross"] = now
        return "[OK] Cross", (0, 200, 0)

    # --- HOOK ---
    if ((60 < left_elb_angle < 120 and abs(ldx) > abs(ldy) * 1.5 and abs(ldx) > 0.02) or
        (60 < right_elb_angle < 120 and abs(rdx) > abs(rdy) * 1.5 and abs(rdx) > 0.02)) \
        and (now - last_time["hook"]) > cooldown:
        last_time["hook"] = now
        return "[OK] Hook", (0, 200, 0)

    # --- UPPERCUT (stricter to avoid false triggers) ---
    if ((left_elb_angle < 110 and lw.y > landmarks[mp_pose.PoseLandmark.NOSE.value].y
         and -ldy > abs(ldx) * 2 and -ldy > 0.05) or
        (right_elb_angle < 110 and rw.y > landmarks[mp_pose.PoseLandmark.NOSE.value].y
         and -rdy > abs(rdx) * 2 and -rdy > 0.05)) \
        and (now - last_time["upper"]) > cooldown:
        last_time["upper"] = now
        return "[OK] Uppercut", (0, 200, 0)

    return None

# ---------------- DEBUG MOTION VECTORS ----------------
def draw_motion_vectors(img, lw_buf, rw_buf):
    h, w, _ = img.shape
    if len(lw_buf) >= 2:
        (x1, y1), (x2, y2) = lw_buf[-2], lw_buf[-1]
        cv2.arrowedLine(img, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (0, 255, 0), 2)
    if len(rw_buf) >= 2:
        (x1, y1), (x2, y2) = rw_buf[-2], rw_buf[-1]
        cv2.arrowedLine(img, (int(x1 * w), int(y1 * h)), (int(x2 * w), int(y2 * h)), (255, 0, 0), 2)

# ---------------- POSE PROCESSOR CLASS ----------------
class PoseProcessor:
    def __init__(self, session_id=None):
        self.session_id = session_id or str(time.time())
        self.pose = mp_pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.lw_buf = deque(maxlen=5)
        self.rw_buf = deque(maxlen=5)
        self.last_punch = None
        self.last_time = 0
        self.display_time = 1.0
        self.cooldowns = {"jab": 0, "cross": 0, "hook": 0, "upper": 0}

        # Stats
        self.total_punches = 0
        self.valid_punches = 0
        self.guard_warnings = 0
        self.punch_counts = {"Jab": 0, "Cross": 0, "Hook": 0, "Uppercut": 0}
        self.session_start = time.time()

        # State
        self.guard_ok_prev = True
        self.last_counted_punch = None
        self.last_count_time = 0.0
        self.count_cooldown = 0.5
        self.feedback_text = "Starting up..."
        self.feedback_color = (255, 255, 255)
        self.guard_up_time = 0
        self.total_tracking_time = 0
        self.last_update_time = time.time()
        
        # Thread safety
        self.lock = threading.Lock()
        # Add these lines to your PoseProcessor __init__ method:
        self.guard_up_time = 0
        self.total_tracking_time = 0
        self.last_update_time = time.time()

    def _extract_name(self, msg_text):
        return msg_text.partition('] ')[2] if '] ' in msg_text else msg_text
    def update_guard_time(self, guard_ok):
        now = time.time()
        time_elapsed = now - self.last_update_time
        self.total_tracking_time += time_elapsed
        
        if guard_ok:
            self.guard_up_time += time_elapsed
        
        self.last_update_time = now

    def process_frame(self, frame):
        img = frame
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
            
            self.update_guard_time(guard_ok)

            if not guard_ok and self.guard_ok_prev:
                with self.lock:
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
                        with self.lock:
                            self.total_punches += 1
                            self.valid_punches += 1
                            if name in self.punch_counts:
                                self.punch_counts[name] += 1
                            self.last_counted_punch = name
                            self.last_count_time = now

                if self.last_punch and (time.time() - self.last_time < self.display_time):
                    feedback.append(self.last_punch)

            draw_motion_vectors(img, self.lw_buf, self.rw_buf)
            
            # Update feedback text for display
            if feedback:
                self.feedback_text, self.feedback_color = feedback[-1]
            else:
                self.feedback_text = "Ready for training"
                self.feedback_color = (255, 255, 255)
                
            # Draw feedback on frame
            y_offset = 30
            for msg, color in feedback:
                cv2.putText(img, msg, (10, y_offset), cv2.FONT_HERSHEY_DUPLEX,
                            0.7, color, 2, cv2.LINE_AA)
                y_offset += 30

        return img

    def get_stats(self):
        with self.lock:
            acc = (self.valid_punches / self.total_punches * 100) if self.total_punches else 0
            session_duration = time.time() - self.session_start
            guard_perfection = (self.guard_up_time / self.total_tracking_time * 100) if self.total_tracking_time > 0 else 0
            return {
                "total_punches": self.total_punches,
                "valid_punches": self.valid_punches,
                "accuracy": round(acc, 1),
                "guard_warnings": self.guard_warnings,
                "guard_perfection": round(guard_perfection, 1),
                "punch_counts": self.punch_counts,
                "session_duration": round(session_duration, 1),
                "punches_per_minute": round(self.total_punches / (session_duration / 60), 1) if session_duration > 0 else 0
            }
    
    def reset_stats(self):
        with self.lock:
            self.total_punches = 0
            self.valid_punches = 0
            self.guard_warnings = 0
            self.punch_counts = {"Jab": 0, "Cross": 0, "Hook": 0, "Uppercut": 0}
            self.session_start = time.time()
            return {"status": "success", "message": "Stats reset successfully"}

# ---------------- FLASK APP ----------------
app = Flask(__name__)
app.secret_key = 'smartspar-secret-key-2023'

# Session management
processors = {}

def get_processor(session_id):
    if session_id not in processors:
        processors[session_id] = PoseProcessor(session_id)
    return processors[session_id]

def generate_frames(session_id):
    processor = get_processor(session_id)
    
    # Try different camera indices if 0 doesn't work
    camera_indices = [0, 1, 2]
    camera = None
    
    for camera_index in camera_indices:
        try:
            camera = cv2.VideoCapture(camera_index)
            if camera.isOpened():
                print(f"Camera found at index {camera_index}")
                break
            else:
                camera.release()
        except:
            pass
    
    if camera is None or not camera.isOpened():
        print("No camera found. Using test pattern.")
        # Create a test pattern if no camera is available
        while True:
            # Create a simple test pattern
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(img, "No camera detected", (100, 200), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(img, "Please check your camera connection", (50, 250), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', img)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)
    
    try:
        while True:
            success, frame = camera.read()
            if not success:
                break
            else:
                # Process the frame
                processed_frame = processor.process_frame(frame)
                
                # Encode the frame
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                
                # Yield the frame in byte format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        if camera:
            camera.release()

@app.route('/')
def index():
    session_id = session.get('session_id')
    if not session_id:
        session_id = str(time.time())
        session['session_id'] = session_id
    
    return render_template('index.html', session_id=session_id)

@app.route('/video_feed')
def video_feed():
    session_id = session.get('session_id', 'default')
    return Response(generate_frames(session_id), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    session_id = session.get('session_id', 'default')
    processor = get_processor(session_id)
    stats_data = processor.get_stats()
    return jsonify(stats_data)

@app.route('/end_session')
def end_session():
    session_id = session.get('session_id', 'default')
    processor = get_processor(session_id)
    stats_data = processor.get_stats()
    processor.reset_stats()
    return render_template('stats.html', stats=stats_data)

@app.route('/reset_stats')
def reset_stats():
    session_id = session.get('session_id', 'default')
    processor = get_processor(session_id)
    result = processor.reset_stats()
    return jsonify(result)

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5000,debug=True)