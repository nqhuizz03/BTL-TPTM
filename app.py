from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Response, jsonify
from ultralytics import YOLO
import os
import cv2
import pandas as pd
import csv
from datetime import datetime
import json
from werkzeug.utils import secure_filename
import time

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
LOG_FILE = 'logs/violations.csv'
LOG_IMG_FOLDER = 'logs/images'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(LOG_IMG_FOLDER, exist_ok=True)
os.makedirs('logs', exist_ok=True)

model = YOLO('best.pt')  # Thay bằng đường dẫn tới mô hình đã huấn luyện

latest_stats = {'with_helmet': 0, 'no_helmet': 0}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    f = request.files.get('file')
    if not f:
        return 'No file uploaded', 400

    filename = secure_filename(f.filename)
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    f.save(input_path)

    if filename.lower().endswith('.mp4'):
        output_filename = 'result_' + os.path.splitext(filename)[0] + '.mp4'
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        process_video(input_path, output_path)
        return render_template('video.html', filename=output_filename)
    else:
        output_filename = 'result_' + filename
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        process_image(input_path, output_path)
        return redirect(url_for('serve_image', filename=output_filename))

@app.route('/image/<filename>')
def serve_image(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/video/<filename>')
def serve_video(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route('/stream')
def stream():
    return render_template('stream.html')

@app.route('/video_feed')
def video_feed():
    ESP32_CAM_URL = "http://172.16.67.98:81/stream"  # Cập nhật IP nếu cần

    def generate():
        global latest_stats
        cap = cv2.VideoCapture(ESP32_CAM_URL)
        if not cap.isOpened():
            print("Không thể mở stream ESP32-CAM")
            return

        while True:
            success, frame = cap.read()
            if not success or frame is None:
                continue

            results = model(frame)[0]
            boxes = results.boxes

            count_with_helmet = sum(int(cls_id) == 0 for cls_id in boxes.cls) if boxes else 0
            count_without_helmet = sum(int(cls_id) == 1 for cls_id in boxes.cls) if boxes else 0
            total_people = count_with_helmet + count_without_helmet

            frame_annotated = results.plot()
            text = f'Tổng: {total_people} (Đội mũ: {count_with_helmet}, Không đội mũ: {count_without_helmet})'
            cv2.putText(frame_annotated, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            log_violations(results, frame)

            _, jpeg = cv2.imencode('.jpg', frame_annotated)
            frame_bytes = jpeg.tobytes()

            latest_stats['with_helmet'] = count_with_helmet
            latest_stats['no_helmet'] = count_without_helmet

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stats')
def stats():
    if not os.path.exists(LOG_FILE):
        labels, values = [], []
    else:
        try:
            df = pd.read_csv(LOG_FILE)
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
            df['date'] = df['time'].dt.date
            grouped = df.groupby('date').size()
            labels = [str(x) for x in grouped.index]
            values = grouped.values.tolist()
        except Exception as e:
            print("Lỗi đọc file CSV:", e)
            labels, values = [], []

    return render_template('stats.html', labels=labels, values=values)

@app.route('/stats_json')
def stats_json():
    if not os.path.exists(LOG_FILE):
        return jsonify({'labels': [], 'with_helmet': [], 'no_helmet': []})
    try:
        df = pd.read_csv(LOG_FILE)
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
        df = df.dropna(subset=['time'])
        df['date'] = df['time'].dt.date
        grouped = df.groupby(['date', 'violation']).size().unstack(fill_value=0)
        grouped = grouped.reindex(columns=['With Helmet', 'No Helmet'], fill_value=0)
        labels = [str(x) for x in grouped.index]
        return jsonify({
            'labels': labels,
            'with_helmet': grouped['With Helmet'].tolist(),
            'no_helmet': grouped['No Helmet'].tolist()
        })
    except Exception as e:
        print("Lỗi đọc file CSV trong stats_json:", e)
        return jsonify({'labels': [], 'with_helmet': [], 'no_helmet': []})

@app.route('/stats_stream')
def stats_stream():
    def get_realtime_stats():
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        violations = []
        try:
            if os.path.exists(LOG_FILE):
                df = pd.read_csv(LOG_FILE)
                last_rows = df.tail(10)
                for _, row in last_rows.iterrows():
                    violations.append(f"[{row['time']}] {row['violation']}")
        except Exception as e:
            print("Lỗi đọc file CSV trong stats_stream:", e)

        return {
            'time': now,
            'with_helmet': latest_stats.get('with_helmet', 0),
            'no_helmet': latest_stats.get('no_helmet', 0),
            'violation_list': violations
        }

    def event_stream():
        while True:
            data = get_realtime_stats()
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)

    return Response(event_stream(), mimetype="text/event-stream")

def process_image(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        print(f"Không đọc được ảnh: {input_path}")
        return
    results = model(img)[0]
    boxes = results.boxes

    count_with_helmet = sum(int(cls_id) == 0 for cls_id in boxes.cls) if boxes else 0
    count_without_helmet = sum(int(cls_id) == 1 for cls_id in boxes.cls) if boxes else 0
    total_people = count_with_helmet + count_without_helmet

    img_annotated = results.plot()
    text = f'Tổng: {total_people} (Đội mũ: {count_with_helmet}, Không đội mũ: {count_without_helmet})'
    cv2.putText(img_annotated, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    log_violations(results, frame=img)
    cv2.imwrite(output_path, img_annotated)

def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Không mở được video: {input_path}")
        return
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    fourcc = cv2.VideoWriter_fourcc(*'avc1')

    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break

        results = model(frame)[0]
        boxes = results.boxes

        count_with_helmet = sum(int(cls_id) == 0 for cls_id in boxes.cls) if boxes else 0
        count_without_helmet = sum(int(cls_id) == 1 for cls_id in boxes.cls) if boxes else 0
        total_people = count_with_helmet + count_without_helmet

        annotated = results.plot()
        text = f'Tổng: {total_people} (Đội mũ: {count_with_helmet}, Không đội mũ: {count_without_helmet})'
        cv2.putText(annotated, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        log_violations(results, frame=frame)

        if annotated.shape[1] != w or annotated.shape[0] != h:
            annotated = cv2.resize(annotated, (w, h))

        out.write(annotated)
        frame_count += 1

    cap.release()
    out.release()

def log_violations(results, frame=None):
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['time', 'violation', 'image'])

    now = datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M:%S')
    boxes = results.boxes

    if boxes is None:
        return

    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for box in boxes:
            cls_id = int(box.cls)
            if cls_id in [0, 1]:
                label = 'With Helmet' if cls_id == 0 else 'No Helmet'
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                img_name = ''
                if frame is not None:
                    h, w = frame.shape[:2]
                    x1_c, y1_c = max(0, x1), max(0, y1)
                    x2_c, y2_c = min(w - 1, x2), min(h - 1, y2)
                    if y2_c > y1_c and x2_c > x1_c:
                        crop = frame[y1_c:y2_c, x1_c:x2_c]
                        img_name = now.strftime('%Y%m%d_%H%M%S_%f') + '.jpg'
                        cv2.imwrite(os.path.join(LOG_IMG_FOLDER, img_name), crop)
                writer.writerow([time_str, label, img_name])

if __name__ == '__main__':
    app.run(debug=True)
