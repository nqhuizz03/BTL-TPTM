<h2 align="center">
    <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
        🎓 Khoa Công nghệ Thông tin - Đại học Đại Nam
    </a>
</h2>

<h2 align="center">
    HỆ THỐNG PHÁT HIỆN GIAN LẬN TRONG THI CỬ BẰNG TRÍ TUỆ NHÂN TẠO
</h2>

<p align="center">
       <img src="C:\Users\Admin\Downloads\1IT.jpg" alt="DaiNam University Logo" width="200"/><br>
</p>

<p align="center">
  <a href="https://www.facebook.com/DNUAIoTLab">
    <img src="https://img.shields.io/badge/AIoTLab-green?style=for-the-badge" alt="AIoTLab" />
  </a>
  <a href="https://dainam.edu.vn/vi/khoa-cong-nghe-thong-tin">
    <img src="https://img.shields.io/badge/Khoa%20Công%20nghệ%20Thông%20tin-blue?style=for-the-badge" alt="Khoa CNTT" />
  </a>
  <a href="https://dainam.edu.vn">
    <img src="https://img.shields.io/badge/Đại%20học%20Đại%20Nam-orange?style=for-the-badge" alt="Đại học Đại Nam" />
  </a>
</p>

# 🚦 Hệ Thống Giám Sát An Toàn Giao Thông Bằng YOLOv8

## 🎯 Mục tiêu đề tài

Phát triển hệ thống giám sát người điều khiển xe máy **có đội mũ bảo hiểm hay không**, phát hiện **vi phạm chở quá số người** trên xe máy. Hệ thống có thể:

* Phân tích ảnh, video hoặc stream từ ESP32-CAM.
* Ghi log vi phạm vào file CSV.
* Lưu ảnh người vi phạm.
* Hiển thị thống kê và số liệu theo thời gian thực.

---

## 🛠️ Công nghệ sử dụng

| Thành phần     | Công nghệ                                            |
| -------------- | ---------------------------------------------------- |
| Nhận diện      | [YOLOv8](https://github.com/ultralytics/ultralytics) |
| Web server     | Flask (Python)                                       |
| Stream video   | ESP32-CAM hoặc video upload                          |
| Giao diện      | HTML, Bootstrap, JavaScript                          |
| Log & Thống kê | CSV + Pandas                                         |

---

## 📂 Cấu trúc thư mục

```
├── app.py                 # Flask app chính
├── best.pt               # Mô hình YOLOv8 đã huấn luyện
├── templates/            # HTML frontend
│   ├── index.html
│   ├── stream.html
│   ├── video.html
│   └── stats.html
├── static/
│   ├── uploads/          # Ảnh/video gốc
│   └── outputs/          # Ảnh/video đã xử lý
├── logs/
│   ├── violations.csv    # Log vi phạm
│   └── images/           # Ảnh người vi phạm (crop từ khung hình)
└── requirements.txt      # Danh sách thư viện
```

---

## ▶️ Cách chạy hệ thống

### 1. Tạo môi trường ảo (khuyến khích)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS
```

### 2. Cài thư viện cần thiết

```bash
pip install -r requirements.txt
```

### 3. Chạy server Flask

```bash
python app.py
```

Truy cập tại: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ⚙️ Các chức năng chính

| Chức năng                    | URL                        | Mô tả                            |
| ---------------------------- | -------------------------- | -------------------------------- |
| Trang chính                  | `/`                        | Giao diện chính upload ảnh/video |
| Upload & xử lý ảnh/video     | `/upload`                  | Xử lý bằng YOLOv8                |
| Xem ảnh kết quả              | `/image/<filename>`        | Hiển thị ảnh đã nhận diện        |
| Xem video kết quả            | `/video/<filename>`        | Hiển thị video đã nhận diện      |
| Stream trực tiếp (ESP32-CAM) | `/stream` và `/video_feed` | Nhận ảnh từ camera               |
| Thống kê vi phạm             | `/stats` và `/stats_json`  | Biểu đồ số lượng theo ngày       |
| Thống kê thời gian thực      | `/stats_stream`            | Cập nhật real-time               |

---

## 📌 Ghi log vi phạm

* Khi phát hiện người **không đội mũ bảo hiểm** (`class_id == 1`) hoặc vi phạm, hệ thống:

  * Lưu ảnh crop phần người vi phạm vào `logs/images/`
  * Ghi vào `logs/violations.csv` gồm:

    * `time`: thời gian vi phạm
    * `violation`: loại vi phạm ("No Helmet", "With Helmet")
    * `image`: tên ảnh crop

---

## 🧠 Huấn luyện mô hình YOLOv8

Bạn có thể tự huấn luyện mô hình `best.pt` với dữ liệu nhãn đội mũ bảo hiểm:

```bash
yolo task=detect mode=train model=yolov8n.pt data=data.yaml epochs=100 imgsz=640
```

---

## 📊 Giao diện

* `index.html`: Giao diện chính để upload ảnh/video
* `stream.html`: Hiển thị camera ESP32-CAM
* `stats.html`: Biểu đồ thống kê số lượng người vi phạm

---

## 📷 Ví dụ

![demo1](https://via.placeholder.com/500x300?text=Helmet+Detection)
![demo2](https://via.placeholder.com/500x300?text=Stats+Page)

---

## 📌 Yêu cầu

* Python 3.8+
* OpenCV, Flask, Ultralytics, Pandas


