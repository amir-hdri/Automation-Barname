# سیستم اتوماسیون هوشمند صدور بارنامه UTCMS

این پروژه یک ربات پیشرفته و عملیاتی برای خودکارسازی فرآیند ثبت بارنامه در سایت [utcms.ir](https://utcms.ir/) است. این سیستم با استفاده از **FastAPI** برای مدیریت درخواست‌ها و **Playwright** برای تعامل با مرورگر، قادر است به صورت هوشمند مکان مبدا و مقصد را از روی نقشه انتخاب کرده و فرم‌ها را پر کند.

---

## 🚀 قابلیت‌ها (Features)

*   **انتخاب هوشمند مسیر (Smart Route Selection):**
    *   پشتیبانی از انواع نقشه‌ها (Google Maps, OpenLayers, Leaflet, Mapbox).
    *   تشخیص خودکار نوع نقشه و کلیک دقیق روی مختصات جغرافیایی.
    *   محاسبه مسافت و زمان سفر (Haversine Formula / Map API).
*   **مکانیزم جایگزین (Fallback Mechanism):**
    *   اگر نقشه کار نکند، سیستم به صورت خودکار از منوی کشویی (استان/شهر) استفاده می‌کند.
    *   اگر منوی کشویی در دسترس نباشد، از ورودی متنی و تکمیل خودکار (Autocomplete) استفاده می‌شود.
*   **مدیریت مرورگر بهینه (Optimized Browser Management):**
    *   استفاده از یک نمونه مرورگر (Singleton) برای کاهش مصرف منابع.
    *   مدیریت چرخه حیات (Lifecycle) دقیق برای جلوگیری از نشت حافظه.
*   **سیستم گزارش‌دهی (Reporting System):**
    *   ارائه آمار لحظه‌ای از تعداد درخواست‌ها، موفقیت‌ها و شکست‌ها.
    *   گزارش تفکیکی استفاده از نقشه.

---

## 🛠️ پیش‌نیازها (Prerequisites)

قبل از شروع، مطمئن شوید که موارد زیر روی سیستم شما نصب شده است:

*   **Python 3.8+**
*   **pip** (مدیریت بسته پایتون)
*   دسترسی به اینترنت برای دانلود مرورگرهای Playwright.

---

## 📦 نصب و راه‌اندازی (Installation)

۱. **کلون کردن مخزن:**
   ```bash
   git clone https://github.com/your-repo/utcms-automation.git
   cd utcms-automation
   ```

۲. **ایجاد محیط مجازی (Virtual Environment):**
   ```bash
   python -m venv venv
   # در لینوکس/مک:
   source venv/bin/activate
   # در ویندوز:
   venv\Scripts\activate
   ```

۳. **نصب وابستگی‌ها:**
   ```bash
   pip install -r requirements.txt
   ```

۴. **نصب مرورگرهای Playwright:**
   ```bash
   playwright install chromium
   ```

---

## ⚙️ پیکربندی (Configuration)

تنظیمات اصلی پروژه در فایل `app/core/config.py` قرار دارد. شما می‌توانید متغیرهایی مانند آدرس سایت هدف یا حالت نمایش مرورگر (Headless) را تغییر دهید.

```python
class UTCMSConfig:
    WAYBILL_URL = "https://barname.utcms.ir/Barname/Waybill/Create"
    HEADLESS = True  # برای مشاهده عملکرد ربات، این مقدار را False کنید
```

متغیرهای مهم محیطی برای محیط عملیاتی:

```bash
# لاگین
export UTCMS_USERNAME="..."
export UTCMS_PASSWORD="..."
export LOGIN_URL="https://barname.utcms.ir/Login"
export USE_PERSISTENT_AUTH_STATE=true
export AUTH_STATE_PATH=".auth/utcms_state.json"

# کپچا (قانونی/دستی)
export UTCMS_CAPTCHA_VALUE=""  # اگر مقدار کپچا را بیرون از ربات دارید
export UTCMS_ENABLE_MANUAL_CAPTCHA=true
export UTCMS_MANUAL_CAPTCHA_TIMEOUT_SECONDS=120
export UTCMS_MANUAL_CAPTCHA_POLL_SECONDS=0.7
export CAPTCHA_MODE="provider_first"  # provider_first | manual_only | provider_only
export CAPTCHA_PROVIDER="twocaptcha"
export TWOCAPTCHA_API_KEY=""

# کنترل بار در حجم بالا
export WAYBILL_MAX_CONCURRENT=2
export WAYBILL_MIN_GAP_SECONDS=0.8
export WAYBILL_JITTER_SECONDS=0.4
export WAYBILL_MAX_RETRIES=1

# امنیت endpointهای حساس (API Key/JWT)
export API_AUTH_MODE="api_key_or_jwt"  # api_key | jwt | api_key_or_jwt | api_key_and_jwt | off
export API_KEY_HEADER="X-API-Key"
export API_KEY="REPLACE_WITH_STRONG_SECRET"
export JWT_SECRET=""
export JWT_ALGORITHM="HS256"
```

---

## ▶️ اجرا (Running)

برای اجرای سرور API از دستور زیر استفاده کنید:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

*   آدرس مستندات API (Swagger UI): [http://localhost:8000/docs](http://localhost:8000/docs)
*   آدرس پنل وضعیت: [http://localhost:8000](http://localhost:8000)
*   Health check: [http://localhost:8000/healthz](http://localhost:8000/healthz)
*   Readiness check: [http://localhost:8000/readyz](http://localhost:8000/readyz)

---

## 📖 نحوه استفاده (Usage)

### ۱. ثبت بارنامه با نقشه (`POST /waybill/create-with-map`)

نمونه درخواست (JSON Body):

```json
{
  "operation_mode": "safe",
  "session_id": "user_session_123",
  "sender": {
    "name": "علی محمدی",
    "phone": "09121234567"
  },
  "receiver": {
    "name": "شرکت پخش",
    "phone": "02188888888"
  },
  "origin": {
    "province": "تهران",
    "city": "تهران",
    "address": "میدان آزادی",
    "coordinates": {
      "lat": 35.6997,
      "lng": 51.3380
    }
  },
  "destination": {
    "province": "خراسان رضوی",
    "city": "مشهد",
    "address": "بلوار وکیل آباد",
    "coordinates": {
      "lat": 36.2972,
      "lng": 59.6067
    }
  },
  "cargo": {
    "type": "مواد غذایی",
    "weight": 5000
  },
  "vehicle": {
    "plate": "12ع345-66"
  },
  "financial": {
    "cost": 15000000
  }
}
```

`operation_mode`:
- `safe` (پیش‌فرض): فرم کامل پر می‌شود ولی ثبت نهایی انجام نمی‌شود.
- `full`: ثبت واقعی انجام می‌شود (فقط با `ALLOW_LIVE_SUBMIT=true`).

### ۲. دریافت گزارشات (`GET /reports/summary`)

پاسخ نمونه:

```json
{
  "total_requests": 150,
  "successful_waybills": 142,
  "failed_attempts": 8,
  "success_rate": "94.7%",
  "map_usage_distribution": {
    "google_maps": 100,
    "leaflet": 50
  }
}
```

گزارش عملیاتی:
- `GET /reports/operational` شامل latency p50/p95، دسته‌بندی خطا و شمارنده mode.

---

## 🚢 استقرار (Deployment)

برای استقرار روی سرور لینوکس (Ubuntu/Debian) پیشنهاد می‌شود از **Docker** یا **Systemd** استفاده کنید.

### روش ۱: استفاده از Systemd (سرویس)

۱. یک فایل سرویس ایجاد کنید: `/etc/systemd/system/utcms.service`
   ```ini
   [Unit]
   Description=UTCMS Automation Bot
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/path/to/utcms-automation
   ExecStart=/path/to/utcms-automation/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

۲. فعال‌سازی و شروع سرویس:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable utcms
   sudo systemctl start utcms
   ```

### نکات مهم عملیاتی:
*   **منابع سرور:** Playwright به حافظه RAM قابل توجهی نیاز دارد. حداقل ۲ گیگابایت RAM توصیه می‌شود.
*   **لاگ‌گیری:** خطاهای مرورگر در کنسول چاپ می‌شوند. برای مدیریت بهتر، از ابزارهایی مثل Sentry استفاده کنید.
*   **کپچا سرویس‌محور:** با تنظیم `CAPTCHA_PROVIDER=twocaptcha` و `TWOCAPTCHA_API_KEY` می‌توان حل کپچا را خودکار کرد.
*   **گزینه حل دستی کپچا:** با `CAPTCHA_MODE=manual_only` و `UTCMS_ENABLE_MANUAL_CAPTCHA=true` حل کپچا به‌صورت دستی فعال می‌شود.

### روش ۲: Docker Compose
```bash
cp env.example .env
docker compose up --build
```

### Smoke test حالت ایمن
```bash
python scripts/live_smoke.py --base-url http://127.0.0.1:8000 --api-key "$API_KEY"
```

---

## 🧪 تست‌ها (Tests)

برای اطمینان از صحت عملکرد کدها، تست‌های واحد را اجرا کنید:

```bash
pytest
```
یا
```bash
python -m unittest discover tests
```
