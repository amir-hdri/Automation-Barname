# گزارش ثبت کامل تعاملات سایت

- شناسه ران: `run-20260225-201132`
- تعداد کل درخواست‌ها: **766**
- URL یکتا: **314**
- HTML پاسخ‌ها: **24** (ذخیره‌شده: 11)
- فیلد استخراج‌شده: **125** (یکتا: 47)
- Select استاندارد: **4** | کاندید کامپوننت سفارشی: **55**
- پیام کنسول: **24** | page errors: **9**
- فریم‌های ویدئویی ایندکس‌شده: **464** (نمونه ذخیره‌شده: 22)

## فایل‌های اصلی خروجی
- ویدیو تعاملات: `output/site-audit/run-20260225-201132/raw/session.webm`
- Trace اکشن‌ها: `output/site-audit/run-20260225-201132/raw/trace-1772037778214.trace`
- Network log: `output/site-audit/run-20260225-201132/raw/trace-1772037778214.network`
- URLها: `output/site-audit/run-20260225-201132/extracted/barname_urls.txt`
- ایندکس صفحات HTML: `output/site-audit/run-20260225-201132/extracted/html_pages_index.json`
- فیلدها (همه): `output/site-audit/run-20260225-201132/extracted/form_fields.json`
- فیلدها (یکتا): `output/site-audit/run-20260225-201132/extracted/form_fields_unique.json`
- Select summary: `output/site-audit/run-20260225-201132/extracted/select_summary.json`
- Custom dropdown: `output/site-audit/run-20260225-201132/extracted/custom_dropdown_candidates_relevant.json`
- خطاهای کنسول: `output/site-audit/run-20260225-201132/extracted/console_messages.json`
- خطاهای صفحه: `output/site-audit/run-20260225-201132/extracted/page_errors.json`
- فریم‌ها: `output/site-audit/run-20260225-201132/extracted/screencast_frames_index.json`

## صفحات HTML مهم (دامنه barname)
- `200` https://barname.utcms.ir/Barname/Notification/Notification -> `output/site-audit/run-20260225-201132/extracted/html_pages/01-d7255f97ca89d1587358888d5be98d940d3d2173.html.html`
- `500` https://barname.utcms.ir/barname/Document/HagigiHogugi -> `output/site-audit/run-20260225-201132/extracted/html_pages/02-ae07f342bea9ca0881d4052d3d23c37b141636d6.html.html`
- `200` https://barname.utcms.ir/Home/index -> `output/site-audit/run-20260225-201132/extracted/html_pages/03-fe93966add5e5b9d52b280ef7017bd8fb76a904c.html.html`
- `200` https://barname.utcms.ir/Account/Login -> `output/site-audit/run-20260225-201132/extracted/html_pages/04-3d165bfee2d9c10ffc952e6e18b150ecc693a9ea.html.html`
- `200` https://barname.utcms.ir/Home/InfoIndex -> `output/site-audit/run-20260225-201132/extracted/html_pages/05-3a3bcbe8c54eb9d40d2b8ef92b2c97cfbfca5dfa.html.html`
- `200` https://barname.utcms.ir/Barname/Account/Login -> `output/site-audit/run-20260225-201132/extracted/html_pages/06-da71d3f3e4b7aed216179ea26078e974ff2349ba.html.html`
- `200` https://barname.utcms.ir/Barname/Notification/Notification -> `output/site-audit/run-20260225-201132/extracted/html_pages/07-f94110d181809448bb4ad1ca1477d71f27da49bd.html.html`
- `200` https://barname.utcms.ir/Account/Login -> `output/site-audit/run-20260225-201132/extracted/html_pages/08-5e79875185560d3cc5582913d9ff9a8ad7e38220.html.html`

## خطاهای HTTP 500 ثبت‌شده
- `GET` https://barname.utcms.ir/barname/Document/HagigiHogugi
- `GET` https://barname.utcms.ir/barname/Document/HagigiHogugi

## تحلیل علت ورود مجدد اجباری
- علت اصلی در این ران «تشخیص ربات» نبوده؛ سشن کاربر پس از خطای داخلی صفحه قطع شده است.
- در `2026-02-25 16:43:32` و `2026-02-25 16:45:17`، مسیر `barname/Document/HagigiHogugi` خطای `500` داده است.
- بلافاصله بعد از خطا، `GET /Account/Logout` با پاسخ `302` ثبت شده و سرور کوکی‌های احراز هویت (`ApplicationToken`, `Barname`, `dntCaptcha`) را خالی کرده و به `/Account/Login` ریدایرکت کرده است.
- در پاسخ‌های کپچا (`cptch.utcms.ir/.../challenge`) وضعیت `200` بوده و نشانه‌ای از بلاک ضدربات (`403` یا `429`) دیده نشده است.
- پیام «کاربری با این مشخصات در سامانه یافت نشد.» نیز برای یکی از تلاش‌های لاگین ثبت شده است (فایل: `.playwright-cli/traces/resources/1e83ffe46dd4d7c2c1ec24b2d5d74d274069a970.json`).
- مرجع لاگ شبکه: `output/site-audit/run-20260225-201132/raw/trace-1772037778214.network`
- مرجع HTML خطای سامانه: `output/site-audit/run-20260225-201132/extracted/html_pages/02-ae07f342bea9ca0881d4052d3d23c37b141636d6.html.html`

## نام فیلدهای یکتا (name)
- `ActionName`
- `CApiId`
- `CapToken`
- `CapType`
- `CloseVerifyModal`
- `DNTCaptchaInputText`
- `DNTCaptchaText`
- `DNTCaptchaToken`
- `NationalCode`
- `Password`
- `RequestVerificationToken`
- `UserName`
- `btnclose`
- `btnshow`
- `ei`
- `loginId`
- `onlyOneRole`
- `otp`
- `q`
- `roleId`
- `ruleExcepted`
- `sca_esv`

## شناسه‌های یکتا (id)
- `APjFqb`
- `ActionName`
- `AllDiesel`
- `AllDriver`
- `AllPetrol`
- `CApiId`
- `CapToken`
- `CapType`
- `CloseVerifyModal`
- `DNTCaptchaInputText`
- `DNTCaptchaText`
- `DNTCaptchaToken`
- `DieselWithBarbarg`
- `DriverWithBarbarg`
- `NationalCode`
- `Nationalbtnclose`
- `PetrolWithBarbarg`
- `ReadStatus`
- `RequestVerificationToken`
- `RoleSelect`
- `advc-btn`
- `btn_Clean`
- `btn_Search`
- `btnclose`
- `btnshow`
- `dubbed`
- `inter`
- `loginId`
- `onlyOneRole`
- `otp`
- `register`
- `roleId`
- `ruleExcepted`
- `search-inp`
- `signIn`
- `sort_asc`
- `sourceVisits`
- `submitRules`
- `user-name`
- `user-password`

## نکته
- در این ران، ترافیک دامنه‌های خارج از سایت اصلی (از جمله `mobomovies.co`) هم ثبت شده است و در فایل‌های خام وجود دارد.
- در این ران، درخواست مرتبط با نقشه (Leaflet/OpenLayers/Google Maps API) در لاگ شبکه دیده نشد.
