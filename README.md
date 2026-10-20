#  Phần mềm Quản lý Học tập Cá nhân

Ứng dụng desktop giúp sinh viên quản lý việc học: môn học, thời khóa biểu, lịch thi, bài tập/deadline và ghi chú bài giảng 

Giao diện : Tinker 

Cơ sở dữ liệu : SQLite

##  Tính năng
Dùng Tab hiển thị chức năng 

Tổng quan | Thống kê số môn học, bài tập chưa xong, lịch thi sắp tới, số ghi chú; danh sách deadline trong 7 ngày tới 

Môn học | Thêm / xóa môn học (tên, số tín chỉ, giảng viên, ghi chú) , chỉnh sửa và tìm kiếm môn học đã thêm 

Thời khóa biểu | Thêm / xóa lịch học theo thứ, tiết bắt đầu - kết thúc, phòng học 

Lịch thi | Thêm / xóa lịch thi (ngày, giờ, phòng, hình thức thi) 

Bài tập / Deadline | Thêm bài tập, đổi trạng thái, đặt mức ưu tiên; tô màu cảnh báo: quá hạn (đỏ), còn ≤ 3 ngày (cam), hoàn thành (xanh) 

Ghi chú | Lưu ghi chú bài giảng quan trọng theo từng môn 

##  Yêu cầu
- Python **3.8** trở lên
- Tkinter (đi kèm Python trên Windows/macOS; trên Linux có thể cần cài thêm: `sudo apt install python3-tk`)
- Không cần cài thư viện bên ngoài

# 2. Chạy ứng dụng
python main.py
``
Cấu Trúc dự án 
```
.
├── main.py          # Giao diện chính (Tkinter) và xử lý sự kiện
├── database.py      # Lớp Database: tạo bảng và thao tác SQLite
├── requirements.txt # Danh sách thư viện (hiện không cần thư viện ngoài)
├── .gitignore
├── LICENSE
└── README.md
```
File `qlht.db` được tạo tự động khi chạy và không được đưa lên Git.
##  Cơ sở dữ liệu
SQLite với 5 bảng:

- `mon_hoc`: môn học
- `lich_hoc`: thời khóa biểu (khóa ngoại `mon_hoc_id`, `ON DELETE CASCADE`)
- `lich_thi`: lịch thi (khóa ngoại `mon_hoc_id`, `ON DELETE CASCADE`)
- `bai_tap`: bài tập / deadline (khóa ngoại `mon_hoc_id`, `ON DELETE SET NULL`)
- `ghi_chu`: ghi chú bài giảng (khóa ngoại `mon_hoc_id`, `ON DELETE SET NULL`)
##  Lưu ý khi sử dụng
- Ngày nhập theo định dạng **dd/mm/yyyy** (ví dụ: `25/12/2026`).
- Giao diện dùng font **Segoe UI** (có sẵn trên Windows). Trên hệ điều hành khác, Tkinter sẽ tự chọn font thay thế.


