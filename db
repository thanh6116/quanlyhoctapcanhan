import sqlite3
import os

DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qlht.db")

class Database:
    def __init__(self, db_path=DB_NAME):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """Tạo các bảng dữ liệu nếu có"""
        #bảng môn học
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS mon_hoc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ten_mon TEXT NOT NULL,
                so_tin_chi INTEGER DEFAULT 0,
                giang_vien TEXT,
                ghi_chu TEXT
            )
        """)
        #bảng lịch học 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lich_hoc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER NOT NULL,
                thu TEXT NOT NULL,
                tiet_bat_dau INTEGER NOT NULL,
                tiet_ket_thuc INTEGER NOT NULL,
                phong_hoc TEXT,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE CASCADE
            )
        """)

        #bảng lịch thi
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS lich_thi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER NOT NULL,
                ngay_thi TEXT NOT NULL,
                gio_thi TEXT,
                phong_thi TEXT,
                hinh_thuc TEXT,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE CASCADE
            )
        """)
        #bảng deadline
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bai_tap (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER,
                tieu_de TEXT NOT NULL,
                mo_ta TEXT,
                han_nop TEXT NOT NULL,
                muc_do_uu_tien TEXT DEFAULT 'Trung bình',
                trang_thai TEXT DEFAULT 'Chưa hoàn thành',
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE SET NULL
            )
        """)

        #bảng ghi chú 
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ghi_chu (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mon_hoc_id INTEGER,
                tieu_de TEXT NOT NULL,
                noi_dung TEXT,
                ngay_tao TEXT NOT NULL,
                FOREIGN KEY (mon_hoc_id) REFERENCES mon_hoc(id) ON DELETE SET NULL
            )
        """)

        self.conn.commit()

    def _id_nho_nhat_con_trong(self, ten_bang):
        """Tìm ID nhỏ nhất chưa được dùng trong bảng (1, 2, 3, ...)."""
        self.cursor.execute(f"SELECT id FROM {ten_bang} ORDER BY id")
        new_id = 1
        for (used_id,) in self.cursor.fetchall():
            if used_id != new_id:
                break
            new_id += 1
        return new_id

    # tên môn học
    def them_mon_hoc(self, ten_mon, so_tin_chi, giang_vien, ghi_chu=""):
        new_id = self._id_nho_nhat_con_trong("mon_hoc")
        self.cursor.execute(
            "INSERT INTO mon_hoc (id, ten_mon, so_tin_chi, giang_vien, ghi_chu) "
            "VALUES (?, ?, ?, ?, ?)",
            (new_id, ten_mon, so_tin_chi, giang_vien, ghi_chu),
        )
        self.conn.commit()
        return new_id

    def lay_danh_sach_mon_hoc(self):
        self.cursor.execute("SELECT * FROM mon_hoc ORDER BY ten_mon")
        return self.cursor.fetchall()

    def xoa_mon_hoc(self, mon_hoc_id):
        self.cursor.execute("DELETE FROM mon_hoc WHERE id = ?", (mon_hoc_id,))
        self.conn.commit()

    def sua_mon_hoc(self, mon_hoc_id, ten_mon, so_tin_chi, giang_vien, ghi_chu):
        self.cursor.execute(
            "UPDATE mon_hoc SET ten_mon=?, so_tin_chi=?, giang_vien=?, ghi_chu=? WHERE id=?",
            (ten_mon, so_tin_chi, giang_vien, ghi_chu, mon_hoc_id),
        )
        self.conn.commit()

    # lịch học
    def them_lich_hoc(self, mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc):
        self.cursor.execute(
            "INSERT INTO lich_hoc (mon_hoc_id, thu, tiet_bat_dau, tiet_ket_thuc, phong_hoc) VALUES (?, ?, ?, ?, ?)",
            (mon_hoc_id, thu, tiet_bd, tiet_kt, phong_hoc),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_thoi_khoa_bieu(self):
        self.cursor.execute("""
            SELECT lich_hoc.id, mon_hoc.ten_mon, lich_hoc.thu,
                   lich_hoc.tiet_bat_dau, lich_hoc.tiet_ket_thuc, lich_hoc.phong_hoc
            FROM lich_hoc
            JOIN mon_hoc ON lich_hoc.mon_hoc_id = mon_hoc.id
            ORDER BY
                CASE lich_hoc.thu
                    WHEN 'Thứ 2' THEN 2 WHEN 'Thứ 3' THEN 3 WHEN 'Thứ 4' THEN 4
                    WHEN 'Thứ 5' THEN 5 WHEN 'Thứ 6' THEN 6 WHEN 'Thứ 7' THEN 7
                    WHEN 'Chủ nhật' THEN 8 ELSE 9
                END, lich_hoc.tiet_bat_dau
        """)
        return self.cursor.fetchall()

    def xoa_lich_hoc(self, lich_id):
        self.cursor.execute("DELETE FROM lich_hoc WHERE id = ?", (lich_id,))
        self.conn.commit()

    # lịch thi
    def them_lich_thi(self, mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc):
        self.cursor.execute(
            "INSERT INTO lich_thi (mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc) VALUES (?, ?, ?, ?, ?)",
            (mon_hoc_id, ngay_thi, gio_thi, phong_thi, hinh_thuc),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_lich_thi(self):
        self.cursor.execute("""
            SELECT lich_thi.id, mon_hoc.ten_mon, lich_thi.ngay_thi,
                   lich_thi.gio_thi, lich_thi.phong_thi, lich_thi.hinh_thuc
            FROM lich_thi
            JOIN mon_hoc ON lich_thi.mon_hoc_id = mon_hoc.id
            ORDER BY lich_thi.ngay_thi
        """)
        return self.cursor.fetchall()

    def xoa_lich_thi(self, thi_id):
        self.cursor.execute("DELETE FROM lich_thi WHERE id = ?", (thi_id,))
        self.conn.commit()

    # deadline
    def them_bai_tap(self, mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien):
        self.cursor.execute(
            """INSERT INTO bai_tap (mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien, trang_thai)
               VALUES (?, ?, ?, ?, ?, 'Chưa hoàn thành')""",
            (mon_hoc_id, tieu_de, mo_ta, han_nop, muc_do_uu_tien),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_danh_sach_bai_tap(self, chi_chua_hoan_thanh=False):
        query = """
            SELECT bai_tap.id, mon_hoc.ten_mon, bai_tap.tieu_de, bai_tap.mo_ta,
                   bai_tap.han_nop, bai_tap.muc_do_uu_tien, bai_tap.trang_thai
            FROM bai_tap
            LEFT JOIN mon_hoc ON bai_tap.mon_hoc_id = mon_hoc.id
        """
        if chi_chua_hoan_thanh:
            query += " WHERE bai_tap.trang_thai != 'Hoàn thành'"
        query += " ORDER BY bai_tap.han_nop"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def cap_nhat_trang_thai_bai_tap(self, bai_tap_id, trang_thai):
        self.cursor.execute(
            "UPDATE bai_tap SET trang_thai=? WHERE id=?", (trang_thai, bai_tap_id)
        )
        self.conn.commit()

    def xoa_bai_tap(self, bai_tap_id):
        self.cursor.execute("DELETE FROM bai_tap WHERE id = ?", (bai_tap_id,))
        self.conn.commit()

    # chú thích thêm
    def them_ghi_chu(self, mon_hoc_id, tieu_de, noi_dung, ngay_tao):
        self.cursor.execute(
            "INSERT INTO ghi_chu (mon_hoc_id, tieu_de, noi_dung, ngay_tao) VALUES (?, ?, ?, ?)",
            (mon_hoc_id, tieu_de, noi_dung, ngay_tao),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def lay_danh_sach_ghi_chu(self):
        self.cursor.execute("""
            SELECT ghi_chu.id, mon_hoc.ten_mon, ghi_chu.tieu_de, ghi_chu.noi_dung, ghi_chu.ngay_tao
            FROM ghi_chu
            LEFT JOIN mon_hoc ON ghi_chu.mon_hoc_id = mon_hoc.id
            ORDER BY ghi_chu.ngay_tao DESC
        """)
        return self.cursor.fetchall()

    def xoa_ghi_chu(self, ghi_chu_id):
        self.cursor.execute("DELETE FROM ghi_chu WHERE id = ?", (ghi_chu_id,))
        self.conn.commit()

    def dong(self):
        self.conn.close()
