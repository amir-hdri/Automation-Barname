# تحلیل فنی خروجی تست سایت (Site Audit)

## منبع داده
این تحلیل بر اساس خروجی اجرای زیر تهیه شده است:
- Run ID: `run-20260225-201132`
- فایل مرجع خلاصه: `docs/site-audit/summary.json`
- گزارش‌های مرجع:
  - `docs/site-audit/AUTOMATION_CAPTURE_REPORT_FA.md`
  - `docs/site-audit/REPORT.md`
  - `docs/site-audit/FIELD_SUMMARY.md`

## شاخص‌های کلیدی
- تعداد کل درخواست‌ها: `766`
- URL یکتا: `314`
- پاسخ HTML: `24` (ذخیره HTML یکتا: `11`)
- فیلدهای استخراج‌شده فرم: `125` (فیلد یکتا: `47`)
- تعداد `<select>` واقعی: `4`
- کاندید dropdown سفارشی: `55`
- پیام‌های console: `24`
- page errors: `9`
- فریم‌های screencast: `464` (نمونه ذخیره‌شده: `22`)

## وضعیت HTTP
بر اساس `summary.json`:
- `200`: 727
- `500`: 2
- `302`: 2
- `204`: 14
- `-1`: 21

500های ثبت‌شده (بر اساس `http_500_requests.json`):
- `GET https://barname.utcms.ir/barname/Document/HagigiHogugi` (دو بار)

## خطاهای JavaScript سمت کلاینت
بر اساس `page_errors.json`:
- خطای تکرارشونده (9 بار):
  - `TypeError: Cannot read properties of undefined (reading 'defaults')`
  - منبع: `datatables-bootstrap5.js`

نتیجه فنی:
- بخشی از صفحات وابسته به دیتاتیبل، خطای init دارند و ممکن است تعامل UI را ناپایدار کنند.

## یافته‌های فرم و احراز هویت
بر اساس `FIELD_SUMMARY.md` و `form_fields_unique.json`:
- فیلدهای کلیدی احراز هویت حضور دارند:
  - `UserName`
  - `Password`
  - `DNTCaptchaInputText`
  - `RequestVerificationToken`
- فیلدهای نقش/OTP نیز مشاهده شده‌اند:
  - `roleId`, `otp`, `loginId`, `onlyOneRole`

نتیجه فنی:
- جریان لاگین چندمرحله‌ای/پویا و کپچا-محور است؛ selectorهای سخت‌کد ساده قابل اتکا نیستند.

## وضعیت نقشه
- `map_related_requests.json` خالی است (`[]`).

نتیجه فنی:
- در این Run، نشانه شبکه‌ای مشخص از provider نقشه برای انتخاب مسیر دیده نشده است.
- بنابراین fallbackهای dropdown/text برای robustness حیاتی هستند.

## آلودگی/نویز شبکه
Top hosts نشان می‌دهد علاوه بر دامنه اصلی، ترافیک جانبی هم وجود دارد:
- `barname.utcms.ir`: 624
- `mobomovies.co`: 70
- `www.google.com`: 42
- `blob:https:`: 16
- `cptch.utcms.ir`: 4

نتیجه فنی:
- ترافیک ثالث/غیرمرتبط می‌تواند روی پایداری رندر/زمان‌بندی اثر بگذارد.
- کنترل نرخ، retry/backoff و timeoutهای هوشمند ضروری هستند.

## ارتباط با اصلاحات انجام‌شده در پروژه
یافته‌های بالا مستقیم در اصلاحات نهایی منعکس شده‌اند:
- امنیت endpointهای حساس (API Key/JWT)
- مدیریت قانونی کپچا + fail-fast شفاف
- reuse state احراز هویت برای کاهش دفعات حل کپچا
- fallback چند selector برای فرم‌های پویا
- کنترل بار (concurrency + pacing + backoff)

## پیشنهاد پایش عملیاتی بعد از استقرار
- پایش روزانه نرخ 401/429/500 برای endpointهای بارنامه
- snapshot دوره‌ای از `traffic-status`
- نگهداری دوره‌ای خروجی audit (summary/page_errors/http_500)
