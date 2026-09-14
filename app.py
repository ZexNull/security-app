import streamlit as st
import requests
import time
import smtplib
from email.mime.text import MIMEText

st.set_page_config(page_title="نظام أمان الاتصال", page_icon="🛡️")

st.title("🛡️ نظام تسجيل الدخول وفحص أمان الاتصال")

# =========================================================
# ⚙️ بيانات البريد الإلكتروني
# =========================================================
SENDER_EMAIL = "ba3221635@gmail.com"
APP_PASSWORD = "phnfmmtpsaocdiqn"

# إدارة حالة الجلسة
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "failed_attempts" not in st.session_state:
    st.session_state.failed_attempts = 0
if "block_until" not in st.session_state:
    st.session_state.block_until = 0

# دالة إرسال الإيميل المحدثة والمضمونة
def send_email_alert(subject, body_text):
    try:
        msg = MIMEText(body_text, _charset="utf-8")
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = SENDER_EMAIL

        # الاتصال عبر المنفذ 587 وتشفير TLS لضمان عدم الحجب
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=15)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, SENDER_EMAIL, msg.as_string())
        server.quit()
        st.success("📧 تم إرسال الإيميل بنجاح إلى صندوق البريد!")
        time.sleep(2)  # مهلة لضمان اكتمال الإرسال قبل تحديث الصفحة
    except Exception as e:
        st.error(f"❌ خطأ أثناء الإرسال: {e}")
        time.sleep(3)

# دالة جلب تفاصيل اتصال وموقع المستخدم
def get_user_location_info():
    try:
        data = requests.get("http://ip-api.com/json/?fields=66846719", timeout=5).json()
        return data
    except:
        return {}

# 1. نظام الحظر عند تكرار الأخطاء (10 ثوانٍ)
current_time = time.time()
if current_time < st.session_state.block_until:
    remaining = int(st.session_state.block_until - current_time)
    st.error(f"⛔ [BLOCKED] تم حظر المحاولات بسبب كثرة الأخطاء! انتظر {remaining} ثوانٍ...")
    st.stop()

# 2. شاشة تسجيل الدخول
if not st.session_state.logged_in:
    st.subheader("🔑 تسجيل الدخول للنظام")
    
    username = st.text_input("اسم المستخدم (Username):")
    password = st.text_input("كلمة المرور (Password):", type="password")
    
    if st.button("تسجيل الدخول"):
        user_info = get_user_location_info()
        user_ip = user_info.get("query", "N/A")
        country = user_info.get("country", "Unknown")
        city = user_info.get("city", "Unknown")
        isp = user_info.get("isp", "Unknown")
        
        # بيانات الحساب الافتراضية
        if username == "Ali" and password == "1234":
            st.info("جاري إرسال إيميل التنبيه...")
            alert_msg = f"تسجيل دخول جديد ناجح!\n\nالمستخدم: {username}\nIP: {user_ip}\nالموقع: {city}, {country}\nمزود الخدمة: {isp}"
            send_email_alert("🚨 تنبيه: تسجيل دخول جديد", alert_msg)
            
            st.session_state.logged_in = True
            st.session_state.failed_attempts = 0
            st.rerun()
        else:
            st.session_state.failed_attempts += 1
            remaining_attempts = 3 - st.session_state.failed_attempts
            
            if st.session_state.failed_attempts >= 3:
                st.session_state.block_until = time.time() + 10  # حظر 10 ثوانٍ
                st.session_state.failed_attempts = 0
                
                st.info("جاري إرسال إيميل التنبيه بالحظر...")
                block_msg = f"تنبيه: تم حظر محاولة دخول مشبوهة بعد 3 أخطاء!\n\nIP: {user_ip}\nالموقع: {city}, {country}\nمزود الخدمة: {isp}"
                send_email_alert("⚠️ تنبيه: حظر محاولة دخول مشبوهة", block_msg)
                
                st.error("⛔ تجاوزت حد المحاولات! تم حظرك لمدة 10 ثوانٍ.")
                st.rerun()
            else:
                st.error(f"بيانات الدخول خاطئة! المحاولات المتبقية: {remaining_attempts}")

# 3. الشاشة الرئيسية وفحص الـ VPN بعد تسجيل الدخول
else:
    st.success("مرحباً بك يا Ali 👋")
    st.write("---")
    
    info = get_user_location_info()
    ip = info.get("query", "N/A")
    isp = info.get("isp", "")
    org = info.get("org", "")
    country = info.get("country", "Unknown")
    is_hosting = info.get("hosting", False)

    # فحص الـ VPN والداتا سنتر
    suspicious_keywords = [
        "cloud", "google", "amazon", "digitalocean", "hosting", "proxy", "vpn",
        "zenlayer", "m247", "datacenter", "expressvpn", "nord", "servers", "network"
    ]
    keyword_match = any(word in isp.lower() or word in org.lower() for word in suspicious_keywords)
    is_vpn = keyword_match or is_hosting

    st.subheader("📊 تفاصيل الاتصال والأمان:")
    st.write(f"**عنوان الـ IP:** `{ip}`")
    st.write(f"**مزود الخدمة (ISP):** `{isp}`")
    st.write(f"**الدولة:** `{country}`")

    if is_vpn:
        st.error("⚠️ [ALERT] تم كشف اتصال مشبوه (VPN / Datacenter)!")
    else:
        st.success("✅ [OK] الاتصال آمن ومنزلي (Residential Connection).")

    st.write("---")
    if st.button("تسجيل الخروج"):
        st.session_state.logged_in = False
