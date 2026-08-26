
## Cách chạy chương trình
```bash
python main.py
```
Khi chạy lần đầu, chương trình sẽ tự động tạo file cơ sở dữ liệu `qlht.db`
trong cùng thư mục — không cần cấu hình gì thêm.
## Cấu trúc thư mục
```
qlht_project/
├── main.py          # Giao diện chính (Tkinter) và logic điều khiển sự kiện
├── database.py       # Lớp Database: kết nối và thao tác CRUD với SQLite
├── qlht.db            # File cơ sở dữ liệu (tự sinh khi chạy lần đầu)
└── README.md
```
## Các chức năng chính
1. **Tổng quan**: thống kê nhanh số môn học, bài tập chưa hoàn thành,
   lịch thi sắp tới, ghi chú; danh sách deadline trong 7 ngày tới.
2. **Môn học**: thêm/xóa/xem danh sách môn học (tên, số tín chỉ, giảng viên,
   ghi chú).
3. **Thời khóa biểu**: thêm lịch học theo thứ/tiết/phòng, xem theo tuần,
   tự động sắp xếp theo thứ tự Thứ 2 → Chủ nhật.
4. **Lịch thi**: quản lý ngày giờ, phòng thi, hình thức thi theo từng môn.
5. **Bài tập / Deadline**: thêm bài tập gắn với môn học, đặt mức ưu tiên,
   cập nhật trạng thái (Chưa hoàn thành / Đang làm / Hoàn thành).
   Danh sách được tô màu cảnh báo:
   - 🔴 Đỏ: đã quá hạn
   - 🟠 Cam: còn ≤ 3 ngày đến hạn
   - 🟢 Xanh: đã hoàn thành
6. **Ghi chú**: lưu ghi chú bài giảng gắn với từng môn học.

## Ghi chú kỹ thuật
- Cơ sở dữ liệu dùng 5 bảng: `mon_hoc`, `lich_hoc`, `lich_thi`, `bai_tap`,
  `ghi_chu`, liên kết qua khóa ngoại `mon_hoc_id`.
- Khi xóa một môn học, toàn bộ lịch học/lịch thi liên quan sẽ tự động bị xóa
  theo (ON DELETE CASCADE); bài tập và ghi chú liên quan sẽ được giữ lại
  nhưng gỡ liên kết môn học (ON DELETE SET NULL).
- Định dạng ngày tháng dùng trong toàn bộ ứng dụng: `dd/mm/yyyy`.
