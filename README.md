# Email Service API

API service để quản lý và truy xuất email từ Outlook/Hotmail, với tính năng chính là tìm và lấy mã OTP từ email.

## Tính năng

- Xác thực OAuth2 với Outlook/Hotmail
- Tự động refresh token khi hết hạn
- Tìm và lấy mã OTP từ email
- Tìm kiếm email theo từ khóa
- Hỗ trợ đa luồng xử lý
- API Documentation với Swagger UI

## Cài đặt

1. Clone repository:
```bash
git clone https://github.com/HieuVo28/HotMail.git
cd HotMail
```

2. Tạo môi trường ảo và kích hoạt:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows
```

3. Cài đặt dependencies:
```bash
pip install -r requirements.txt
```

4. Tạo file `.env` và cấu hình:
```env
IMAP_HOST=outlook.office365.com
IMAP_PORT=993
RATE_LIMIT=60
```

## API Endpoints

### 1. Lấy OTP từ Email

```http
GET /api/v1/otp?email=<email>&password=<password>&client_id=<client_id>&refresh_token=<refresh_token>
```

hoặc sử dụng chuỗi:

```http
GET /api/v1/otp/string?hotmail_str=<email>|<password>|<refresh_token>|<client_id>
```

### 2. Tìm kiếm Email

```http
GET /api/v1/search?email=<email>&password=<password>&client_id=<client_id>&refresh_token=<refresh_token>&query=<search_query>
```

## Response Format

### Success Response

```json
[
    {
        "otp": "123456",
        "date": "2024-01-22T10:30:00+00:00",
        "subject": "Email Subject",
        "from": "sender@example.com"
    }
]
```

### Error Response

```json
{
    "detail": {
        "error_code": "invalid_grant",
        "message": "Token hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại để lấy refresh token mới.",
        "correlation_id": "xxx-xxx-xxx"
    }
}
```

## Chạy Development Server

```bash
uvicorn app.main:app --reload
```

Truy cập API documentation tại: `http://localhost:8000/docs`

## Cấu trúc Project

```
email_service/
├── app/
│   ├── api/
│   │   └── routes.py          # API endpoints
│   │   └── auth.py            # Authentication logic
│   │   └── core/
│   │       ├── config.py         # Cấu hình
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   ├── services/
│   │   └── email_service.py  # Business logic
│   └── main.py              # FastAPI app
├── requirements.txt
└── README.md
```

## Contributing

1. Fork repository
2. Tạo nhánh feature: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add some AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Tạo Pull Request

## License

MIT License 