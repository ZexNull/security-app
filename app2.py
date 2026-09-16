import streamlit as st
import requests
import smtplib
import time
from email.mime.text import MIMEText

# --- 1. إعدادات الصفحة والعنوان ---
st.set_page_config(page_title="نظام أمان الاتصال", page_icon="🔐")
st.title("🔐 نظام تسجيل الدخول وفحص أمان الاتصال")

# --- 2. بيانات البريد الإلكتروني للتنبيهات ---
SENDER_EMAIL = "ba3221635@gmail.com"
APP_PASSWORD = "phnfmmtpsaocdiqn"

# --- 3. تهيئة الذاكرة المؤقتة (Session State) ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0

if "block_until" not in st.session_state:
    st.session_state.block_until = 0

# --- 4. دالة جلب معلومات الموقع الجغرافي والـ IP ---
def get_user_location_info():
    try:
        # محاولة سحب الـ IP الحقيقي للزائر من هيدرز Streamlit
        headers = st.context.headers
        user_ip = headers.get("X-Forwarded-For", "").split(",")[0].strip()
        
        # إذا لم يكن موجوداً محلياً، نعتمد على الخدمة الخارجية لتحديد الـ IP تلقائياً
        if not user_ip:
            url = "http://ip-api.com/json/?fields=66846719"
        else:
            url = f"http://ip-api.com/json/{user_ip}?fields=66846719"
            
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return {}
    except:
        return {}

# --- 5. دالة إرسال الإيميل التلقائي ---
def send_email_alert(subject, body_text):
    try:
        msg = MIMEText(body_text, _charset="utf-8")
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL
        
        # الاتصال بسيرفر جيميل وإرسال التنبيه
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"خطأ في الإرسال: {e}")

# --- 6. نظام الحظر المؤقت (Brute-force protection) ---
current_time = time.time()
if current_time < st.session_state.block_until:
    remaining = int(st.session_state.block_until - current_time)
    st.error(f"🚨 تم حظر المحاولات بسبب كثرة الأخطاء. انتظر {remaining} ثوانٍ...")
    st.stop()

# --- 7. واجهة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.subheader("تسجيل الدخول للنظام")
    username = st.text_input("اسم المستخدم (Username)")
    password = st.text_input("كلمة المرور (Password)", type="password")
    
    if st.button("دخول"):
        # تجربة بيانات الدخول (يمكنك تعديل الباسورد هنا حسب رغبتك، مثلاً: admin / 1234)
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.failed_attempts = 0 # تصفير المحاولات الخاطئة
            
            # جلب معلومات الموقع والـ IP فور تسجيل الدخول الناجح
            loc_data = get_user_location_info()
            ip_val = loc_data.get('query', 'غير معروف')
            country_val = loc_data.get('country', 'غير معروف')
            city_val = loc_data.get('city', 'غير معروف')
            isp_val = loc_data.get('isp', 'غير معروف')
            
            # تجهيز محتوى الإيميل
            subject = "⚠️ تنبيه: تم تسجيل دخول ناجح للنظام"
            body = f"تم تسجيل الدخول بنجاح.\n\nتفاصيل الاتصال:\n- عنوان IP: {ip_val}\n- الدولة: {country_val}\n- المدينة: {city_val}\n- مزود الخدمة: {isp_val}"
            
            # إرسال التنبيه إلى بريدك
            send_email_alert(subject, body)
            
            st.success("تم تسجيل الدخول بنجاح وجاري إرسال التنبيه لصاحب الحساب!")
            time.sleep(1)
            st.rerun()
        else:
            st.session_state.failed_attempts += 1
            remaining_tries = 3 - st.session_state.failed_attempts
            
            if st.session_state.failed_attempts >= 3:
                # تفعيل حظر لمدة 10 ثوانٍ عند الوصول لـ 3 محاولات خاطئة
                st.session_state.block_until = time.time() + 10
                st.session_state.failed_attempts = 0
                st.error("🚨 تم تجاوز الحد الأقصى للمحاولات الخاطئة. تم حظرك لمدة 10 ثوانٍ!")
                st.rerun()
            else:
                st.error(f"❌ كلمة المرور أو اسم المستخدم غير صحيح. المحاولات المتبقية: {remaining_tries}")

else:
    # --- 8. الشاشة الداخلية بعد تسجيل الدخول الناجح ---
    st.success("🎉 أهلاً بك في لوحة التحكم الآمنة!")
    st.write("تم توثيق دخولك بنجاح وتأمين الجلسة.")
    
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
        st.rerun()
