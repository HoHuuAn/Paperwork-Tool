# Photocopy Tools

## Giới thiệu
Ứng dụng hỗ trợ xử lý ảnh CCCD, tạo file PDF phục vụ in ấn, sử dụng giao diện PyQt6.

## Yêu cầu hệ thống
- Python 3.11 trở lên
- Windows OS
- Các thư viện Python: PyQt6, fpdf, PyPDF2

## Cài đặt thư viện
Chạy lệnh sau trong thư mục dự án:

```powershell
pip install PyQt6 fpdf PyPDF2
```

## Chạy ứng dụng
Chạy file giao diện chính:

```powershell
python tools_v3.py
```

## Build file thực thi (EXE)
Ứng dụng hỗ trợ build bằng PyInstaller. Chạy lệnh sau:

```powershell
pyinstaller --clean --noconfirm tools_v3.spec
```

Hoặc sử dụng file batch có sẵn:

```powershell
./build.bat
```

File thực thi sẽ nằm trong thư mục `dist/`.

## Sử dụng
- Chọn ảnh CCCD cần xử lý.
- Chọn số lượng in.
- Nhấn nút "1 trang" hoặc "2 trang" để tạo file PDF.
- File PDF đầu ra sẽ nằm cùng thư mục với ảnh đầu vào.

## Lưu ý
- Đảm bảo các file UI, icon, modules đều nằm đúng vị trí như cấu trúc dự án.
- Nếu gặp lỗi, kiểm tra lại phiên bản Python và các thư viện đã cài đặt.
