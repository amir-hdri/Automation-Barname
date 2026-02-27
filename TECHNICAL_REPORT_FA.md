# گزارش فنی و دقیق پروژه اتوماسیون بارنامه (آماده‌سازی GitHub)

## 1) مشخصات پروژه و خروجی نهایی
- مسیر پروژه اصلی:
  - `/Users/amirheidari/Desktop/Bar/Auto-Barrname-main-6424634728173761651`
- مسیر نسخه پاک‌سازی‌شده (GitHub-ready):
  - `/Users/amirheidari/Desktop/bar22/utcms-automation-github-ready`
- فایل فشرده آماده آپلود GitHub:
  - `/Users/amirheidari/Desktop/bar22/utcms-automation-github-ready.zip`
- هش SHA-256 فایل خروجی:
  - `bc2f1e94226b45fec8c096807bccde20fa43f529c4abcec26fe9e198d0cea531`

## 2) عملیات پاک‌سازی فایل‌های اضافی
نسخه GitHub-ready با حذف کامل فایل‌های غیرضروری تولید شد.

### الگوهای حذف‌شده
- محیط مجازی: `.venv/`
- کش تست: `.pytest_cache/`
- داده احراز هویت محلی: `.auth/`
- فایل‌های کش پایتون: `__pycache__/`, `*.pyc`
- فایل پایگاه‌داده محلی: `*.db`
- آرتیفکت‌های دیباگ/اسکرین‌شات:
  - `waybill_map_error.png`
  - `waybill_notfound_snapshot.html`
- فایل‌های سیستمی: `.DS_Store`

### آمار قبل/بعد پاک‌سازی
- پروژه اصلی:
  - تعداد فایل: `5224`
  - حجم: `211M`
- نسخه GitHub-ready:
  - تعداد فایل: `87`
  - حجم: `540K`

### بخشی از اقلام حذف‌شده در پروژه اصلی
- فایل‌های `.venv`: `5070`
- فایل‌های کش پایتون (`__pycache__` / `*.pyc`): `2123`
- فایل‌های `.db`: `1`
- فایل‌های snapshot/screenshot مرتبط با اجرا: `2`
- فایل‌های `.auth`: `1`
- فایل‌های `.pytest_cache`: `5`

## 3) تایید سلامت نسخه پاک‌سازی‌شده
تست کامل روی نسخه پاک‌سازی‌شده اجرا شد:
- نتیجه: `84 passed in 50.89s`
- نتیجه نشان می‌دهد نسخه خروجی برای انتشار کد و CI آماده است.

## 4) معماری فنی پروژه
### هسته سرویس
- `FastAPI` با lifecycle برای init/close مرورگر و DB
- API اصلی:
  - `POST /waybill/create-with-map`
  - `POST /waybill/detect-map`
  - `GET /waybill/traffic-status`
  - `GET /reports/summary`
  - `GET /reports/operational`
  - `GET /healthz`, `GET /readyz`

### لایه اتوماسیون
- `BrowserManager`: مدیریت Browser/Context/Page
- `UTCMSAuthenticator`: لاگین + مدیریت کپچا (provider/manual)
- `EnhancedWaybillManager`: پرکردن فرم، انتخاب مبدا/مقصد از نقشه، fallback، submit
- `LocationSelector/MapController`: تشخیص و تعامل با انواع نقشه

### پایداری شبکه (افزوده/تقویت‌شده)
- لایه مرکزی تشخیص خطاهای موقتی شبکه:
  - `app/core/network.py`
- `goto` با retry نمایی + jitter در auth/service/waybill flow
- تبدیل خطاهای موقتی شبکه به پاسخ عملیاتی `503` با پیام قابل اقدام

## 5) کنترل‌های امنیتی و عملیاتی
- محافظت endpointهای حساس با `API Key / JWT` (قابل تنظیم)
- محدودسازی ترافیک/همزمانی برای جلوگیری از فشار و block شدن
- حالت `safe/full` با گیت `ALLOW_LIVE_SUBMIT`
- گزارش‌گیری خطا/latency/mode برای پایش عملیاتی

## 6) وضعیت واقعی ربات در محیط UTCMS
- ربات از نظر کدنویسی، تست و کنترل خطا آماده است.
- ثبت واقعی وابسته به این پیش‌نیازهای بیرونی است:
  - دسترسی حساب به ماژول صدور بارنامه در UTCMS
  - پایداری DNS/شبکه اینترنت تا دامنه مقصد
  - مدیریت کپچا طبق سیاست قانونی سامانه

## 7) دستورالعمل آپلود به GitHub
از روی نسخه آماده‌شده (`utcms-automation-github-ready`) اجرا کنید:

```bash
cd /Users/amirheidari/Desktop/bar22/utcms-automation-github-ready

git init
git add .
git commit -m "Initial clean release: UTCMS automation"

git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

یا اگر ترجیح می‌دهید فایل فشرده آپلود شود:
- فایل آماده: `/Users/amirheidari/Desktop/bar22/utcms-automation-github-ready.zip`

## 8) فهرست فایل‌های مهم نسخه خروجی
- `app/` (هسته اپلیکیشن)
- `tests/` (84 تست)
- `requirements.txt`
- `README.md`
- `docker-compose.yml`
- `Dockerfile`
- `env.example`
- `deploy/`
- `docs/`

## 9) جمع‌بندی نهایی
- پروژه به‌صورت حرفه‌ای برای GitHub آماده شد.
- فایل‌های اضافی از نسخه خروجی حذف شدند.
- یک بسته فشرده مستقل برای آپلود ساخته شد.
- گزارش فنی دقیق حاضر تولید و ذخیره شد.
