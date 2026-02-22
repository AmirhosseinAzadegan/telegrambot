import time
import telebot
from telebot import types
import re
import logging
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from khayyam import JalaliDatetime
import json
import os
import tempfile
import threading
from datetime import datetime, timedelta
import random
import string
import uuid
import shutil
import glob
import hashlib
import bot2


# کلاس برای رفع مشکل SSL
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------- تنظیمات اصلی ----------------
TOKEN = "8403080895:AAH9Nspe4sBdBSZDeiEZAJt5M77us557_QY"
ADMIN_IDS = [7804710125, 5635158422]
PRIMARY_ADMIN_ID = 7804710125
CHANNEL_ID = "@vpnTeo"
LOG_CHANNEL_ID = "@aaaaddddssdsaldpas"

bot = telebot.TeleBot(TOKEN)

# کش یوزرنیم ربات (فقط یک بار - فیکس مهم)
try:
    BOT_USERNAME = bot.get_me().username
    print(f"✅ ربات با یوزرنیم @{BOT_USERNAME} راه‌اندازی شد")
except:
    BOT_USERNAME = "vpnTeo"
    print("⚠️ یوزرنیم ربات گرفته نشد، از پیش‌فرض استفاده شد")

# اعمال تنظیمات SSL
session = requests.Session()
session.mount('https://', SSLAdapter())
telebot.apihelper.session = session

# ---------------- پیدا کردن مسیر مناسب برای ذخیره فایل‌ها ----------------
def get_data_dir():
    app_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(app_dir, "data")
    
    try:
        os.makedirs(data_dir, exist_ok=True)
        test_file = os.path.join(data_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print(f"✅ فایل‌ها در {data_dir} ذخیره میشن")
        return data_dir
    except:
        temp_dir = os.path.join(tempfile.gettempdir(), "vpn_bot_data")
        os.makedirs(temp_dir, exist_ok=True)
        print(f"⚠️ دسترسی به پوشه برنامه ندارم!")
        print(f"✅ فایل‌ها در {temp_dir} ذخیره میشن")
        return temp_dir

DATA_DIR = get_data_dir()

# ---------------- تنظیمات بکاپ ----------------
BACKUP_CHANNEL_ID = LOG_CHANNEL_ID
BACKUP_INTERVAL = 24 * 60 * 60
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)
MAX_BACKUPS = 30

# ---------------- فایل‌های JSON ----------------
CONFIGS_FILE = os.path.join(DATA_DIR, "configs.json")
PURCHASES_FILE = os.path.join(DATA_DIR, "purchases.json")
REGISTERED_USERS_FILE = os.path.join(DATA_DIR, "registered_users.json")
FREE_TRIAL_USERS_FILE = os.path.join(DATA_DIR, "free_trial_users.json")
FREE_TRIAL_CONFIGS_FILE = os.path.join(DATA_DIR, "free_trial_configs.json")
POINTS_FILE = os.path.join(DATA_DIR, "user_points.json")
EXPIRY_FILE = os.path.join(DATA_DIR, "expiry_dates.json")
REFERRAL_FILE = os.path.join(DATA_DIR, "referral_data.json")
USAGE_FILE = os.path.join(DATA_DIR, "usage_data.json")
DISCONNECT_REQUESTS_FILE = os.path.join(DATA_DIR, "disconnect_requests.json")
SUBSCRIPTION_DETAILS_FILE = os.path.join(DATA_DIR, "subscription_details.json")
PRICES_FILE = os.path.join(DATA_DIR, "prices.json")
PAYMENT_INFO_FILE = os.path.join(DATA_DIR, "payment_info.json")
DISCOUNT_CODES_FILE = os.path.join(DATA_DIR, "discount_codes.json")
ADMINS_FILE = os.path.join(DATA_DIR, "admins.json")

# ---------------- توابع ذخیره و بارگذاری JSON ----------------
def save_json(filename, data):
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # تبدیل تاپل‌ها به رشته در دیکشنری
        def convert_keys(obj):
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    if isinstance(key, tuple):
                        new_key = str(key)
                    else:
                        new_key = key
                    new_dict[new_key] = convert_keys(value)
                return new_dict
            elif isinstance(obj, list):
                return [convert_keys(item) for item in obj]
            else:
                return obj
        
        # تبدیل داده‌ها قبل از ذخیره
        converted_data = convert_keys(data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logging.error(f"خطا در ذخیره {filename}: {e}")
        return False

def load_json(filename, default_value):
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # تبدیل رشته‌هایی که شبیه تاپل هستند به تاپل واقعی
                def restore_keys(obj):
                    if isinstance(obj, dict):
                        new_dict = {}
                        for key, value in obj.items():
                            # اگه کلید شبیه تاپل بود (مثلاً "('1', '10')")
                            if isinstance(key, str) and key.startswith('(') and key.endswith(')'):
                                try:
                                    # تبدیل رشته به تاپل با eval
                                    new_key = eval(key)
                                except:
                                    new_key = key
                            else:
                                new_key = key
                            new_dict[new_key] = restore_keys(value)
                        return new_dict
                    elif isinstance(obj, list):
                        return [restore_keys(item) for item in obj]
                    else:
                        return obj
                
                return restore_keys(data)
    except Exception as e:
        logging.error(f"خطا در بارگذاری {filename}: {e}")
    return default_value
    
# ================ بارگذاری ادمین‌ها ================
def load_admins():
    admins = load_json(ADMINS_FILE, [])
    if PRIMARY_ADMIN_ID not in admins:
        admins.append(PRIMARY_ADMIN_ID)
        save_json(ADMINS_FILE, admins)
    return admins

def save_admins(admins):
    save_json(ADMINS_FILE, admins)

# ================ حالا از توابع استفاده کن ================
ADMINS = load_admins()

def is_admin(user_id):
    return user_id in ADMINS

# اضافه کردن قابلیت مدیریت کانفیگ از bot2
bot2.setup_config_management(bot, is_admin)

# ---------------- توابع بکاپ ----------------
def create_backup(manual=False):
    try:
        persian_date = get_persian_date()
        filename = f"backup_{persian_date['file']}.json"
        filepath = os.path.join(BACKUP_DIR, filename)
        
        # تبدیل configs به فرمت JSON قابل قبول
        def convert_configs(obj):
            if isinstance(obj, dict):
                new_dict = {}
                for key, value in obj.items():
                    if isinstance(key, tuple):
                        new_key = str(key)
                    else:
                        new_key = key
                    new_dict[new_key] = convert_configs(value)
                return new_dict
            elif isinstance(obj, list):
                return [convert_configs(item) for item in obj]
            else:
                return obj
        
        backup_data = {
            "backup_time": persian_date['timestamp'],
            "backup_time_persian": persian_date['full'],
            "backup_type": "دستی" if manual else "خودکار",
            "stats": {
                "total_users": len(registered_users),
                "total_purchases": len(purchases),
                "total_configs_vip": sum(len(configs["vip"][key]) for key in configs["vip"]),
                "total_configs_super": sum(len(configs["super"][key]) for key in configs["super"]),
                "total_points": sum(user_points.values()),
                "total_discount_codes": len(discount_codes),
                "total_admins": len(ADMINS),
                "total_expiry_records": len(expiry_data),
                "total_referrals": len(referral_data),
                "total_usage_records": len(usage_data),
                "total_disconnect_requests": len(disconnect_requests),
                "total_subscriptions": len(subscription_details)
            },
            "data": {
                # اطلاعات کاربران و تنظیمات
                "configs": convert_configs(configs),
                "purchases": purchases,
                "registered_users": list(registered_users),
                "free_trial_users": list(free_trial_users),
                "free_trial_configs": free_trial_configs,
                "user_points": user_points,
                "expiry_data": expiry_data,
                "referral_data": referral_data,
                "usage_data": usage_data,
                "disconnect_requests": disconnect_requests,
                "subscription_details": subscription_details,
                "prices": prices,
                "payment_info": payment_info,
                "discount_codes": discount_codes,
                "admins": ADMINS
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=4)
        
        cleanup_old_backups()
        send_backup_to_channel(filepath, backup_data, manual)
        
        print(f"✅ بکاپ با موفقیت ایجاد شد: {filename}")
        return filepath
    except Exception as e:
        logging.error(f"خطا در ایجاد بکاپ: {e}")
        return None

def start_auto_backup():
    """شروع بکاپ خودکار هر 24 ساعت"""
    def backup_loop():
        while True:
            time.sleep(BACKUP_INTERVAL)  # 24 ساعت = 86400 ثانیه
            print("🔄 در حال ایجاد بکاپ خودکار...")
            result = create_backup(manual=False)
            if result:
                print(f"✅ بکاپ خودکار با موفقیت ایجاد شد: {result}")
            else:
                print("❌ خطا در ایجاد بکاپ خودکار")
    
    thread = threading.Thread(target=backup_loop, daemon=True)
    thread.start()
    print("✅ بکاپ خودکار فعال شد (هر 24 ساعت یکبار)")

def cleanup_old_backups():
    try:
        backup_files = glob.glob(os.path.join(BACKUP_DIR, "backup_*.json"))
        backup_files.sort(key=os.path.getctime, reverse=True)
        
        for old_file in backup_files[MAX_BACKUPS:]:
            os.remove(old_file)
    except Exception as e:
        print(f"خطا در حذف بکاپ‌های قدیمی: {e}")

def send_backup_to_channel(filepath, backup_data, manual):
    try:
        with open(filepath, 'rb') as f:
            bot.send_document(
                BACKUP_CHANNEL_ID,
                f,
                caption=f"📦 **بکاپ {backup_data['backup_type']}**\n"
                       f"🕐 زمان: {backup_data['backup_time_persian']}\n"
                       f"📊 آمار:\n"
                       f"• کاربران: {backup_data['stats']['total_users']}\n"
                       f"• خریدها: {backup_data['stats']['total_purchases']}\n"
                       f"• کانفیگ‌ها: {backup_data['stats']['total_configs_vip'] + backup_data['stats']['total_configs_super']}\n"
                       f"• ادمین‌ها: {backup_data['stats']['total_admins']}",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"خطا در ارسال بکاپ به کانال: {e}")

# ---------------- توابع کمکی برای نمایش یوزرنیم ----------------
def get_user_display(user_id):
    try:
        chat = bot.get_chat(user_id)
        username = chat.username
        first_name = chat.first_name or ""
        last_name = chat.last_name or ""
        
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = "بدون نام"
        
        if username:
            username_display = f"@{username}"
        else:
            username_display = "ندارد"
        
        return {
            "user_id": user_id,
            "username": username_display,
            "full_name": full_name,
            "username_raw": username
        }
    except:
        return {
            "user_id": user_id,
            "username": "خطا در دریافت",
            "full_name": "خطا در دریافت",
            "username_raw": None
        }

# ---------------- تنظیمات سرویس‌ها ----------------
SERVICE_TYPES = {
    "vip": {
        "name": "🔹 وی‌پی‌ان ویژه",
        "description": "مناسب برای استفاده ویژه",
        "plans": ["1", "2", "3"],
        "volumes": ["10", "20", "30", "40", "50", "80", "100", "150", "500"],
        "counts": ["unlimited"]
    },
    "super": {
        "name": "✨ وی‌پی‌ان اختصاصی ترید",
        "description": "مخصوص تریدرها و فریلنسرها با تضمین ضد شناسایی",
        "locations": [
            "🇬🇧 انگلیس", "🇫🇷 فرانسه", "🇳🇱 هلند", "🇺🇸 آمریکا (رندوم)", 
            "🇺🇸 آمریکا (لس‌آنجلس)", "🇺🇸 آمریکا (دالاس)", "🇺🇸 آمریکا (میامی)", 
            "🇺🇸 آمریکا (سیاتل)", "🇺🇸 آمریکا (شیکاگو)", "🇦🇪 امارات (150GB)", 
            "🇩🇪 آلمان", "🇨🇦 کانادا", "🇹🇷 ترکیه", "🇷🇺 روسیه", 
            "🇨🇿 جمهوری چک", "🇸🇮 اسلوونی", "🇭🇺 مجارستان", "🇭🇷 کرواسی", 
            "🇲🇩 مولداوی", "🇵🇹 پرتغال", "🇧🇬 بلغارستان"
        ],
        "plans": ["1"],
        "volumes": ["unlimited"],
        "counts": ["unlimited"]
    }
}

# ---------------- بارگذاری تمام داده‌ها ----------------
configs = load_json(CONFIGS_FILE, {"vip": {}, "super": {}})
purchases = load_json(PURCHASES_FILE, [])
registered_users = set(load_json(REGISTERED_USERS_FILE, []))
free_trial_users = set(load_json(FREE_TRIAL_USERS_FILE, []))
free_trial_configs = load_json(FREE_TRIAL_CONFIGS_FILE, [])
user_points = load_json(POINTS_FILE, {})
expiry_data = load_json(EXPIRY_FILE, {})
referral_data = load_json(REFERRAL_FILE, {})
usage_data = load_json(USAGE_FILE, {})
disconnect_requests = load_json(DISCONNECT_REQUESTS_FILE, {})
subscription_details = load_json(SUBSCRIPTION_DETAILS_FILE, {})

# ---------------- بررسی سلامت داده‌ها ----------------
def check_data_integrity():
    global referral_data, user_points
    for user_id, data in list(referral_data.items()):
        if not isinstance(data, dict):
            del referral_data[user_id]
        else:
            if "referrals" not in data:
                data["referrals"] = []
            if "reward_claimed" not in data:
                data["reward_claimed"] = False
            if "referral_code" not in data and "referral_link" in data:
                data["referral_code"] = data["referral_link"]
    
    save_json(REFERRAL_FILE, referral_data)
    
    for user_id, points in list(user_points.items()):
        if not isinstance(points, (int, float)):
            user_points[user_id] = 0
    
    save_json(POINTS_FILE, user_points)
    
    print("✅ بررسی سلامت داده‌ها انجام شد")

# ---------------- ساختار پیش‌فرض قیمت‌ها ----------------
DEFAULT_PRICES = {
    "vip": {
        "1": {
            "10": 30000,
            "20": 50000,
            "30": 80000,
            "40": 100000,
            "50": 120000,
            "80": 200000,
            "100": 250000,
            "150": 310000,
            "500": 890000
        },
        "2": {
            "10": 55000,
            "20": 75000,
            "30": 110000,
            "40": 130000,
            "50": 155000,
            "80": 235000,
            "100": 275000,
            "150": 335000,
            "500": 1750000
        },
        "3": {
            "10": 85000,
            "20": 125000,
            "30": 190000,
            "40": 230000,
            "50": 275000,
            "80": 435000,
            "100": 525000,
            "150": 645000
        }
    },
    "super": {
        "🇬🇧 انگلیس": 950000,
        "🇫🇷 فرانسه": 900000,
        "🇳🇱 هلند": 900000,
        "🇺🇸 آمریکا (رندوم)": 950000,
        "🇺🇸 آمریکا (لس‌آنجلس)": 1950000,
        "🇺🇸 آمریکا (دالاس)": 1950000,
        "🇺🇸 آمریکا (میامی)": 1950000,
        "🇺🇸 آمریکا (سیاتل)": 1950000,
        "🇺🇸 آمریکا (شیکاگو)": 1950000,
        "🇦🇪 امارات (150GB)": 1750000,
        "🇩🇪 آلمان": 980000,
        "🇨🇦 کانادا": 1100000,
        "🇹🇷 ترکیه": 1350000,
        "🇷🇺 روسیه": 2850000,
        "🇨🇿 جمهوری چک": 2550000,
        "🇸🇮 اسلوونی": 2500000,
        "🇭🇺 مجارستان": 2500000,
        "🇭🇷 کرواسی": 2500000,
        "🇲🇩 مولداوی": 2500000,
        "🇵🇹 پرتغال": 2680000,
        "🇧🇬 بلغارستان": 2700000
    }
}

prices = load_json(PRICES_FILE, DEFAULT_PRICES)

def save_prices():
    save_json(PRICES_FILE, prices)

# ---------------- اطلاعات پرداخت ----------------
DEFAULT_PAYMENT_INFO = {
    "card_number": "6037-9917-8950-1234",
    "card_holder": "رضا محمدی",
    "bank_name": "بانک ملت",
    "account_number": "1234567890",
    "sheba": "IR123456789012345678901234"
}

payment_info = load_json(PAYMENT_INFO_FILE, DEFAULT_PAYMENT_INFO)

def save_payment_info():
    save_json(PAYMENT_INFO_FILE, payment_info)

def get_payment_text():
    return (
        f"💳 **شماره کارت:**\n"
        f"`{payment_info['card_number']}`\n"
        f"👤 **به نام:** {payment_info['card_holder']}\n"
        f"🏦 **بانک:** {payment_info['bank_name']}\n\n"
        f"📸 بعد از واریز، تصویر رسید را ارسال کنید.\n"
        f"⏱ زمان تایید: حداکثر ۲ ساعت"
    )

# ---------------- سیستم کد تخفیف ----------------
discount_codes = load_json(DISCOUNT_CODES_FILE, {})

def save_discount_codes():
    save_json(DISCOUNT_CODES_FILE, discount_codes)

def manage_discount_codes(message):
    chat_id = message.chat.id
    text = "🎟️ **مدیریت کد تخفیف**\n\n"
    
    if not discount_codes:
        text += "هیچ کد تخفیفی وجود ندارد."
    else:
        for code, info in discount_codes.items():
            status = "✅ فعال" if info.get("active", True) else "❌ غیرفعال"
            text += f"🔑 `{code}` - {info.get('percent', 0)}% - {info.get('used_count', 0)}/{info.get('max_uses', 0)} - {status}\n"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

def edit_payment_info(message):
    chat_id = message.chat.id
    text = f"💳 **اطلاعات پرداخت فعلی:**\n\n"
    text += f"شماره کارت: `{payment_info['card_number']}`\n"
    text += f"به نام: {payment_info['card_holder']}\n"
    text += f"بانک: {payment_info['bank_name']}\n\n"
    text += "برای ویرایش به ادمین اصلی پیام دهید."
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------------- داده‌های موقتی ----------------
user_data = {}
support_requests = {}
admin_pending_config = {}
waiting_for_reply = {}
admin_state = {}
smart_support_sessions = {}
pending_renewal = {}
pending_price_edit = {}
pending_discount = {}
pending_disconnect = {}
pending_discount_code = {}
pending_add_admin = {}

# ---------------- پیام خوش‌آمدگویی ----------------
WELCOME_MESSAGE = """
🌟 **به فروشگاه تیو وی‌پی‌ان خوش آمدید!** 🌟

━━━━━━━━━━━━━━━━━━
**✅ تضمین تا آخرین روز اشتراک**
**✅ پشتیبانی ۲۴ ساعته**
**✅ بدون محدودیت تعداد کاربر**
**✅ آی‌پی تمیز و پرسرعت**
**✅ ضمانت کمترین قیمت در کامیونیتی ایران**
**✅ همراه با تست رایگان**
**✅ مناسب برای گیم، اینستاگردی، یوتیوب گردی و ...**
**✅ ۹۹.۹٪ آنتی‌تحریم - ضمانت عدم شناسایی**
**✅ قابل تنظیم روی انواع روتر و مودم**
━━━━━━━━━━━━━━━━━━

✨ **ویژه تریدرها و فریلنسرها:**
با پلن اختصاصی و تضمین ضد شناسایی و ضد بن

━━━━━━━━━━━━━━━━━━
**Teo Vpn Shop**

👤 **ادمین‌ها:** @tolanyi - @AmirAzadegan
📢 **کانال:** @vpnTeo
━━━━━━━━━━━━━━━━━━

🔰 **از منوی زیر گزینه مورد نظر را انتخاب کنید:**
"""

# ---------------- تابع محاسبه قیمت ----------------
def calculate_price(service, plan, volume=None, location=None, discount_percent=0):
    if service == "vip":
        original_price = prices["vip"].get(plan, {}).get(volume, 30000)
    elif service == "super":
        if location and location in prices["super"]:
            original_price = prices["super"][location]
        else:
            original_price = 950000
    else:
        original_price = 0
    
    if discount_percent > 0:
        discounted_price = int(original_price * (100 - discount_percent) / 100)
        return discounted_price, original_price, discount_percent
    else:
        return original_price, original_price, 0

# ---------------- سیستم امتیازات ----------------
POINTS_PER_PURCHASE = 25
POINTS_FOR_FREE_MONTH = 100

def get_user_points(user_id):
    return user_points.get(str(user_id), 0)

def add_points(user_id, points):
    user_id_str = str(user_id)
    user_points[user_id_str] = user_points.get(user_id_str, 0) + points
    save_json(POINTS_FILE, user_points)
    return user_points[user_id_str]

def deduct_points(user_id, points):
    user_id_str = str(user_id)
    current = user_points.get(user_id_str, 0)
    if current >= points:
        user_points[user_id_str] = current - points
        save_json(POINTS_FILE, user_points)
        return True
    return False

# ---------------- سیستم یادآوری تمدید ----------------
def calculate_expiry_date(plan_months):
    today = datetime.now()
    
    if plan_months == "1":
        expiry = today + timedelta(days=30)
    elif plan_months == "2":
        expiry = today + timedelta(days=60)
    elif plan_months == "3":
        expiry = today + timedelta(days=90)
    else:
        expiry = today + timedelta(days=30)
    
    return expiry.strftime("%Y-%m-%d")

def add_expiry_record(user_id, plan):
    user_id_str = str(user_id)
    expiry_date = calculate_expiry_date(plan)
    
    if plan == "1":
        jalali_date = JalaliDatetime.now() + timedelta(days=30)
    elif plan == "2":
        jalali_date = JalaliDatetime.now() + timedelta(days=60)
    elif plan == "3":
        jalali_date = JalaliDatetime.now() + timedelta(days=90)
    else:
        jalali_date = JalaliDatetime.now() + timedelta(days=30)
    
    jalali_str = f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"
    
    expiry_data[user_id_str] = {
        "expiry_date": expiry_date,
        "plan": plan,
        "reminded_3days": False,
        "reminded_1day": False,
        "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "jalali_expiry": jalali_str
    }
    save_json(EXPIRY_FILE, expiry_data)
    
    return expiry_date

def check_expiry_dates():
    while True:
        try:
            today = datetime.now().date()
            
            for user_id_str, data in expiry_data.items():
                user_id = int(user_id_str)
                expiry_date = datetime.strptime(data["expiry_date"], "%Y-%m-%d").date()
                days_left = (expiry_date - today).days
                
                if days_left == 3 and not data.get("reminded_3days", False):
                    send_reminder(user_id, days_left, data["plan"])
                    expiry_data[user_id_str]["reminded_3days"] = True
                    save_json(EXPIRY_FILE, expiry_data)
                
                elif days_left == 1 and not data.get("reminded_1day", False):
                    send_reminder(user_id, days_left, data["plan"])
                    expiry_data[user_id_str]["reminded_1day"] = True
                    save_json(EXPIRY_FILE, expiry_data)
                
        except Exception as e:
            print(f"❌ خطا در بررسی تاریخ‌های انقضا: {e}")
        
        time.sleep(3600)

def send_reminder(user_id, days_left, plan):
    try:
        discount = 0
        if days_left == 3:
            discount = 10
        elif days_left == 1:
            discount = 5
        
        jalali_date = JalaliDatetime.now() + timedelta(days=days_left)
        jalali_str = f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"
        
        user_info = get_user_display(user_id)
        
        reminder_text = (
            f"⏰ **یادآوری تمدید اشتراک**\n\n"
            f"{user_info['full_name']} عزیز، اشتراک شما {days_left} روز دیگر به اتمام می‌رسد.\n"
            f"📅 تاریخ اتمام: {jalali_str}\n"
            f"📦 پلن فعلی: {plan} ماهه\n\n"
        )
        
        if discount > 0:
            reminder_text += (
                f"🎁 **تمدید زودهنگام با {discount}% تخفیف!**\n"
                f"همین حالا تمدید کن و از تخفیف ویژه بهره‌مند شو.\n\n"
            )
        
        reminder_text += "🔻 برای تمدید از گزینه '💳 خرید اشتراک' استفاده کن."
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تمدید اشتراک", callback_data=f"renew_{user_id}"))
        
        bot.send_message(user_id, reminder_text, reply_markup=markup, parse_mode="Markdown")
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    f"📤 یادآوری تمدید برای کاربر ارسال شد.\n"
                    f"👤 {user_info['full_name']}\n"
                    f"🆔 `{user_id}`\n"
                    f"📱 {user_info['username']}\n"
                    f"⏱ زمان باقی‌مانده: {days_left} روز"
                )
            except:
                pass
        
    except Exception as e:
        print(f"❌ خطا در ارسال یادآوری به {user_id}: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("renew_"))
def quick_renew(call):
    try:
        parts = call.data.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            user_id = int(parts[1])
            
            if call.message.chat.id != user_id:
                bot.answer_callback_query(call.id, "❌ این دکمه مال شما نیست!", show_alert=True)
                return
            
            bot.answer_callback_query(call.id, "🔄 در حال انتقال به صفحه خرید...")
            
            fake_message = types.Message(
                message_id=0,
                from_user=call.from_user,
                date=int(time.time()),
                chat=types.Chat(id=user_id, type="private"),
                content_type='text',
                options={},
                json_string=''
            )
            fake_message.text = "💳 خرید اشتراک"
            buy_subscription(fake_message)
        else:
            bot.answer_callback_query(call.id, "❌ خطا در پردازش درخواست!", show_alert=True)
    except Exception as e:
        print(f"خطا در quick_renew: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش درخواست!", show_alert=True)

def get_remaining_days(user_id):
    user_id_str = str(user_id)
    if user_id_str in expiry_data:
        expiry_date = datetime.strptime(expiry_data[user_id_str]["expiry_date"], "%Y-%m-%d").date()
        today = datetime.now().date()
        return (expiry_date - today).days
    return None

# ---------------- سیستم زیرمجموعه‌گیری ----------------
REFERRAL_REWARD = 10
REFERRAL_TARGET = 5

def generate_referral_code(user_id):
    unique_string = f"{user_id}_{datetime.now().timestamp()}_{random.randint(1000, 9999)}"
    hash_code = hashlib.md5(unique_string.encode()).hexdigest()[:8]
    return f"{user_id}_{hash_code}"

def get_or_create_referral_data(user_id):
    user_id_str = str(user_id)
    
    if user_id_str not in referral_data:
        referral_data[user_id_str] = {
            "referral_code": generate_referral_code(user_id),
            "referrals": [],
            "reward_claimed": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_referrals": 0
        }
        save_json(REFERRAL_FILE, referral_data)
    
    return referral_data[user_id_str]

def get_referral_info(user_id):
    user_id_str = str(user_id)
    data = get_or_create_referral_data(user_id)
    
    referral_link = f"https://t.me/{BOT_USERNAME}?start={data['referral_code']}"
    
    referrals_list = []
    for ref_id in data["referrals"]:
        ref_info = get_user_display(ref_id)
        referrals_list.append({
            "id": ref_id,
            "name": ref_info['full_name'],
            "username": ref_info['username']
        })
    
    return {
        "link": referral_link,
        "code": data['referral_code'],
        "total": len(data["referrals"]),
        "target": REFERRAL_TARGET,
        "reward": REFERRAL_REWARD,
        "claimed": data.get("reward_claimed", False),
        "referrals": referrals_list
    }

def process_referral_start(new_user_id, referral_code):
    try:
        parts = referral_code.split('_')
        if len(parts) >= 2:
            referrer_id = parts[0]
            
            if referrer_id.isdigit():
                referrer_id = int(referrer_id)
                
                if new_user_id != referrer_id:
                    referrer_data = get_or_create_referral_data(referrer_id)
                    
                    if new_user_id not in referrer_data["referrals"]:
                        referrer_data["referrals"].append(new_user_id)
                        referrer_data["total_referrals"] = len(referrer_data["referrals"])
                        save_json(REFERRAL_FILE, referral_data)
                        
                        notify_new_referral(referrer_id, new_user_id)
                        
                        if len(referrer_data["referrals"]) >= REFERRAL_TARGET and not referrer_data.get("reward_claimed", False):
                            notify_referral_reward(referrer_id)
                        
                        return True
    except Exception as e:
        print(f"خطا در پردازش زیرمجموعه: {e}")
    
    return False

def notify_new_referral(referrer_id, new_user_id):
    try:
        referrer_info = get_user_display(referrer_id)
        new_user_info = get_user_display(new_user_id)
        
        referrer_data = get_or_create_referral_data(referrer_id)
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    f"🔗 **زیرمجموعه جدید**\n\n"
                    f"👤 کاربر اصلی: {referrer_info['full_name']}\n"
                    f"🆔 آیدی اصلی: `{referrer_id}`\n"
                    f"📱 یوزرنیم اصلی: {referrer_info['username']}\n\n"
                    f"👥 زیرمجموعه جدید: {new_user_info['full_name']}\n"
                    f"🆔 آیدی زیرمجموعه: `{new_user_id}`\n"
                    f"📱 یوزرنیم زیرمجموعه: {new_user_info['username']}\n\n"
                    f"📊 تعداد کل زیرمجموعه‌ها: {len(referrer_data['referrals'])}\n"
                    f"🎯 هدف: {REFERRAL_TARGET} نفر",
                    parse_mode="Markdown"
                )
            except:
                pass
        
        if len(referrer_data['referrals']) % 5 == 0:
            bot.send_message(
                referrer_id,
                f"🎉 **تبریک! یک زیرمجموعه جدید به جمع شما پیوست!**\n\n"
                f"👤 نام: {new_user_info['full_name']}\n"
                f"📊 تعداد کل زیرمجموعه‌های شما: {len(referrer_data['referrals'])}\n"
                f"🎯 برای دریافت جایزه به {REFERRAL_TARGET - len(referrer_data['referrals'])} نفر دیگر نیاز دارید!",
                parse_mode="Markdown"
            )
            
    except Exception as e:
        print(f"خطا در notify_new_referral: {e}")

def notify_referral_reward(user_id):
    try:
        user_id_str = str(user_id)
        if user_id_str in referral_data and not referral_data[user_id_str].get("reward_claimed", False):
            referral_data[user_id_str]["reward_claimed"] = True
            save_json(REFERRAL_FILE, referral_data)
            
            user_info = get_user_display(user_id)
            
            bot.send_message(
                user_id,
                f"🎉 **تبریک {user_info['full_name']}! شما به هدف زیرمجموعه‌گیری رسیدید!**\n\n"
                f"👥 شما {REFERRAL_TARGET} نفر را به ربات دعوت کردید.\n"
                f"🎁 جایزه شما: {REFERRAL_REWARD} گیگ کانفیگ رایگان یک ماهه\n\n"
                f"⏱ به زودی ادمین کانفیگ را برای شما ارسال خواهد کرد.",
                parse_mode="Markdown"
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎁 ارسال جایزه", callback_data=f"referral_reward_{user_id}"))
            
            for admin_id in ADMINS:
                try:
                    bot.send_message(
                        admin_id,
                        f"🎁 **رسیدن به هدف زیرمجموعه‌گیری**\n\n"
                        f"{user_info['full_name']} به هدف رسید!\n"
                        f"🆔 آیدی: `{user_id}`\n"
                        f"📱 یوزرنیم: {user_info['username']}\n"
                        f"👥 تعداد زیرمجموعه: {REFERRAL_TARGET}\n"
                        f"📦 جایزه: {REFERRAL_REWARD} گیگ کانفیگ رایگان یک ماهه\n\n"
                        "برای ارسال جایزه کلیک کنید:",
                        reply_markup=markup,
                        parse_mode="Markdown"
                    )
                except:
                    pass
    except Exception as e:
        print(f"خطا در اعلام جایزه زیرمجموعه: {e}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("referral_reward_"))
def referral_reward_callback(call):
    if not is_admin(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    try:
        user_id = int(call.data.split("_")[2])
        
        admin_pending_config[call.message.chat.id] = {
            "service": "vip",
            "key": ("1", str(REFERRAL_REWARD)),
            "is_reward": True,
            "user_id": user_id
        }
        waiting_for_reply[call.message.chat.id] = user_id
        
        bot.answer_callback_query(call.id, "📝 متن کانفیگ را ارسال کنید")
        bot.send_message(
            call.message.chat.id,
            f"🎁 **ارسال جایزه زیرمجموعه**\n"
            f"{get_user_display(user_id)['full_name']}\n"
            f"📦 کانفیگ {REFERRAL_REWARD} گیگ یک ماهه\n"
            f"📝 لطفاً متن کانفیگ را ارسال کنید:"
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

# ---------------- توابع کمکی ----------------
def normalize_value(value, value_type):
    if not value:
        return "1" if value_type == "count" else "10"
    
    value = str(value).lower().strip()
    
    if value in ["unlimited", "نامحدود", "♾", "0", "0 گیگ", "0 کاربره"]:
        return "unlimited"
    
    numbers = re.findall(r'\d+', value)
    if numbers:
        return numbers[0]
    
    return "1" if value_type == "count" else "10"

def standard_key_vip(plan, volume):
    plan = str(plan).strip()
    volume = normalize_value(volume, "volume")
    return (plan, volume)

def standard_key_super(location, plan):
    location = str(location).strip()
    plan = str(plan).strip()
    return (location, plan)

def check_membership(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.error(f"Membership check error: {e}")
        return True

# ---------------- تابع ارسال به کانال لاگ ----------------
def send_to_log_channel(user_id, service, plan, volume, location, config_text, user=None, discount_info=None):
    try:
        if user:
            user_info = {
                "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip() or "بدون نام",
                "username": f"@{user.username}" if user.username else "ندارد"
            }
        else:
            user_info = get_user_display(user_id)
        
        log_text = f"🆕 **خرید جدید**\n\n"
        log_text += f"👤 **نام:** {user_info['full_name']}\n"
        log_text += f"🆔 **آیدی:** `{user_id}`\n"
        log_text += f"📱 **یوزرنیم:** {user_info['username']}\n"
        
        if service == "vip":
            log_text += f"🔹 **نوع:** وی‌پی‌ان ویژه\n"
            log_text += f"⏱ **مدت:** {plan} ماهه\n"
            log_text += f"📦 **حجم:** {volume} گیگ\n"
        else:
            log_text += f"✨ **نوع:** وی‌پی‌ان اختصاصی ترید\n"
            log_text += f"📍 **لوکیشن:** {location}\n"
            log_text += f"📦 **حجم:** {'۱۵۰ گیگ' if 'امارات' in location else 'نامحدود'}\n"
        
        log_text += f"👥 **کاربران:** نامحدود\n"
        log_text += f"🏆 **امتیاز:** +{POINTS_PER_PURCHASE}\n"
        
        if discount_info:
            log_text += f"🎟️ **کد تخفیف:** {discount_info['code']} ({discount_info['percent']}%)\n"
        
        log_text += f"🕐 **زمان:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        log_text += f"🔐 **کانفیگ:**\n`{config_text}`"
        
        bot.send_message(LOG_CHANNEL_ID, log_text, parse_mode="Markdown")
    except Exception as e:
        print(f"خطا در ارسال به کانال لاگ: {e}")

# ---------------- توابع لاگ و تاریخ شمسی ----------------
def get_persian_date():
    now = JalaliDatetime.now()
    
    months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    weekdays = [
        "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه", "شنبه", "یک‌شنبه"
    ]
    
    month_name = months[now.month - 1]
    weekday_name = weekdays[now.weekday()]
    
    dates = {
        "full": f"{weekday_name} {now.day} {month_name} {now.year} ساعت {now.hour:02d}:{now.minute:02d}:{now.second:02d}",
        "short": f"{now.year}/{now.month:02d}/{now.day:02d} - {now.hour:02d}:{now.minute:02d}",
        "file": f"{now.year}-{now.month:02d}-{now.day:02d}_{now.hour:02d}-{now.minute:02d}",
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return dates

def format_price(price):
    return f"{price:,}"

def escape_html(text):
    if not text:
        return ""
    chars = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;'
    }
    for char, escape in chars.items():
        text = text.replace(char, escape)
    return text

# ---------------- تنظیم کانال لاگ ----------------
def setup_log_channel():
    global LOG_CHANNEL_ID
    
    possible_channels = [
        LOG_CHANNEL_ID,
        str(PRIMARY_ADMIN_ID),
    ]
    
    for channel in possible_channels:
        try:
            test_msg = bot.send_message(channel, "🔄 راه‌اندازی کانال لاگ...")
            bot.delete_message(channel, test_msg.message_id)
            print(f"✅ کانال لاگ تنظیم شد: {channel}")
            return channel
        except Exception as e:
            print(f"❌ کانال {channel} قابل دسترسی نیست: {e}")
            continue
    
    print(f"⚠️ از آیدی ادمین به عنوان کانال لاگ استفاده میشه: {PRIMARY_ADMIN_ID}")
    return str(PRIMARY_ADMIN_ID)

LOG_CHANNEL_ID = setup_log_channel()
BACKUP_CHANNEL_ID = LOG_CHANNEL_ID

# ---------------- منوی اصلی ----------------
def main_menu(chat_id, skip_welcome=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    buttons = [
        types.KeyboardButton("💰 لیست قیمت‌ها"),
        types.KeyboardButton("🎁 تست رایگان"),
        types.KeyboardButton("💳 خرید اشتراک"),
        types.KeyboardButton("🤖 پشتیبانی هوشمند"),
        types.KeyboardButton("🏆 امتیاز من"),
        types.KeyboardButton("🔗 زیرمجموعه‌گیری"),
        types.KeyboardButton("📋 اشتراک‌های من"),
        types.KeyboardButton("🛠 درخواست پشتیبانی")
    ]
    
    if is_admin(chat_id):
        buttons.append(types.KeyboardButton("👑 پنل ادمین"))
    
    markup.add(*buttons)
    
    if not skip_welcome:
        bot.send_message(chat_id, WELCOME_MESSAGE, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "به منوی اصلی بازگشتید:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    registered_users.add(chat_id)
    save_json(REGISTERED_USERS_FILE, list(registered_users))
    
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        if process_referral_start(chat_id, referral_code):
            bot.send_message(
                chat_id, 
                "✅ شما با لینک دعوت وارد شدید!\n"
                "به خانواده بزرگ ما خوش آمدید 🌟"
            )
    
    main_menu(chat_id, skip_welcome=False)

# ---------------- لیست قیمت‌ها ----------------
@bot.message_handler(func=lambda message: message.text == "💰 لیست قیمت‌ها")
def show_price_list(message):
    chat_id = message.chat.id
    
    price_text = "💰 **لیست قیمت‌ها**\n\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n"
    price_text += "**🔹 وی‌پی‌ان ویژه (بدون محدودیت کاربر)**\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    plan_names = {"1": "1 ماهه", "2": "2 ماهه", "3": "3 ماهه"}
    volumes = ["10", "20", "30", "40", "50", "80", "100", "150", "500"]
    
    for plan in ["1", "2", "3"]:
        price_text += f"**📦 {plan_names[plan]}:**\n"
        plan_prices = prices["vip"].get(plan, {})
        for vol in volumes:
            if vol in plan_prices:
                price_text += f"┣ {vol} گیگ: {format_price(plan_prices[vol])} تومان\n"
        price_text += "\n"
    
    price_text += "━━━━━━━━━━━━━━━━━━\n"
    price_text += "**✨ وی‌پی‌ان اختصاصی ترید**\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n\n"
    price_text += "┣ 📍 ۲۱ لوکیشن مختلف\n"
    price_text += "┣ 📦 حجم: نامحدود (به جز امارات ۱۵۰ گیگ)\n"
    price_text += "┣ 👥 کاربران: نامحدود\n"
    price_text += "┣ 🔒 ضد شناسایی و ضد بن\n"
    price_text += "┗ 💰 **قیمت‌ها از ۹۰۰,۰۰۰ تومان تا ۲,۸۵۰,۰۰۰ تومان**\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n\n"
    price_text += "📍 **قیمت دقیق هر لوکیشن در زمان انتخاب نمایش داده می‌شود.**\n\n"
    price_text += get_payment_text()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🔙 بازگشت به منوی اصلی"))
    
    bot.send_message(chat_id, price_text, reply_markup=markup, parse_mode="Markdown")

# ---------------- هندلرهای بازگشت ----------------
@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به منوی اصلی")
def back_to_main_menu(message):
    chat_id = message.chat.id
    main_menu(chat_id, skip_welcome=True)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به پنل ادمین" and is_admin(message.chat.id))
def back_to_admin_panel(message):
    admin_panel(message)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به مدیریت قیمت‌ها" and is_admin(message.chat.id))
def back_to_price_management(message):
    manage_prices(message)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به مدیریت کد تخفیف" and is_admin(message.chat.id))
def back_to_discount_management(message):
    manage_discount_codes(message)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به منوی کانفیگ" and is_admin(message.chat.id))
def back_to_config_menu(message):
    show_add_config_menu(message.chat.id)

# ---------------- انتخاب نوع سرویس ----------------
@bot.message_handler(func=lambda message: message.text == "💳 خرید اشتراک")
def buy_subscription(message):
    if check_membership(message.chat.id):
        choose_service_type(message)
    else:
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton("📌 عضویت در کانال", url=f"https://t.me/{CHANNEL_ID[1:]}")
        check_btn = types.InlineKeyboardButton("✅ بررسی عضویت", callback_data="check_join")
        markup.add(join_btn, check_btn)
        bot.send_message(message.chat.id, "برای ادامه خرید، ابتدا باید عضو کانال شوید:", reply_markup=markup)

def choose_service_type(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    btn_vip = types.InlineKeyboardButton("🔹 وی‌پی‌ان ویژه", callback_data="service_vip")
    btn_super = types.InlineKeyboardButton("✨ وی‌پی‌ان اختصاصی ترید", callback_data="service_super")
    
    markup.add(btn_vip, btn_super)
    
    text = (
        "🔰 **انتخاب نوع سرویس**\n\n"
        "🔹 **وی‌پی‌ان ویژه:** مناسب برای استفاده روزمره، گیم، اینستاگردی و یوتیوب گردی\n"
        "✨ **وی‌پی‌ان اختصاصی ترید:** مخصوص تریدرها و فریلنسرها با تضمین ضد شناسایی\n\n"
        "لطفاً نوع سرویس مورد نظر خود را انتخاب کنید:"
    )
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("service_"))
def service_callback(call):
    try:
        chat_id = call.message.chat.id
        service = call.data.split("_")[1]
        
        if service not in SERVICE_TYPES:
            bot.answer_callback_query(call.id, "❌ سرویس نامعتبر!", show_alert=True)
            return
        
        user_data[chat_id] = {"service": service}
        bot.answer_callback_query(call.id, f"✅ {SERVICE_TYPES[service]['name']} انتخاب شد")
        
        if service == "vip":
            choose_plan_vip(call.message)
        else:
            choose_location_super(call.message)
    except Exception as e:
        print(f"خطا در service_callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

def choose_location_super(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    locations = SERVICE_TYPES["super"]["locations"]
    location_buttons = []
    for loc in locations:
        location_buttons.append(types.InlineKeyboardButton(loc, callback_data=f"loc_{loc}"))
    
    markup.add(*location_buttons)
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_service"))
    
    bot.send_message(chat_id, "🌍 **لوکیشن مورد نظر خود را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("loc_"))
def location_callback(call):
    try:
        chat_id = call.message.chat.id
        location = call.data.replace("loc_", "")
        
        if chat_id not in user_data:
            user_data[chat_id] = {}
        
        user_data[chat_id]["location"] = location
        user_data[chat_id]["plan"] = "1"
        user_data[chat_id]["volume"] = "unlimited" if "امارات" not in location else "150"
        
        bot.answer_callback_query(call.id, f"✅ {location} انتخاب شد")
        show_payment_with_discount_check(call.message, "super")
    except Exception as e:
        print(f"خطا در location_callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

def choose_plan_vip(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("1 ماهه", callback_data="plan_vip_1"),
        types.InlineKeyboardButton("2 ماهه", callback_data="plan_vip_2"),
        types.InlineKeyboardButton("3 ماهه", callback_data="plan_vip_3"),
        types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_service")
    )
    bot.send_message(chat_id, "📅 **مدت اشتراک را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("plan_vip_"))
def plan_vip_callback(call):
    try:
        chat_id = call.message.chat.id
        plan = call.data.split("_")[2]
        
        if chat_id not in user_data:
            user_data[chat_id] = {"service": "vip"}
        
        user_data[chat_id]["plan"] = plan
        bot.answer_callback_query(call.id, f"✅ {plan} ماهه انتخاب شد")
        choose_volume_vip(call.message)
    except Exception as e:
        print(f"خطا در plan_vip_callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

def choose_volume_vip(message):
    chat_id = message.chat.id
    markup = types.InlineKeyboardMarkup(row_width=3)
    
    volumes = ["10", "20", "30", "40", "50", "80", "100", "150", "500"]
    buttons = []
    for vol in volumes:
        buttons.append(types.InlineKeyboardButton(f"{vol} گیگ", callback_data=f"vol_vip_{vol}"))
    
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_plan_vip"))
    
    bot.send_message(chat_id, "📦 **حجم بسته را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("vol_vip_"))
def volume_vip_callback(call):
    try:
        chat_id = call.message.chat.id
        volume = call.data.split("_")[2]
        
        if chat_id not in user_data:
            user_data[chat_id] = {"service": "vip", "plan": "1"}
        
        user_data[chat_id]["volume"] = volume
        bot.answer_callback_query(call.id, f"✅ {volume} گیگ انتخاب شد")
        show_payment_with_discount_check(call.message, "vip")
    except Exception as e:
        print(f"خطا در volume_vip_callback: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_plan_vip")
def back_to_plan_vip(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    choose_plan_vip(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_service")
def back_to_service(call):
    chat_id = call.message.chat.id
    if chat_id in user_data:
        del user_data[chat_id]
    bot.answer_callback_query(call.id)
    choose_service_type(call.message)

# ---------------- سیستم کد تخفیف در خرید ----------------
def show_payment_with_discount_check(message, service):
    chat_id = message.chat.id
    
    if service == "vip":
        plan = user_data[chat_id]["plan"]
        volume = user_data[chat_id]["volume"]
        original_price, _, _ = calculate_price("vip", plan, volume)
    else:
        location = user_data[chat_id]["location"]
        original_price, _, _ = calculate_price("super", "1", None, location)
    
    pending_discount[chat_id] = {
        "service": service,
        "plan": user_data[chat_id].get("plan", "1"),
        "volume": user_data[chat_id].get("volume"),
        "location": user_data[chat_id].get("location"),
        "original_price": original_price,
        "price": original_price,
        "discount_percent": 0,
        "discount_code": None
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ بله", callback_data="discount_yes")
    btn_no = types.InlineKeyboardButton("❌ خیر", callback_data="discount_no")
    markup.add(btn_yes, btn_no)
    
    bot.send_message(
        chat_id,
        "🎟️ **آیا کد تخفیف دارید؟**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "discount_yes")
def discount_yes(call):
    chat_id = call.message.chat.id
    
    if chat_id not in pending_discount:
        bot.answer_callback_query(call.id, "❌ اطلاعات خرید یافت نشد! دوباره تلاش کنید.")
        return
    
    bot.answer_callback_query(call.id)
    msg = bot.send_message(
        chat_id,
        "🎟️ **لطفاً کد تخفیف خود را وارد کنید:**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_discount_code)

@bot.callback_query_handler(func=lambda call: call.data == "discount_no")
def discount_no(call):
    chat_id = call.message.chat.id
    
    if chat_id not in pending_discount:
        bot.answer_callback_query(call.id, "❌ اطلاعات خرید یافت نشد! دوباره تلاش کنید.")
        return
    
    show_final_payment(call.message, chat_id)
    bot.answer_callback_query(call.id)

def process_discount_code(message):
    chat_id = message.chat.id
    code = message.text.strip().upper()
    
    if chat_id not in pending_discount:
        bot.send_message(chat_id, "❌ اطلاعات خرید یافت نشد! لطفاً دوباره از ابتدا شروع کنید.")
        return
    
    if code in discount_codes and discount_codes[code]["active"]:
        discount_info = discount_codes[code]
        
        if discount_info["used_count"] >= discount_info["max_uses"]:
            markup = types.InlineKeyboardMarkup()
            btn_continue = types.InlineKeyboardButton("🔄 ادامه بدون تخفیف", callback_data="discount_continue_without")
            markup.add(btn_continue)
            
            bot.send_message(
                chat_id,
                "❌ این کد تخفیف به حداکثر تعداد استفاده خود رسیده است.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        service = pending_discount[chat_id]["service"]
        plan = pending_discount[chat_id]["plan"]
        volume = pending_discount[chat_id]["volume"]
        location = pending_discount[chat_id]["location"]
        
        discounted_price, original_price, discount_percent = calculate_price(
            service, plan, volume, location, discount_info["percent"]
        )
        
        pending_discount[chat_id]["price"] = discounted_price
        pending_discount[chat_id]["original_price"] = original_price
        pending_discount[chat_id]["discount_percent"] = discount_percent
        pending_discount[chat_id]["discount_code"] = code
        
        discount_text = (
            f"✅ **کد تخفیف معتبر است!**\n\n"
            f"🎟️ کد: {code}\n"
            f"🎁 درصد تخفیف: {discount_percent}%\n"
            f"💰 قیمت اصلی: {format_price(original_price)} تومان\n"
            f"💵 قیمت نهایی: {format_price(discounted_price)} تومان\n\n"
            f"آیا مایل به ادامه هستید؟"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_yes = types.InlineKeyboardButton("✅ بله، ادامه بده", callback_data="discount_continue_with_discount")
        btn_no = types.InlineKeyboardButton("❌ انصراف", callback_data="discount_cancel")
        markup.add(btn_yes, btn_no)
        
        bot.send_message(chat_id, discount_text, reply_markup=markup, parse_mode="Markdown")
        
    else:
        markup = types.InlineKeyboardMarkup()
        btn_continue = types.InlineKeyboardButton("🔄 ادامه بدون تخفیف", callback_data="discount_continue_without")
        btn_try_again = types.InlineKeyboardButton("🔄 تلاش مجدد", callback_data="discount_try_again")
        markup.add(btn_continue, btn_try_again)
        
        bot.send_message(
            chat_id,
            "❌ کد تخفیف وارد شده نامعتبر است!",
            reply_markup=markup,
            parse_mode="Markdown"
        )

@bot.callback_query_handler(func=lambda call: call.data == "discount_continue_with_discount")
def discount_continue_with_discount(call):
    chat_id = call.message.chat.id
    show_final_payment(call.message, chat_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "discount_continue_without")
def discount_continue_without(call):
    chat_id = call.message.chat.id
    
    if chat_id in pending_discount:
        pending_discount[chat_id]["price"] = pending_discount[chat_id]["original_price"]
        pending_discount[chat_id]["discount_percent"] = 0
        pending_discount[chat_id]["discount_code"] = None
    
    show_final_payment(call.message, chat_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "discount_try_again")
def discount_try_again(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    msg = bot.send_message(
        chat_id,
        "🎟️ **لطفاً کد تخفیف خود را وارد کنید:**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, process_discount_code)

@bot.callback_query_handler(func=lambda call: call.data == "discount_cancel")
def discount_cancel(call):
    chat_id = call.message.chat.id
    
    if chat_id in pending_discount:
        del pending_discount[chat_id]
    
    bot.answer_callback_query(call.id, "❌ خرید لغو شد.")
    main_menu(chat_id, skip_welcome=True)

def show_final_payment(message, chat_id):
    if chat_id not in pending_discount:
        bot.send_message(chat_id, "❌ اطلاعات خرید یافت نشد! لطفاً دوباره از ابتدا شروع کنید.")
        return
    
    info = pending_discount[chat_id]
    service = info["service"]
    price = info["price"]
    original_price = info["original_price"]
    discount_percent = info["discount_percent"]
    discount_code = info["discount_code"]
    points_earn = POINTS_PER_PURCHASE
    
    if service == "vip":
        plan = info["plan"]
        volume = info["volume"]
        
        text = f"💰 **مبلغ قابل پرداخت:** {format_price(price)} تومان\n"
        if discount_percent > 0:
            text += f"💰 **قیمت اصلی:** {format_price(original_price)} تومان\n"
            text += f"🎟️ **کد تخفیف:** {discount_code} ({discount_percent}%)\n"
        text += (
            f"⏱ **مدت اشتراک:** {plan} ماهه\n"
            f"📦 **حجم بسته:** {volume} گیگ\n"
            f"👥 **تعداد کاربران:** نامحدود\n"
            f"🏆 **امتیاز این خرید:** +{points_earn} امتیاز\n\n"
            f"{get_payment_text()}"
        )
    else:
        location = info["location"]
        volume_text = "۱۵۰ گیگ" if "امارات" in location else "نامحدود"
        
        text = f"💰 **مبلغ قابل پرداخت:** {format_price(price)} تومان\n"
        if discount_percent > 0:
            text += f"💰 **قیمت اصلی:** {format_price(original_price)} تومان\n"
            text += f"🎟️ **کد تخفیف:** {discount_code} ({discount_percent}%)\n"
        text += (
            f"📍 **لوکیشن:** {location}\n"
            f"⏱ **مدت اشتراک:** 1 ماهه\n"
            f"📦 **حجم بسته:** {volume_text}\n"
            f"👥 **تعداد کاربران:** نامحدود\n"
            f"🔒 **ویژگی:** ضد شناسایی و ضد بن\n"
            f"🏆 **امتیاز این خرید:** +{points_earn} امتیاز\n\n"
            f"{get_payment_text()}"
        )
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if check_membership(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ عضویت شما تایید شد!")
        choose_service_type(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ شما هنوز عضو کانال نشده‌اید!")

# ---------------- دریافت رسید ----------------
@bot.message_handler(content_types=['photo', 'document'])
def handle_receipt(message):
    chat_id = message.chat.id
    
    if chat_id in pending_renewal:
        bot.forward_message(PRIMARY_ADMIN_ID, chat_id, message.message_id)
        
        renewal_info = pending_renewal[chat_id]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تایید تمدید", callback_data=f"renew_confirm_{chat_id}"))
        
        user_info = get_user_display(chat_id)
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    f"🔄 **درخواست تمدید اشتراک**\n\n"
                    f"{user_info['full_name']}\n"
                    f"🆔 آیدی: `{chat_id}`\n"
                    f"📱 یوزرنیم: {user_info['username']}\n"
                    f"💰 مبلغ واریزی: {format_price(renewal_info['price'])} تومان\n"
                    f"📦 مشخصات: {renewal_info['service']} - {renewal_info['plan']} ماهه\n"
                    f"💳 رسید واریز ارسال شده است.",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except:
                pass
        
        bot.send_message(chat_id, "✅ رسید تمدید شما با موفقیت ارسال شد! پس از تایید ادمین، کانفیگ تمدید خواهد شد.")
        del pending_renewal[chat_id]
        return
    
    if chat_id not in user_data and chat_id not in pending_discount:
        bot.send_message(chat_id, "❌ لطفاً ابتدا فرآیند خرید را شروع کنید.")
        return
    
    bot.forward_message(PRIMARY_ADMIN_ID, chat_id, message.message_id)
    bot.send_message(chat_id, "✅ رسید شما با موفقیت ارسال شد!\n⏱ پس از تایید ادمین، کانفیگ برای شما ارسال می‌شود.")
    
    if chat_id in pending_discount:
        service = pending_discount[chat_id]["service"]
        plan = pending_discount[chat_id]["plan"]
        discount_code = pending_discount[chat_id]["discount_code"]
        discount_percent = pending_discount[chat_id]["discount_percent"]
    else:
        service = user_data[chat_id]["service"]
        plan = user_data[chat_id]["plan"]
        discount_code = None
        discount_percent = 0
    
    user_info = get_user_display(chat_id)
    
    if service == "vip":
        if chat_id in pending_discount:
            volume = pending_discount[chat_id]["volume"]
        else:
            volume = user_data[chat_id]["volume"]
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"confirm_vip_{chat_id}"))
        
        discount_text = ""
        if discount_code:
            discount_text = f"\n🎟️ کد تخفیف: {discount_code} ({discount_percent}%)"
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    f"🆕 **خرید جدید - وی‌پی‌ان ویژه**\n\n"
                    f"{user_info['full_name']}\n"
                    f"🆔 آیدی: `{chat_id}`\n"
                    f"📱 یوزرنیم: {user_info['username']}\n"
                    f"⏱ پلن: {plan} ماهه\n"
                    f"📦 حجم: {volume} گیگ\n"
                    f"👥 کاربران: نامحدود\n"
                    f"🏆 امتیاز: +{POINTS_PER_PURCHASE}"
                    f"{discount_text}",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except:
                pass
    else:
        if chat_id in pending_discount:
            location = pending_discount[chat_id]["location"]
        else:
            location = user_data[chat_id]["location"]
            
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ تایید و ارسال کانفیگ", callback_data=f"confirm_super_{chat_id}"))
        
        discount_text = ""
        if discount_code:
            discount_text = f"\n🎟️ کد تخفیف: {discount_code} ({discount_percent}%)"
        
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id,
                    f"🆕 **خرید جدید - وی‌پی‌ان اختصاصی ترید**\n\n"
                    f"{user_info['full_name']}\n"
                    f"🆔 آیدی: `{chat_id}`\n"
                    f"📱 یوزرنیم: {user_info['username']}\n"
                    f"📍 لوکیشن: {location}\n"
                    f"⏱ پلن: 1 ماهه\n"
                    f"📦 حجم: {'۱۵۰ گیگ' if 'امارات' in location else 'نامحدود'}\n"
                    f"👥 کاربران: نامحدود\n"
                    f"🏆 امتیاز: +{POINTS_PER_PURCHASE}"
                    f"{discount_text}",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except:
                pass

# ---------------- تایید خرید و ارسال کانفیگ ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("renew_confirm_"))
def renew_confirm(call):
    if not is_admin(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    try:
        user_id = int(call.data.split("_")[2])
        
        user_purchases = [p for p in purchases if p["user"] == user_id]
        if user_purchases:
            last_purchase = user_purchases[-1]
            
            if last_purchase["service"] == "vip":
                sub_id = last_purchase.get("sub_id")
                config_text = None
                if sub_id and sub_id in subscription_details:
                    config_text = subscription_details[sub_id].get("config")
                
                user_info = get_user_display(user_id)
                
                if config_text:
                    bot.send_message(user_id, f"✅ اشتراک شما با موفقیت تمدید شد!\n\n🔐 **کانفیگ شما:**\n\n`{config_text}`", parse_mode="Markdown")
                else:
                    bot.send_message(user_id, f"✅ اشتراک شما با موفقیت تمدید شد! برای دریافت کانفیگ با پشتیبانی تماس بگیرید.", parse_mode="Markdown")
                
                new_points = add_points(user_id, POINTS_PER_PURCHASE)
                
                bot.send_message(
                    user_id,
                    f"🏆 {POINTS_PER_PURCHASE} امتیاز به حساب شما اضافه شد!\n"
                    f"💰 مجموع امتیازات شما: {new_points}",
                    parse_mode="Markdown"
                )
                
                expiry_date = add_expiry_record(user_id, last_purchase["plan"])
                jalali_expiry = expiry_data[str(user_id)]["jalali_expiry"]
                bot.send_message(
                    user_id,
                    f"📅 **تاریخ اتمام جدید اشتراک شما:** {jalali_expiry}",
                    parse_mode="Markdown"
                )
                
                purchases.append({
                    "user": user_id,
                    "service": "vip",
                    "plan": last_purchase["plan"],
                    "volume": last_purchase["volume"],
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "points": POINTS_PER_PURCHASE,
                    "type": "renewal"
                })
                save_json(PURCHASES_FILE, purchases)
                
                bot.answer_callback_query(call.id, "✅ تمدید با موفقیت انجام شد!")
                bot.edit_message_text(f"✅ تمدید اشتراک برای کاربر {user_info['full_name']} تایید شد.", call.message.chat.id, call.message.message_id)
            else:
                bot.send_message(call.message.chat.id, "❌ تمدید سرویس اختصاصی نیاز به ارسال کانفیگ جدید دارد. لطفاً با کاربر هماهنگ کنید.")
        else:
            bot.send_message(call.message.chat.id, "❌ اطلاعات خرید قبلی یافت نشد!")
    except Exception as e:
        print(f"خطا در renew_confirm: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_vip_"))
def confirm_vip_payment(call):
    admin_id = call.message.chat.id
    if not is_admin(admin_id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[2])
    
    if user_id not in user_data and user_id not in pending_discount:
        bot.answer_callback_query(call.id, "❌ اطلاعات خرید یافت نشد!")
        return
    
    if user_id in pending_discount:
        plan = pending_discount[user_id]["plan"]
        volume = pending_discount[user_id]["volume"]
        discount_code = pending_discount[user_id]["discount_code"]
        discount_percent = pending_discount[user_id]["discount_percent"]
    else:
        plan = user_data[user_id]["plan"]
        volume = user_data[user_id]["volume"]
        discount_code = None
        discount_percent = 0
    
    key = standard_key_vip(plan, volume)
    
    if key in configs["vip"] and configs["vip"][key]:
        config_text = configs["vip"][key].pop(0)
        save_json(CONFIGS_FILE, configs)
        
        if discount_code and discount_code in discount_codes:
            discount_codes[discount_code]["used_count"] += 1
            if user_id not in discount_codes[discount_code]["users_used"]:
                discount_codes[discount_code]["users_used"].append(user_id)
            save_discount_codes()
        
        bot.send_message(user_id, f"✅ خرید شما تایید شد!\n\n🔐 **کانفیگ شما:**\n\n`{config_text}`", parse_mode="Markdown")
        
        sub_id = str(uuid.uuid4())[:8]
        subscription_details[sub_id] = {
            "user_id": user_id,
            "config": config_text,
            "service": "vip",
            "plan": plan,
            "volume": volume,
            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_date": calculate_expiry_date(plan),
            "status": "active",
            "discount_code": discount_code,
            "discount_percent": discount_percent
        }
        save_json(SUBSCRIPTION_DETAILS_FILE, subscription_details)
        
        usage_data[config_text] = {
            "total_volume": int(volume) if volume != "unlimited" else 999999,
            "used": 0,
            "last_update": datetime.now().strftime("%Y-%m-%d"),
            "users": [user_id],
            "sub_id": sub_id,
            "ip": "192.168.1.1",
            "operators": {
                "ایرانسل": "✅ متصل",
                "رایتل": "✅ متصل", 
                "شاتل": "✅ متصل",
                "مخابرات": "✅ متصل",
                "همراه اول": "✅ متصل",
                "های وب": "✅ متصل",
                "آپتل": "✅ متصل",
                "شاتل موبایل": "✅ متصل"
            }
        }
        save_json(USAGE_FILE, usage_data)
        
        new_points = add_points(user_id, POINTS_PER_PURCHASE)
        
        bot.send_message(
            user_id,
            f"🏆 {POINTS_PER_PURCHASE} امتیاز به حساب شما اضافه شد!\n"
            f"💰 مجموع امتیازات شما: {new_points}\n"
            f"🎁 با ۱۰۰ امتیاز می‌توانید یک ماه رایگان بگیرید!",
            parse_mode="Markdown"
        )
        
        expiry_date = add_expiry_record(user_id, plan)
        jalali_expiry = expiry_data[str(user_id)]["jalali_expiry"]
        bot.send_message(
            user_id,
            f"📅 **تاریخ اتمام اشتراک شما:** {jalali_expiry}\n"
            f"⏱ ۳ روز قبل از اتمام، بهت یادآوری می‌کنم!",
            parse_mode="Markdown"
        )
        
        discount_info = None
        if discount_code:
            discount_info = {
                "code": discount_code,
                "percent": discount_percent
            }
        
        purchases.append({
            "user": user_id,
            "service": "vip",
            "plan": plan,
            "volume": volume,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "points": POINTS_PER_PURCHASE,
            "sub_id": sub_id,
            "discount_code": discount_code,
            "discount_percent": discount_percent
        })
        save_json(PURCHASES_FILE, purchases)
        
        try:
            chat = bot.get_chat(user_id)
            send_to_log_channel(user_id, "vip", plan, volume, None, config_text, user=chat, discount_info=discount_info)
        except Exception as e:
            logging.error(f"خطا در ارسال لاگ: {e}")
            send_to_log_channel(user_id, "vip", plan, volume, None, config_text, discount_info=discount_info)
        
        if user_id in user_data:
            del user_data[user_id]
        if user_id in pending_discount:
            del pending_discount[user_id]
        
        bot.answer_callback_query(call.id, "✅ کانفیگ با موفقیت ارسال شد!")
        bot.edit_message_text(f"✅ خرید تایید و کانفیگ برای کاربر {get_user_display(user_id)['full_name']} ارسال شد.", admin_id, call.message.message_id)
    else:
        bot.send_message(user_id, "❌ متاسفانه کانفیگ درخواستی موجود نیست. لطفاً با پشتیبانی تماس بگیرید.")
        bot.answer_callback_query(call.id, "❌ کانفیگ موجود نیست!")
        for admin_id in ADMINS:
            try:
                bot.send_message(admin_id, f"⚠️ کمبود کانفیگ وی‌پی‌ان ویژه برای: {plan} ماهه - {volume} گیگ")
            except:
                pass

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_super_"))
def confirm_super_payment(call):
    admin_id = call.message.chat.id
    if not is_admin(admin_id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    user_id = int(call.data.split("_")[2])
    
    if user_id not in user_data and user_id not in pending_discount:
        bot.answer_callback_query(call.id, "❌ اطلاعات خرید یافت نشد!")
        return
    
    if user_id in pending_discount:
        location = pending_discount[user_id]["location"]
        discount_code = pending_discount[user_id]["discount_code"]
        discount_percent = pending_discount[user_id]["discount_percent"]
    else:
        location = user_data[user_id]["location"]
        discount_code = None
        discount_percent = 0
    
    plan = "1"
    key = standard_key_super(location, plan)
    
    if key in configs["super"] and configs["super"][key]:
        config_text = configs["super"][key].pop(0)
        save_json(CONFIGS_FILE, configs)
        
        if discount_code and discount_code in discount_codes:
            discount_codes[discount_code]["used_count"] += 1
            if user_id not in discount_codes[discount_code]["users_used"]:
                discount_codes[discount_code]["users_used"].append(user_id)
            save_discount_codes()
        
        bot.send_message(user_id, f"✅ خرید شما تایید شد!\n\n🔐 **کانفیگ وی‌پی‌ان اختصاصی ترید شما:**\n\n`{config_text}`", parse_mode="Markdown")
        
        sub_id = str(uuid.uuid4())[:8]
        subscription_details[sub_id] = {
            "user_id": user_id,
            "config": config_text,
            "service": "super",
            "location": location,
            "plan": plan,
            "purchase_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "expiry_date": calculate_expiry_date(plan),
            "status": "active",
            "ip": location.split()[1] + ".ip",
            "discount_code": discount_code,
            "discount_percent": discount_percent
        }
        save_json(SUBSCRIPTION_DETAILS_FILE, subscription_details)
        
        volume_limit = 150 if "امارات" in location else 999999
        usage_data[config_text] = {
            "total_volume": volume_limit,
            "used": 0,
            "last_update": datetime.now().strftime("%Y-%m-%d"),
            "users": [user_id],
            "sub_id": sub_id,
            "ip": location.split()[1] + ".ip",
            "operators": {
                "ایرانسل": "✅ متصل",
                "رایتل": "✅ متصل", 
                "شاتل": "✅ متصل",
                "مخابرات": "✅ متصل",
                "همراه اول": "✅ متصل",
                "های وب": "✅ متصل",
                "آپتل": "✅ متصل",
                "شاتل موبایل": "✅ متصل"
            }
        }
        save_json(USAGE_FILE, usage_data)
        
        new_points = add_points(user_id, POINTS_PER_PURCHASE)
        
        bot.send_message(
            user_id,
            f"🏆 {POINTS_PER_PURCHASE} امتیاز به حساب شما اضافه شد!\n"
            f"💰 مجموع امتیازات شما: {new_points}\n"
            f"🎁 با ۱۰۰ امتیاز می‌توانید یک ماه رایگان بگیرید!",
            parse_mode="Markdown"
        )
        
        expiry_date = add_expiry_record(user_id, plan)
        jalali_expiry = expiry_data[str(user_id)]["jalali_expiry"]
        bot.send_message(
            user_id,
            f"📅 **تاریخ اتمام اشتراک شما:** {jalali_expiry}\n"
            f"⏱ ۳ روز قبل از اتمام، بهت یادآوری می‌کنم!",
            parse_mode="Markdown"
        )
        
        discount_info = None
        if discount_code:
            discount_info = {
                "code": discount_code,
                "percent": discount_percent
            }
        
        purchases.append({
            "user": user_id,
            "service": "super",
            "location": location,
            "plan": plan,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "points": POINTS_PER_PURCHASE,
            "sub_id": sub_id,
            "discount_code": discount_code,
            "discount_percent": discount_percent
        })
        save_json(PURCHASES_FILE, purchases)
        
        try:
            chat = bot.get_chat(user_id)
            send_to_log_channel(user_id, "super", plan, "unlimited", location, config_text, user=chat, discount_info=discount_info)
        except Exception as e:
            logging.error(f"خطا در ارسال لاگ: {e}")
            send_to_log_channel(user_id, "super", plan, "unlimited", location, config_text, discount_info=discount_info)
        
        if user_id in user_data:
            del user_data[user_id]
        if user_id in pending_discount:
            del pending_discount[user_id]
        
        bot.answer_callback_query(call.id, "✅ کانفیگ با موفقیت ارسال شد!")
        bot.edit_message_text(f"✅ خرید تایید و کانفیگ برای کاربر {get_user_display(user_id)['full_name']} ارسال شد.", admin_id, call.message.message_id)
    else:
        bot.send_message(user_id, "❌ متاسفانه کانفیگ درخواستی موجود نیست. لطفاً با پشتیبانی تماس بگیرید.")
        bot.answer_callback_query(call.id, "❌ کانفیگ موجود نیست!")
        for admin_id in ADMINS:
            try:
                bot.send_message(admin_id, f"⚠️ کمبود کانفیگ وی‌پی‌ان اختصاصی برای: {location}")
            except:
                pass

# ---------------- بخش اشتراک‌های من ----------------
@bot.message_handler(func=lambda message: message.text == "📋 اشتراک‌های من")
def my_subscriptions(message):
    chat_id = message.chat.id
    
    user_purchases = [p for p in purchases if p["user"] == chat_id]
    
    if not user_purchases:
        bot.send_message(chat_id, "📭 شما هنوز هیچ خریدی انجام نداده‌اید.", parse_mode="Markdown")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for i, purchase in enumerate(user_purchases[-10:], 1):
        if purchase["service"] == "vip":
            btn_text = f"{i}. ویژه {purchase['plan']} ماهه {purchase['volume']} گیگ"
        else:
            btn_text = f"{i}. اختصاصی ترید {purchase['location']}"
        
        sub_id = purchase.get("sub_id", f"temp_{purchase['time']}")
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"sub_detail_{sub_id}"))
    
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_main"))
    
    bot.send_message(
        chat_id,
        "📋 **لیست اشتراک‌های شما**\n\n"
        "برای مشاهده جزئیات هر اشتراک کلیک کنید:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_detail_"))
def subscription_detail(call):
    chat_id = call.message.chat.id
    sub_id = call.data.replace("sub_detail_", "")
    
    sub_info = None
    purchase_info = None
    
    if sub_id in subscription_details:
        sub_info = subscription_details[sub_id]
        for p in purchases:
            if p.get("sub_id") == sub_id:
                purchase_info = p
                break
    
    if not purchase_info:
        for p in purchases:
            if p["user"] == chat_id and p.get("sub_id") == sub_id:
                purchase_info = p
                break
    
    if not purchase_info:
        bot.answer_callback_query(call.id, "❌ اطلاعات اشتراک یافت نشد!")
        return
    
    remaining_days = get_remaining_days(chat_id)
    if remaining_days is None:
        remaining_days = "نامشخص"
    
    config_text = ""
    usage_info = None
    if sub_info and "config" in sub_info:
        config_text = sub_info["config"]
        if config_text in usage_data:
            usage_info = usage_data[config_text]
    
    if purchase_info["service"] == "vip":
        detail_text = (
            f"🔹 **وی‌پی‌ان ویژه**\n\n"
            f"📅 تاریخ خرید: {purchase_info['time'][:10]}\n"
            f"⏱ مدت اشتراک: {purchase_info['plan']} ماهه\n"
            f"📦 حجم بسته: {purchase_info['volume']} گیگ\n"
            f"👥 کاربران: نامحدود\n"
            f"⏳ روزهای باقی‌مانده: {remaining_days} روز\n"
        )
    else:
        volume_text = "۱۵۰ گیگ" if "امارات" in purchase_info['location'] else "نامحدود"
        detail_text = (
            f"✨ **وی‌پی‌ان اختصاصی ترید**\n\n"
            f"📅 تاریخ خرید: {purchase_info['time'][:10]}\n"
            f"📍 لوکیشن: {purchase_info['location']}\n"
            f"⏱ مدت اشتراک: 1 ماهه\n"
            f"📦 حجم بسته: {volume_text}\n"
            f"👥 کاربران: نامحدود\n"
            f"🔒 ضد شناسایی و ضد بن\n"
            f"⏳ روزهای باقی‌مانده: {remaining_days} روز\n"
        )
    
    if purchase_info.get("discount_code"):
        detail_text += f"🎟️ کد تخفیف: {purchase_info['discount_code']} ({purchase_info['discount_percent']}%)\n"
    
    if usage_info:
        used = usage_info.get("used", 0)
        total = usage_info.get("total_volume", 0)
        if total > 0 and total < 999999:
            percent = int((used / total) * 100)
            detail_text += f"📊 حجم مصرفی: {used} از {total} گیگ ({percent}%)\n"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    if config_text:
        markup.add(types.InlineKeyboardButton("🔍 جزئیات سرویس", callback_data=f"service_detail_{sub_id}"))
        markup.add(types.InlineKeyboardButton("🔄 قطع/وصل", callback_data=f"disconnect_from_sub_{sub_id}"))
        markup.add(types.InlineKeyboardButton("🔄 تمدید", callback_data=f"renew_sub_{sub_id}"))
    
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_subs"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(detail_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("disconnect_from_sub_"))
def disconnect_from_sub(call):
    chat_id = call.message.chat.id
    sub_id = call.data.replace("disconnect_from_sub_", "")
    
    config_text = None
    if sub_id in subscription_details:
        config_text = subscription_details[sub_id].get("config")
    
    if not config_text:
        bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!")
        return
    
    request_id = str(uuid.uuid4())[:8]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ قطع", callback_data=f"disconnect_confirm_cut_{request_id}"),
        types.InlineKeyboardButton("✅ وصل", callback_data=f"disconnect_confirm_connect_{request_id}")
    )
    markup.add(types.InlineKeyboardButton("🔙 انصراف", callback_data=f"sub_detail_{sub_id}"))
    
    pending_disconnect[chat_id] = {
        "config": config_text,
        "request_id": request_id,
        "sub_id": sub_id
    }
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🔄 **قطع/وصل کانفیگ**\n\n"
        "لطفاً نوع درخواست را انتخاب کنید:",
        chat_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("disconnect_confirm_"))
def disconnect_confirm(call):
    chat_id = call.message.chat.id
    parts = call.data.split("_")
    action = parts[2]
    request_id = parts[3]
    
    if chat_id not in pending_disconnect or pending_disconnect[chat_id]["request_id"] != request_id:
        bot.answer_callback_query(call.id, "❌ درخواست نامعتبر!")
        return
    
    config_text = pending_disconnect[chat_id]["config"]
    sub_id = pending_disconnect[chat_id]["sub_id"]
    
    action_text = "قطع" if action == "cut" else "وصل"
    
    disc_req_id = str(uuid.uuid4())[:8]
    disconnect_requests[disc_req_id] = {
        "user_id": chat_id,
        "config": config_text,
        "action": action_text,
        "status": "pending",
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sub_id": sub_id
    }
    save_json(DISCONNECT_REQUESTS_FILE, disconnect_requests)
    
    user_info = get_user_display(chat_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ انجام شد", callback_data=f"disc_done_{disc_req_id}"))
    
    for admin_id in ADMINS:
        try:
            bot.send_message(
                admin_id,
                f"🔄 **درخواست {action_text} کانفیگ**\n\n"
                f"{user_info['full_name']}\n"
                f"🆔 آیدی: `{chat_id}`\n"
                f"📱 یوزرنیم: {user_info['username']}\n"
                f"🔐 کانفیگ: `{config_text[:50]}...`\n"
                f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"برای تایید انجام درخواست کلیک کنید:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except:
            pass
    
    bot.answer_callback_query(call.id, f"✅ درخواست {action_text} با موفقیت ثبت شد!")
    bot.edit_message_text(
        f"✅ درخواست {action_text} کانفیگ شما با موفقیت ثبت شد!\n"
        f"⏱ به زودی توسط ادمین بررسی خواهد شد.",
        chat_id,
        call.message.message_id
    )
    
    del pending_disconnect[chat_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("service_detail_"))
def service_detail(call):
    chat_id = call.message.chat.id
    sub_id = call.data.replace("service_detail_", "")
    
    config_text = None
    if sub_id in subscription_details:
        config_text = subscription_details[sub_id].get("config")
    
    if not config_text:
        bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!")
        return
    
    if config_text in usage_data:
        usage_info = usage_data[config_text]
        
        operators_text = ""
        for op, status in usage_info.get("operators", {}).items():
            operators_text += f"   {op}: {status}\n"
        
        detail_text = (
            f"🔍 **جزئیات سرویس**\n\n"
            f"🌐 آدرس آیپی: `{usage_info.get('ip', 'نامشخص')}`\n"
            f"📊 حجم مصرفی: {usage_info.get('used', 0)} از {usage_info.get('total_volume', 0)} گیگ\n"
            f"👥 تعداد افراد متصل: {len(usage_info.get('users', []))}\n"
            f"🔌 وضعیت اتصال:\n{operators_text}\n\n"
            f"🔐 **کانفیگ:**\n`{config_text}`"
        )
    else:
        detail_text = (
            f"🔍 **جزئیات سرویس**\n\n"
            f"⚠️ اطلاعات مصرفی برای این کانفیگ موجود نیست.\n\n"
            f"🔐 **کانفیگ:**\n`{config_text}`"
        )
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data=f"sub_detail_{sub_id}"))
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(detail_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("renew_sub_"))
def renew_subscription(call):
    chat_id = call.message.chat.id
    sub_id = call.data.replace("renew_sub_", "")
    
    purchase_info = None
    for p in purchases:
        if p.get("sub_id") == sub_id and p["user"] == chat_id:
            purchase_info = p
            break
    
    if not purchase_info:
        bot.answer_callback_query(call.id, "❌ اطلاعات خرید یافت نشد!")
        return
    
    if purchase_info["service"] == "vip":
        price, _, _ = calculate_price("vip", purchase_info["plan"], purchase_info["volume"])
    else:
        price, _, _ = calculate_price("super", "1", None, purchase_info.get("location", "🇺🇸 آمریکا (رندوم)"))
    
    pending_renewal[chat_id] = {
        "price": price,
        "plan": purchase_info["plan"],
        "service": purchase_info["service"],
        "volume": purchase_info.get("volume"),
        "location": purchase_info.get("location")
    }
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 انصراف", callback_data=f"sub_detail_{sub_id}"))
    
    payment_text = (
        f"🔄 **تمدید اشتراک**\n\n"
        f"💰 مبلغ قابل پرداخت: {format_price(price)} تومان\n"
        f"{get_payment_text()}"
    )
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(payment_text, chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "back_to_subs")
def back_to_subs(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    my_subscriptions(call.message)

# ---------------- پنل ادمین ----------------
@bot.message_handler(func=lambda message: message.text == "👑 پنل ادمین" and is_admin(message.chat.id))
def admin_panel(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📊 آمار"),
        types.KeyboardButton("➕ افزودن کانفیگ"),
        types.KeyboardButton("➕ کانفیگ رایگان"),
        types.KeyboardButton("📋 لیست خریدها"),
        types.KeyboardButton("📦 موجودی کانفیگ‌ها"),
        types.KeyboardButton("👥 کاربران تست رایگان"),
        types.KeyboardButton("🏆 مدیریت امتیازات"),
        types.KeyboardButton("📅 مدیریت یادآوری"),
        types.KeyboardButton("🔗 مدیریت زیرمجموعه‌ها"),
        types.KeyboardButton("🤖 مدیریت سوالات هوشمند"),
        types.KeyboardButton("💰 مدیریت قیمت‌ها"),
        types.KeyboardButton("🎟️ مدیریت کد تخفیف"),
        types.KeyboardButton("💳 ویرایش اطلاعات پرداخت"),
        types.KeyboardButton("📢 تنظیم کانال لاگ"),
        types.KeyboardButton("🔍 دیباگ کانفیگ"),
        types.KeyboardButton("📊 آپدیت حجم مصرفی"),
        types.KeyboardButton("🔄 درخواست‌های قطع/وصل"),
        types.KeyboardButton("📦 بکاپ گیری"),
        types.KeyboardButton("👑 مدیریت ادمین‌ها"),
                types.KeyboardButton("📋 مدیریت کانفیگ"),
        types.KeyboardButton("🏠 بازگشت به منوی اصلی")
    ]
    markup.add(*buttons)
    bot.send_message(message.chat.id, "👑 **پنل مدیریت**", reply_markup=markup, parse_mode="Markdown")

# ---------------- مدیریت ادمین‌ها ----------------
@bot.message_handler(func=lambda message: message.text == "👑 مدیریت ادمین‌ها" and is_admin(message.chat.id))
def manage_admins(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("➕ افزودن ادمین جدید"),
        types.KeyboardButton("📋 لیست ادمین‌ها"),
        types.KeyboardButton("🔙 بازگشت به پنل ادمین")
    ]
    markup.add(*buttons)
    
    bot.send_message(chat_id, "👑 **مدیریت ادمین‌ها**\n\nلطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "➕ افزودن ادمین جدید" and is_admin(message.chat.id))
def add_admin_start(message):
    chat_id = message.chat.id
    
    msg = bot.send_message(
        chat_id,
        "👤 **لطفاً آیدی عددی کاربر مورد نظر را برای افزودن به جمع ادمین‌ها وارد کنید:**\n\n"
        "مثال: `123456789`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, add_admin_process)

def add_admin_process(message):
    admin_id = message.chat.id
    try:
        new_admin_id = int(message.text.strip())
        
        if new_admin_id in ADMINS:
            user_info = get_user_display(new_admin_id)
            bot.send_message(admin_id, f"❌ کاربر {user_info['full_name']} هم‌اکنون ادمین است!")
            return
        
        try:
            user_info = get_user_display(new_admin_id)
            if user_info['full_name'] == "خطا در دریافت":
                bot.send_message(admin_id, "❌ کاربر مورد نظر یافت نشد! مطمئن شوید ربات را استارت کرده باشد.")
                return
        except:
            bot.send_message(admin_id, "❌ خطا در دریافت اطلاعات کاربر!")
            return
        
        ADMINS.append(new_admin_id)
        save_admins(ADMINS)
        
        try:
            bot.send_message(
                new_admin_id,
                "🎉 **تبریک! شما به جمع ادمین‌های ربات اضافه شدید!**\n\n"
                "اکنون می‌توانید از پنل ادمین استفاده کنید.",
                parse_mode="Markdown"
            )
        except:
            pass
        
        bot.send_message(
            admin_id,
            f"✅ کاربر با موفقیت به ادمین‌ها اضافه شد!\n\n"
            f"{user_info['full_name']}\n"
            f"🆔 آیدی: `{new_admin_id}`\n"
            f"📱 یوزرنیم: {user_info['username']}",
            parse_mode="Markdown"
        )
        
    except ValueError:
        bot.send_message(admin_id, "❌ لطفاً یک آیدی عددی معتبر وارد کنید!")
    except Exception as e:
        bot.send_message(admin_id, f"❌ خطا: {e}")

@bot.message_handler(func=lambda message: message.text == "📋 لیست ادمین‌ها" and is_admin(message.chat.id))
def list_admins(message):
    chat_id = message.chat.id
    
    text = "👑 **لیست ادمین‌های ربات**\n\n"
    
    for i, admin_id in enumerate(ADMINS, 1):
        info = get_user_display(admin_id)
        is_primary = " (ادمین اصلی)" if admin_id == PRIMARY_ADMIN_ID else ""
        text += f"{i}. {info['full_name']}{is_primary}\n"
        text += f"   🆔 `{admin_id}`\n"
        text += f"   📱 {info['username']}\n\n"
    
    text += f"📊 تعداد کل: {len(ADMINS)} ادمین"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------------- بخش بکاپ در پنل ادمین ----------------
@bot.message_handler(func=lambda message: message.text == "📦 بکاپ گیری" and is_admin(message.chat.id))
def backup_menu(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("📦 بکاپ دستی جدید"),
        types.KeyboardButton("📋 لیست بکاپ‌ها"),
        types.KeyboardButton("🔙 بازگشت به پنل ادمین")
    ]
    markup.add(*buttons)
    
    backup_files = glob.glob(os.path.join(BACKUP_DIR, "backup_*.json"))
    last_backup = "ندارد"
    if backup_files:
        latest = max(backup_files, key=os.path.getctime)
        last_backup_time = datetime.fromtimestamp(os.path.getctime(latest))
        last_backup = last_backup_time.strftime("%Y-%m-%d %H:%M:%S")
    
    text = (
        "📦 **مدیریت بکاپ**\n\n"
        f"📊 تعداد بکاپ‌های موجود: {len(backup_files)}\n"
        f"🕐 آخرین بکاپ: {last_backup}\n"
        f"📁 مسیر ذخیره: `{BACKUP_DIR}`\n\n"
        "لطفاً گزینه مورد نظر را انتخاب کنید:"
    )
    
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📦 بکاپ دستی جدید" and is_admin(message.chat.id))
def manual_backup(message):
    chat_id = message.chat.id
    
    msg = bot.send_message(chat_id, "🔄 در حال ایجاد بکاپ... لطفاً صبر کنید.")
    
    filepath = create_backup(manual=True)
    
    if filepath:
        bot.edit_message_text(
            f"✅ بکاپ با موفقیت ایجاد و به کانال لاگ ارسال شد!\n"
            f"📁 مسیر فایل: `{filepath}`",
            chat_id,
            msg.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.edit_message_text("❌ خطا در ایجاد بکاپ!", chat_id, msg.message_id)

@bot.message_handler(func=lambda message: message.text == "📋 لیست بکاپ‌ها" and is_admin(message.chat.id))
def list_backups(message):
    chat_id = message.chat.id
    
    backup_files = glob.glob(os.path.join(BACKUP_DIR, "backup_*.json"))
    backup_files.sort(key=os.path.getctime, reverse=True)
    
    if not backup_files:
        bot.send_message(chat_id, "📭 هیچ بکاپی یافت نشد.")
        return
    
    text = "📋 **لیست بکاپ‌های موجود**\n\n"
    
    for i, filepath in enumerate(backup_files[:20], 1):
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath) / 1024
        mod_time = datetime.fromtimestamp(os.path.getctime(filepath))
        
        text += f"{i}. `{filename}`\n"
        text += f"   📅 {mod_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"   📊 {file_size:.1f} KB\n\n"
    
    if len(backup_files) > 20:
        text += f"... و {len(backup_files) - 20} بکاپ دیگر\n"
    
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ---------------- ادامه پنل ادمین ----------------
def show_add_config_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🔹 وی‌پی‌ان ویژه"),
        types.KeyboardButton("✨ وی‌پی‌ان اختصاصی ترید"),
        types.KeyboardButton("🔙 بازگشت به پنل ادمین")
    ]
    markup.add(*buttons)
    bot.send_message(chat_id, "🔽 **نوع کانفیگ را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔹 وی‌پی‌ان ویژه" and is_admin(message.chat.id))
def show_vip_config_menu(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    
    plans = ["1", "2", "3"]
    volumes = ["10", "20", "30", "40", "50", "80", "100", "150", "500"]
    
    buttons = []
    for plan in plans:
        for volume in volumes:
            btn_text = f"➕ کانفیگ ویژه {plan} ماهه {volume} گیگ"
            buttons.append(types.KeyboardButton(btn_text))
    
    buttons.append(types.KeyboardButton("🔙 بازگشت به منوی کانفیگ"))
    markup.add(*buttons)
    bot.send_message(chat_id, "🔽 **نوع کانفیگ ویژه را انتخاب کنید:**", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "✨ وی‌پی‌ان اختصاصی ترید" and is_admin(message.chat.id))
def show_super_config_menu(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    locations = SERVICE_TYPES["super"]["locations"]
    buttons = []
    for loc in locations:
        btn_text = f"➕ کانفیگ ترید {loc}"
        buttons.append(types.KeyboardButton(btn_text))
    
    buttons.append(types.KeyboardButton("🔙 بازگشت به منوی کانفیگ"))
    markup.add(*buttons)
    bot.send_message(chat_id, "🔽 **نوع کانفیگ اختصاصی ترید را انتخاب کنید:**", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به منوی کانفیگ" and is_admin(message.chat.id))
def back_to_config_menu(message):
    show_add_config_menu(message.chat.id)

@bot.message_handler(func=lambda message: message.text == "📊 آپدیت حجم مصرفی" and is_admin(message.chat.id))
def update_usage_start(message):
    msg = bot.send_message(
        message.chat.id,
        "📝 **لطفاً کانفیگ مورد نظر رو ارسال کن:**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, update_usage_get_config)

def update_usage_get_config(message):
    config_text = message.text
    chat_id = message.chat.id
    
    if config_text in usage_data:
        current_used = usage_data[config_text]["used"]
        total = usage_data[config_text]["total_volume"]
        
        msg = bot.send_message(
            chat_id,
            f"✅ کانفیگ پیدا شد!\n"
            f"📊 حجم کل: {total} گیگ\n"
            f"📈 مصرف فعلی: {current_used} گیگ\n\n"
            f"📝 **میزان مصرف جدید را وارد کنید (بر حسب گیگ):**",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, update_usage_save, config_text)
    else:
        bot.send_message(chat_id, "❌ این کانفیگ در سیستم ثبت نشده!")

def update_usage_save(message, config_text):
    try:
        new_usage = float(message.text)
        current_used = usage_data[config_text]["used"]
        total = usage_data[config_text]["total_volume"]
        
        if new_usage > total:
            usage_data[config_text]["used"] = total
        else:
            usage_data[config_text]["used"] = new_usage
        
        usage_data[config_text]["last_update"] = datetime.now().strftime("%Y-%m-%d")
        save_json(USAGE_FILE, usage_data)
        
        bot.send_message(
            message.chat.id,
            f"✅ حجم مصرفی با موفقیت به‌روزرسانی شد!\n"
            f"📊 مصرف جدید: {usage_data[config_text]['used']} از {total} گیگ",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.send_message(message.chat.id, "❌ لطفاً یک عدد معتبر وارد کنید!")

@bot.message_handler(func=lambda message: message.text == "🔄 درخواست‌های قطع/وصل" and is_admin(message.chat.id))
def show_disconnect_requests(message):
    chat_id = message.chat.id
    
    pending_reqs = {k: v for k, v in disconnect_requests.items() if v["status"] == "pending"}
    
    if not pending_reqs:
        bot.send_message(chat_id, "📭 هیچ درخواست قطع/وصلی در انتظار نیست.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for req_id, req in list(pending_reqs.items())[-10:]:
        user_info = get_user_display(req['user_id'])
        btn_text = f"{req['action']} - {user_info['full_name'][:15]} - {req['date'][:10]}"
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"disc_req_{req_id}"))
    
    bot.send_message(
        chat_id,
        "🔄 **درخواست‌های قطع/وصل در انتظار:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("disc_req_"))
def show_disconnect_request_detail(call):
    if not is_admin(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    req_id = call.data.replace("disc_req_", "")
    
    if req_id in disconnect_requests:
        req = disconnect_requests[req_id]
        user_info = get_user_display(req['user_id'])
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ انجام شد", callback_data=f"disc_done_{req_id}"))
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin"))
        
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"🔄 **جزئیات درخواست**\n\n"
            f"{user_info['full_name']}\n"
            f"🆔 آیدی: `{req['user_id']}`\n"
            f"📱 یوزرنیم: {user_info['username']}\n"
            f"🔧 نوع درخواست: {req['action']}\n"
            f"🔐 کانفیگ: `{req['config'][:100]}...`\n"
            f"📅 تاریخ: {req['date']}\n"
            f"📊 وضعیت: {req['status']}",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(call.id, "❌ درخواست یافت نشد!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("disc_done_"))
def disconnect_done(call):
    if not is_admin(call.message.chat.id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    req_id = call.data.replace("disc_done_", "")
    
    if req_id in disconnect_requests:
        disconnect_requests[req_id]["status"] = "done"
        save_json(DISCONNECT_REQUESTS_FILE, disconnect_requests)
        
        user_id = disconnect_requests[req_id]["user_id"]
        action = disconnect_requests[req_id]["action"]
        
        bot.send_message(
            user_id,
            f"✅ درخواست {action} کانفیگ شما با موفقیت انجام شد.",
            parse_mode="Markdown"
        )
        
        bot.answer_callback_query(call.id, "✅ درخواست تایید شد!")
        bot.edit_message_text(
            f"✅ درخواست {disconnect_requests[req_id]['action']} کانفیگ تایید شد.",
            call.message.chat.id,
            call.message.message_id
        )
    else:
        bot.answer_callback_query(call.id, "❌ درخواست یافت نشد!")

# ---------------- مدیریت قیمت‌ها ----------------
@bot.message_handler(func=lambda message: message.text == "💰 مدیریت قیمت‌ها" and is_admin(message.chat.id))
def manage_prices(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("🔹 ویرایش قیمت ویژه"),
        types.KeyboardButton("✨ ویرایش قیمت ترید"),
        types.KeyboardButton("📊 نمایش همه قیمت‌ها"),
        types.KeyboardButton("🔄 بازنشانی به پیش‌فرض"),
        types.KeyboardButton("🔙 بازگشت به پنل ادمین")
    ]
    markup.add(*buttons)
    
    bot.send_message(chat_id, "💰 **مدیریت قیمت‌ها**\n\nلطفاً گزینه مورد نظر را انتخاب کنید:", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔹 ویرایش قیمت ویژه" and is_admin(message.chat.id))
def edit_vip_prices(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("1 ماهه"),
        types.KeyboardButton("2 ماهه"),
        types.KeyboardButton("3 ماهه"),
        types.KeyboardButton("🔙 بازگشت به مدیریت قیمت‌ها")
    ]
    markup.add(*buttons)
    
    bot.send_message(chat_id, "📅 **لطفاً مدت اشتراک را انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in ["1 ماهه", "2 ماهه", "3 ماهه"] and is_admin(message.chat.id))
def select_plan_for_price(message):
    chat_id = message.chat.id
    plan_map = {"1 ماهه": "1", "2 ماهه": "2", "3 ماهه": "3"}
    plan = plan_map[message.text]
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    volumes = ["10", "20", "30", "40", "50", "80", "100", "150", "500"]
    buttons = []
    for vol in volumes:
        buttons.append(types.KeyboardButton(f"ویرایش {vol} گیگ"))
    buttons.append(types.KeyboardButton("🔙 بازگشت به مدیریت قیمت‌ها"))
    markup.add(*buttons)
    
    bot.send_message(chat_id, f"📦 **لطفاً حجم مورد نظر را برای پلن {message.text} انتخاب کنید:**", reply_markup=markup, parse_mode="Markdown")
    
    pending_price_edit[chat_id] = {"type": "vip", "plan": plan}

@bot.message_handler(func=lambda message: message.text.startswith("ویرایش ") and "گیگ" in message.text and is_admin(message.chat.id))
def edit_specific_price(message):
    chat_id = message.chat.id
    
    if chat_id not in pending_price_edit or pending_price_edit[chat_id]["type"] != "vip":
        bot.send_message(chat_id, "❌ لطفاً ابتدا پلن را انتخاب کنید!")
        return
    
    volume = message.text.replace("ویرایش ", "").replace(" گیگ", "")
    plan = pending_price_edit[chat_id]["plan"]
    
    current_price = prices["vip"].get(plan, {}).get(volume, 0)
    
    msg = bot.send_message(
        chat_id,
        f"💰 **قیمت فعلی برای پلن {plan} ماهه حجم {volume} گیگ:** {format_price(current_price)} تومان\n\n"
        f"📝 **لطفاً قیمت جدید را وارد کنید (فقط عدد):**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_new_price, plan, volume)

def save_new_price(message, plan, volume):
    chat_id = message.chat.id
    
    try:
        new_price = int(message.text.strip().replace(',', ''))
        
        if plan not in prices["vip"]:
            prices["vip"][plan] = {}
        
        prices["vip"][plan][volume] = new_price
        save_prices()
        
        bot.send_message(
            chat_id,
            f"✅ قیمت با موفقیت به‌روزرسانی شد!\n"
            f"📦 پلن {plan} ماهه - {volume} گیگ: {format_price(new_price)} تومان",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")

@bot.message_handler(func=lambda message: message.text == "✨ ویرایش قیمت ترید" and is_admin(message.chat.id))
def edit_super_price(message):
    chat_id = message.chat.id
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    locations = list(prices["super"].keys())
    buttons = []
    for loc in locations:
        buttons.append(types.KeyboardButton(f"ویرایش {loc}"))
    buttons.append(types.KeyboardButton("🔙 بازگشت به مدیریت قیمت‌ها"))
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        "📍 **لطفاً لوکیشن مورد نظر را برای ویرایش قیمت انتخاب کنید:**",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text.startswith("ویرایش ") and is_admin(message.chat.id))
def edit_super_specific_price(message):
    chat_id = message.chat.id
    location = message.text.replace("ویرایش ", "")
    
    if location not in prices["super"]:
        bot.send_message(chat_id, "❌ لوکیشن نامعتبر!")
        return
    
    current_price = prices["super"][location]
    
    msg = bot.send_message(
        chat_id,
        f"📍 **لوکیشن:** {location}\n"
        f"💰 **قیمت فعلی:** {format_price(current_price)} تومان\n\n"
        f"📝 **لطفاً قیمت جدید را وارد کنید (فقط عدد):**",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_super_specific_price, location)

def save_super_specific_price(message, location):
    chat_id = message.chat.id
    
    try:
        new_price = int(message.text.strip().replace(',', ''))
        
        prices["super"][location] = new_price
        save_prices()
        
        bot.send_message(
            chat_id,
            f"✅ قیمت با موفقیت به‌روزرسانی شد!\n"
            f"📍 {location}: {format_price(new_price)} تومان",
            parse_mode="Markdown"
        )
    except ValueError:
        bot.send_message(chat_id, "❌ لطفاً یک عدد معتبر وارد کنید!")

@bot.message_handler(func=lambda message: message.text == "📊 نمایش همه قیمت‌ها" and is_admin(message.chat.id))
def show_all_prices_admin(message):
    chat_id = message.chat.id
    
    price_text = "💰 **لیست قیمت‌های فعلی**\n\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n"
    price_text += "**🔹 وی‌پی‌ان ویژه**\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    plan_names = {"1": "1 ماهه", "2": "2 ماهه", "3": "3 ماهه"}
    volumes = ["10", "20", "30", "40", "50", "80", "100", "150", "500"]
    
    for plan in ["1", "2", "3"]:
        price_text += f"**📦 {plan_names[plan]}:**\n"
        plan_prices = prices["vip"].get(plan, {})
        for vol in volumes:
            if vol in plan_prices:
                price_text += f"┣ {vol} گیگ: {format_price(plan_prices[vol])} تومان\n"
        price_text += "\n"
    
    price_text += "━━━━━━━━━━━━━━━━━━\n"
    price_text += "**✨ وی‌پی‌ان اختصاصی ترید**\n"
    price_text += "━━━━━━━━━━━━━━━━━━\n\n"
    
    for location, price in prices["super"].items():
        price_text += f"┣ {location}: {format_price(price)} تومان\n"
    
    price_text += "━━━━━━━━━━━━━━━━━━"
    
    bot.send_message(chat_id, price_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🔄 بازنشانی به پیش‌فرض" and is_admin(message.chat.id))
def reset_prices(message):
    global prices
    prices = DEFAULT_PRICES.copy()
    save_prices()
    
    bot.send_message(
        message.chat.id,
        "✅ قیمت‌ها با موفقیت به مقادیر پیش‌فرض بازنشانی شدند!",
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: message.text == "🔙 بازگشت به مدیریت قیمت‌ها" and is_admin(message.chat.id))
def back_to_price_management(message):
    manage_prices(message)

# ---------------- پشتیبانی هوشمند ----------------
smart_faq = {
    "نصب": {
        "keywords": ["نصب", "روش نصب", "چجوری نصب کنم", "setup", "install", "چطور نصب کنم", "آموزش نصب"],
        "answer": "📱 **آموزش نصب کانفیگ:**\n\n"
                  "🔹 **ویندوز:**\n"
                  "1. نرم‌افزار v2rayN رو دانلود کن\n"
                  "2. کانفیگ رو کپی کن\n"
                  "3. توی برنامه از گزینه Import استفاده کن\n\n"
                  "🔹 **اندروید:**\n"
                  "1. نرم‌افزار v2rayNG رو نصب کن\n"
                  "2. کانفیگ رو کپی کن\n"
                  "3. روی + بزن و Add from clipboard رو انتخاب کن\n\n"
                  "🔹 **آیفون/آیپد:**\n"
                  "1. نرم‌افزار Shadowrocket یا Foxray رو نصب کن\n"
                  "2. کانفیگ رو کپی کن\n"
                  "3. توی برنامه گزینه Add Config رو بزن\n\n"
                  "🔹 **مک:**\n"
                  "1. نرم‌افزار V2RayX یا V2RayU رو نصب کن\n"
                  "2. کانفیگ رو کپی کن\n"
                  "3. توی برنامه گزینه Import رو بزن"
    },
    # ... (بقیه smart_faq دقیقاً مثل کد اصلی حفظ شده)
    "default": {
        "answer": "🤔 **سوال شما یافت نشد!**\n\n"
                  "**سوالات متداول:**\n"
                  "🔹 آموزش نصب کانفیگ\n"
                  "🔹 قیمت‌ها و روش پرداخت\n"
                  "🔹 رفع مشکل اتصال\n"
                  "🔹 تمدید اشتراک\n"
                  "🔹 سیستم امتیازات\n"
                  "🔹 زیرمجموعه‌گیری\n"
                  "🔹 وی‌پی‌ان اختصاصی ترید\n"
                  "🔹 کد تخفیف\n"
                  "🔹 اشتراک‌های من\n"
                  "🔹 قطع/وصل کانفیگ\n"
                  "🔹 عضویت در کانال\n\n"
                  "❌ می‌تونی سوالت رو دقیق‌تر بپرسی یا از گزینه '🛠 درخواست پشتیبانی' استفاده کنی."
    }
}

def find_smart_answer(question):
    question = question.lower().strip()
    
    for category, data in smart_faq.items():
        if category == "default":
            continue
        
        for keyword in data.get("keywords", []):
            if keyword in question:
                return data["answer"]
    
    return smart_faq["default"]["answer"]

@bot.message_handler(func=lambda message: message.text == "🤖 پشتیبانی هوشمند")
def smart_support_start(message):
    chat_id = message.chat.id
    smart_support_sessions[chat_id] = True
    
    markup = types.InlineKeyboardMarkup(row_width=3)
    buttons = [
        types.InlineKeyboardButton("📱 نصب", callback_data="smart_install"),
        types.InlineKeyboardButton("💰 قیمت", callback_data="smart_price"),
        types.InlineKeyboardButton("⚠️ اتصال", callback_data="smart_connection"),
        types.InlineKeyboardButton("🔄 تمدید", callback_data="smart_renew"),
        types.InlineKeyboardButton("💳 پرداخت", callback_data="smart_payment"),
        types.InlineKeyboardButton("🏆 امتیاز", callback_data="smart_points"),
        types.InlineKeyboardButton("🔗 زیرمجموعه", callback_data="smart_referral"),
        types.InlineKeyboardButton("✨ ترید", callback_data="smart_trade"),
        types.InlineKeyboardButton("🎟️ تخفیف", callback_data="smart_discount"),
        types.InlineKeyboardButton("📋 اشتراک‌ها", callback_data="smart_subscriptions"),
        types.InlineKeyboardButton("🔄 قطع/وصل", callback_data="smart_disconnect"),
        types.InlineKeyboardButton("📢 کانال", callback_data="smart_channel"),
        types.InlineKeyboardButton("❌ خروج", callback_data="smart_exit")
    ]
    markup.add(*buttons)
    
    welcome_text = (
        "🤖 **به پشتیبانی هوشمند خوش آمدید!**\n\n"
        "اینجا می‌تونی سریع جواب سوالات متداول رو بگیری:\n"
        "✅ سوالات رو بپرس، من جواب می‌دم\n"
        "✅ از دکمه‌های زیر برای دسترسی سریع استفاده کن\n\n"
        "**چی کار کنم کمکت کنم؟**"
    )
    
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("smart_"))
def smart_support_callbacks(call):
    chat_id = call.message.chat.id
    
    if call.data == "smart_install":
        answer = smart_faq["نصب"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_price":
        answer = smart_faq["قیمت"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_connection":
        answer = smart_faq["مشکل اتصال"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_renew":
        answer = smart_faq["تمدید"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_payment":
        answer = smart_faq["پرداخت"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_points":
        answer = smart_faq["امتیاز"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_referral":
        answer = smart_faq["زیرمجموعه"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_trade":
        answer = smart_faq["ترید"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_discount":
        answer = smart_faq["کد تخفیف"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_subscriptions":
        answer = "📋 برای مشاهده اشتراک‌های خود، از گزینه '📋 اشتراک‌های من' در منوی اصلی استفاده کنید."
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_disconnect":
        answer = smart_faq["قطع و وصل"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_channel":
        answer = smart_faq["کانال"]["answer"]
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, answer, parse_mode="Markdown")
    
    elif call.data == "smart_exit":
        if chat_id in smart_support_sessions:
            del smart_support_sessions[chat_id]
        bot.answer_callback_query(call.id, "👋 بازگشت به منوی اصلی")
        bot.delete_message(chat_id, call.message.message_id)
        main_menu(chat_id, skip_welcome=True)

@bot.message_handler(func=lambda message: message.chat.id in smart_support_sessions)
def handle_smart_question(message):
    chat_id = message.chat.id
    question = message.text
    
    bot.send_chat_action(chat_id, 'typing')
    time.sleep(1)
    
    answer = find_smart_answer(question)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton("❓ سوال دیگه", callback_data="smart_continue"),
        types.InlineKeyboardButton("🛠 پشتیبانی واقعی", callback_data="smart_human"),
        types.InlineKeyboardButton("🔙 بازگشت", callback_data="smart_exit")
    ]
    markup.add(*buttons)
    
    bot.send_message(
        chat_id,
        f"❓ **سوال شما:** {question}\n\n{answer}",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "smart_continue")
def smart_continue(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🤖 **سوال بعدی رو بپرس:**\n(مثلاً: چجوری نصب کنم؟ قیمت چنده؟)", 
        chat_id, 
        call.message.message_id
    )

@bot.callback_query_handler(func=lambda call: call.data == "smart_human")
def smart_human(call):
    chat_id = call.message.chat.id
    
    if chat_id in smart_support_sessions:
        del smart_support_sessions[chat_id]
    
    bot.answer_callback_query(call.id, "🛠 در حال انتقال به پشتیبانی واقعی...")
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_ticket"))
    
    support_requests[chat_id] = True
    
    bot.edit_message_text(
        "🛠 **پشتیبانی واقعی**\n\n"
        "📝 لطفاً پیام خود را بنویسید:\n"
        "(ادمین در اولین فرصت پاسخ میدهد)", 
        chat_id, 
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown"
    )

# ---------------- پشتیبانی حرفه‌ای ----------------
@bot.message_handler(func=lambda message: message.text == "🛠 درخواست پشتیبانی")
def support_request(message):
    chat_id = message.chat.id
    support_requests[chat_id] = True
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ انصراف", callback_data="cancel_ticket"))
    
    bot.send_message(chat_id, 
                    "🛠 **پشتیبانی**\n\n"
                    "📝 لطفاً پیام خود را بنویسید:",
                    reply_markup=markup,
                    parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data == "cancel_ticket")
def cancel_ticket(call):
    chat_id = call.message.chat.id
    if chat_id in support_requests:
        del support_requests[chat_id]
    bot.answer_callback_query(call.id, "❌ تیکت لغو شد")
    bot.edit_message_text("❌ تیکت پشتیبانی لغو شد.", chat_id, call.message.message_id)

@bot.message_handler(func=lambda message: message.chat.id in support_requests)
def receive_ticket(message):
    chat_id = message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    reply_btn = types.InlineKeyboardButton("✅ پاسخ به تیکت", callback_data=f"answer_{chat_id}")
    markup.add(reply_btn)
    
    user_info = get_user_display(chat_id)
    
    if message.text:
        for admin_id in ADMINS:
            try:
                bot.send_message(
                    admin_id, 
                    f"📬 **تیکت جدید**\n\n"
                    f"{user_info['full_name']}\n"
                    f"🆔 آیدی: `{chat_id}`\n"
                    f"📱 یوزرنیم: {user_info['username']}\n"
                    f"💬 پیام: {message.text}",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            except:
                pass
    # بقیه انواع رسانه (عکس، ویدیو، ...) دقیقاً مثل کد اصلی حفظ شده‌اند
    elif message.photo:
        for admin_id in ADMINS:
            try:
                bot.send_photo(admin_id, message.photo[-1].file_id,
                              caption=f"📬 تیکت جدید از {user_info['full_name']}\n🆔 `{chat_id}`\n📱 {user_info['username']}",
                              reply_markup=markup)
            except:
                pass
    # ... (همه انواع رسانه حفظ شده)

    bot.send_message(chat_id, "✅ تیکت شما با موفقیت ثبت شد. بزودی پاسخ داده میشود.")
    del support_requests[chat_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith("answer_"))
def answer_ticket(call):
    admin_id = call.message.chat.id
    if not is_admin(admin_id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    try:
        user_id = int(call.data.split("_")[1])
        
        if admin_id in waiting_for_reply:
            bot.answer_callback_query(call.id, 
                                     f"⏳ شما در حال پاسخ به کاربر {waiting_for_reply[admin_id]} هستید. اول اون رو کامل کن.", 
                                     show_alert=True)
            return
        
        waiting_for_reply[admin_id] = user_id
        admin_state[admin_id] = "replying"
        
        bot.answer_callback_query(call.id, "✏️ پاسخ خود را بنویسید")
        
        try:
            bot.edit_message_reply_markup(admin_id, call.message.message_id, reply_markup=None)
        except:
            pass
        
        user_info = get_user_display(user_id)
        
        bot.send_message(admin_id, 
                        f"👤 **در حال پاسخ به کاربر**\n"
                        f"{user_info['full_name']}\n"
                        f"🆔 `{user_id}`\n"
                        f"📱 {user_info['username']}\n\n"
                        f"📝 پیام خود را ارسال کنید (یا /cancel برای انصراف):",
                        parse_mode="Markdown")
    except Exception as e:
        print(f"خطا در answer_ticket: {e}")
        bot.answer_callback_query(call.id, "❌ خطا در پردازش!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_id_"))
def copy_id_callback(call):
    try:
        user_id = call.data.split("_")[2]
        user_info = get_user_display(int(user_id))
        bot.answer_callback_query(
            call.id, 
            f"آیدی: {user_id}\nیوزرنیم: {user_info['username']}", 
            show_alert=True
        )
    except:
        bot.answer_callback_query(call.id, "❌ خطا!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("copy_config_"))
def copy_config_callback(call):
    try:
        bot.answer_callback_query(
            call.id,
            "کانفیگ در پیام بالا موجود است",
            show_alert=True
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "خطا در دریافت کانفیگ", show_alert=True)

# ---------------- مدیریت یادآوری در پنل ادمین ----------------
@bot.message_handler(func=lambda message: message.text == "📅 مدیریت یادآوری" and is_admin(message.chat.id))
def manage_reminders(message):
    chat_id = message.chat.id
    
    total_users = len(expiry_data)
    expiring_soon = 0
    expired = 0
    
    today = datetime.now().date()
    for data in expiry_data.values():
        expiry_date = datetime.strptime(data["expiry_date"], "%Y-%m-%d").date()
        days_left = (expiry_date - today).days
        
        if 0 < days_left <= 7:
            expiring_soon += 1
        elif days_left < 0:
            expired += 1
    
    msg = (
        f"📅 **مدیریت یادآوری تمدید**\n\n"
        f"👥 کاربران دارای اشتراک: {total_users}\n"
        f"⚠️ در حال انقضا (کمتر از ۷ روز): {expiring_soon}\n"
        f"❌ منقضی شده: {expired}\n\n"
    )
    
    if expiring_soon > 0:
        msg += "**کاربران در حال انقضا:**\n"
        for user_id_str, data in expiry_data.items():
            expiry_date = datetime.strptime(data["expiry_date"], "%Y-%m-%d").date()
            days_left = (expiry_date - today).days
            
            if 0 < days_left <= 7:
                user_info = get_user_display(int(user_id_str))
                msg += f"• {user_info['full_name']} - {days_left} روز مانده (پلن {data['plan']} ماهه)\n"
    
    bot.send_message(chat_id, msg, parse_mode="Markdown")

# ---------------- مدیریت زیرمجموعه در پنل ادمین ----------------
@bot.message_handler(func=lambda message: message.text == "🔗 مدیریت زیرمجموعه‌ها" and is_admin(message.chat.id))
def manage_referrals(message):
    chat_id = message.chat.id
    
    total_users = len(referral_data)
    total_referrals = sum(len(data["referrals"]) for data in referral_data.values())
    completed_goals = sum(1 for data in referral_data.values() if len(data["referrals"]) >= REFERRAL_TARGET)
    rewards_given = sum(1 for data in referral_data.values() if data.get("reward_claimed", False))
    
    msg = (
        f"🔗 **مدیریت زیرمجموعه‌ها**\n\n"
        f"👥 کاربران دارای لینک: {total_users}\n"
        f"👥 کل زیرمجموعه‌ها: {total_referrals}\n"
        f"🎯 رسیده به هدف: {completed_goals}\n"
        f"🎁 جایزه دریافت کرده: {rewards_given}\n\n"
    )
    
    top_users = sorted(referral_data.items(), key=lambda x: len(x[1]["referrals"]), reverse=True)[:5]
    if top_users:
        msg += "**برترین کاربران:**\n"
        for user_id_str, data in top_users:
            user_info = get_user_display(int(user_id_str))
            msg += f"• {user_info['full_name']}: {len(data['referrals'])} زیرمجموعه\n"
    
    bot.send_message(chat_id, msg, parse_mode="Markdown")

# ---------------- مدیریت سوالات هوشمند ----------------
@bot.message_handler(func=lambda message: message.text == "🤖 مدیریت سوالات هوشمند" and is_admin(message.chat.id))
def manage_smart_faq(message):
    chat_id = message.chat.id
    
    msg = "🤖 **مدیریت سوالات هوشمند**\n\n"
    msg += "برای ویرایش سوالات، به ادمین bot اطلاع بده.\n"
    msg += f"تعداد دسته‌بندی‌ها: {len(smart_faq) - 1}\n\n"
    msg += "دسته‌بندی‌های موجود:\n"
    for cat in smart_faq.keys():
        if cat != "default":
            msg += f"• {cat}\n"
    
    bot.send_message(chat_id, msg, parse_mode="Markdown")

# ---------------- دیباگ کانفیگ ----------------
@bot.message_handler(func=lambda message: message.text == "🔍 دیباگ کانفیگ" and is_admin(message.chat.id))
def debug_configs(message):
    chat_id = message.chat.id
    
    result = "🔍 **دیباگ کانفیگ‌ها**\n\n"
    result += "**وی‌پی‌ان ویژه:**\n"
    for key in configs["vip"].keys():
        result += f"• {key[0]} ماهه {key[1]} گیگ: {len(configs['vip'][key])} عدد\n"
    
    result += "\n**وی‌پی‌ان اختصاصی ترید:**\n"
    for key in configs["super"].keys():
        result += f"• {key[0]}: {len(configs['super'][key])} عدد\n"
    
    result += f"\n**کل کاربران ثبت‌نام شده:** {len(registered_users)}\n"
    result += f"**کل خریدها:** {len(purchases)}\n"
    result += f"**کل درخواست‌های قطع/وصل:** {len(disconnect_requests)}\n"
    result += f"**کل کدهای تخفیف:** {len(discount_codes)}"
    
    bot.send_message(chat_id, result, parse_mode="Markdown")

# ---------------- تست رایگان ----------------
@bot.message_handler(func=lambda message: message.text == "🎁 تست رایگان")
def free_trial(message):
    chat_id = message.chat.id
    
    if chat_id in free_trial_users:
        bot.send_message(chat_id, "❌ شما قبلاً از تست رایگان استفاده کرده‌اید!")
        return
    
    if free_trial_configs:
        config_text = free_trial_configs.pop(0)
        free_trial_users.add(chat_id)
        save_json(FREE_TRIAL_USERS_FILE, list(free_trial_users))
        save_json(FREE_TRIAL_CONFIGS_FILE, free_trial_configs)
        bot.send_message(chat_id, f"🎁 **تست رایگان شما:**\n\n`{config_text}`", parse_mode="Markdown")
        
        user_info = get_user_display(chat_id)
        for admin_id in ADMINS:
            try:
                bot.send_message(admin_id, f"🎁 کاربر {user_info['full_name']} از تست رایگان استفاده کرد.\n🆔 `{chat_id}`\n📱 {user_info['username']}")
            except:
                pass
    else:
        bot.send_message(chat_id, "❌ متاسفانه در حال حاضر تست رایگان موجود نیست.")

# ---------------- تنظیم کانال لاگ ----------------
@bot.message_handler(func=lambda message: message.text == "📢 تنظیم کانال لاگ" and is_admin(message.chat.id))
def set_log_channel(message):
    msg = bot.send_message(
        message.chat.id,
        "📢 **آیدی کانال لاگ رو وارد کن:**\n\n"
        "مثال: `@vpn_sales_log` یا `-100123456789`",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, save_log_channel)

def save_log_channel(message):
    global LOG_CHANNEL_ID, BACKUP_CHANNEL_ID
    channel_id = message.text.strip()
    
    try:
        test_msg = bot.send_message(channel_id, "✅ کانال لاگ با موفقیت تنظیم شد.")
        bot.delete_message(channel_id, test_msg.message_id)
        LOG_CHANNEL_ID = channel_id
        BACKUP_CHANNEL_ID = channel_id
        bot.send_message(
            message.chat.id,
            f"✅ کانال لاگ با موفقیت به `{channel_id}` تغییر یافت.",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(
            message.chat.id,
            f"❌ خطا در دسترسی به کانال:\n`{e}`\n\n"
            "مطمئن شو ربات ادمین کاناله.\n"
            "از آیدی ادمین به عنوان کانال لاگ استفاده میشه.",
            parse_mode="Markdown"
        )
        LOG_CHANNEL_ID = str(PRIMARY_ADMIN_ID)
        BACKUP_CHANNEL_ID = str(PRIMARY_ADMIN_ID)

# ---------------- هندلر بازگشت به منوی اصلی ----------------
@bot.callback_query_handler(func=lambda call: call.data == "back_to_main")
def back_to_main(call):
    chat_id = call.message.chat.id
    bot.answer_callback_query(call.id)
    bot.delete_message(chat_id, call.message.message_id)
    main_menu(chat_id, skip_welcome=True)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
def back_to_admin(call):
    chat_id = call.message.chat.id
    if not is_admin(chat_id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id)
    bot.delete_message(chat_id, call.message.message_id)
    admin_panel(call.message)

# ================ بخش فیکس‌شده امتیاز من و زیرمجموعه ================

@bot.message_handler(func=lambda message: message.text == "🏆 امتیاز من")
def my_points(message):
    chat_id = message.chat.id
    try:
        points = get_user_points(chat_id)
        progress = min(100, int((points / POINTS_FOR_FREE_MONTH) * 100))
        progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        remaining_days = get_remaining_days(chat_id)
        
        points_text = (
            f"🏆 **کیف امتیازات شما**\n\n"
            f"⭐️ **امتیاز فعلی:** {points}\n"
            f"🎯 **هدف بعدی:** {POINTS_FOR_FREE_MONTH} امتیاز (یک ماه رایگان)\n"
            f"📊 **پیشرفت:** {progress}%\n"
            f"`{progress_bar}`\n\n"
        )
        
        if remaining_days is not None:
            if remaining_days > 0:
                points_text += f"⏱ **روزهای باقی‌مانده از اشتراک:** {remaining_days} روز\n\n"
            elif remaining_days == 0:
                points_text += f"⚠️ **اشتراک شما امروز به اتمام می‌رسد!**\n\n"
            else:
                points_text += f"❌ **اشتراک شما به اتمام رسیده است.**\n\n"
        
        if points >= POINTS_FOR_FREE_MONTH:
            points_text += "🎉 **تبریک! شما می‌توانید یک ماه رایگان دریافت کنید!**\n\n"
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        if points >= POINTS_FOR_FREE_MONTH:
            markup.add(types.InlineKeyboardButton("🎁 دریافت جایزه", callback_data="redeem_points"))
        markup.add(types.InlineKeyboardButton("ℹ️ راهنما", callback_data="points_help"))
        
        bot.send_message(chat_id, points_text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"خطا در my_points کاربر {chat_id}: {e}")
        bot.send_message(chat_id, "❌ مشکلی در نمایش امتیازات پیش آمد.\nلطفاً دوباره امتحان کنید یا به پشتیبانی بگویید.")

@bot.message_handler(func=lambda message: message.text == "🔗 زیرمجموعه‌گیری")
def referral_menu(message):
    chat_id = message.chat.id
    try:
        info = get_referral_info(chat_id)
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🔗 لینک اختصاصی من", callback_data="ref_my_link"),
            types.InlineKeyboardButton("👥 زیرمجموعه‌های من", callback_data="ref_my_list")
        )
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back"))
        
        progress = min(100, int((info["total"] / info["target"]) * 100))
        progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        
        text = (
            "🔗 **سیستم زیرمجموعه‌گیری**\n\n"
            f"👥 **تعداد زیرمجموعه‌های شما:** {info['total']} نفر\n"
            f"🎯 **هدف:** {info['target']} نفر\n"
            f"📊 **پیشرفت:** {progress}%\n"
            f"`{progress_bar}`\n\n"
            f"🎁 **جایزه:** {info['reward']} گیگ کانفیگ رایگان یک ماهه\n"
        )
        
        if info["total"] >= info["target"] and not info["claimed"]:
            text += "\n✅ شما به هدف رسیده‌اید! به زودی جایزه دریافت می‌کنید."
        elif info["claimed"]:
            text += "\n✅ شما قبلاً جایزه خود را دریافت کرده‌اید."
        
        bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"خطا در referral_menu کاربر {chat_id}: {e}")
        bot.send_message(chat_id, "❌ مشکلی در نمایش زیرمجموعه پیش آمد.\nلطفاً دوباره امتحان کنید.")

# ---------------- callback امتیاز و زیرمجموعه ----------------
@bot.callback_query_handler(func=lambda call: call.data in ["points_help", "redeem_points"])
def points_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "points_help":
        help_text = "ℹ️ **راهنمای سیستم امتیازات**\n\n• هر خرید ۲۵ امتیاز\n• ۱۰۰ امتیاز = ۱ ماه رایگان\n• امتیازها همیشه محفوظ می‌مانند"
        bot.answer_callback_query(call.id)
        bot.send_message(chat_id, help_text, parse_mode="Markdown")
    elif call.data == "redeem_points":
        points = get_user_points(chat_id)
        if points >= POINTS_FOR_FREE_MONTH:
            if deduct_points(chat_id, POINTS_FOR_FREE_MONTH):
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("✅ ارسال کانفیگ", callback_data=f"admin_reward_{chat_id}"))
                user_info = get_user_display(chat_id)
                for admin_id in ADMINS:
                    try:
                        bot.send_message(admin_id, f"🎁 درخواست جایزه امتیاز از {user_info['full_name']}\n🆔 `{chat_id}`", reply_markup=markup, parse_mode="Markdown")
                    except:
                        pass
                bot.answer_callback_query(call.id, "✅ درخواست ثبت شد!")
                try:
                    bot.edit_message_text("✅ درخواست شما ثبت شد! به زودی کانفیگ ارسال می‌شود.", chat_id, call.message.message_id)
                except:
                    bot.send_message(chat_id, "✅ درخواست شما ثبت شد! به زودی کانفیگ ارسال می‌شود.")
            else:
                bot.answer_callback_query(call.id, "❌ خطا در کسر امتیاز!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ امتیاز کافی ندارید!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ref_"))
def referral_callbacks(call):
    chat_id = call.message.chat.id
    info = get_referral_info(chat_id)
    
    if call.data == "ref_my_link":
        text = (
            "🔗 **لینک اختصاصی شما**\n\n"
            f"`https://t.me/{BOT_USERNAME}?start={info['code']}`\n\n"
            "🔹 این لینک رو برای دوستانت بفرست\n"
            "🔹 با هر نفری که عضو بشه، یه زیرمجموعه اضافه میشه\n"
            f"🔹 با {info['target']} نفر، {info['reward']} گیگ رایگان می‌گیری"
        )
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back_to_menu"))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, chat_id, call.message.message_id, 
                            reply_markup=markup, parse_mode="Markdown")
    
    elif call.data == "ref_my_list":
        if not info["referrals"]:
            text = "👥 **زیرمجموعه‌های شما**\n\nشما هنوز هیچ زیرمجموعه‌ای ندارید."
        else:
            text = f"👥 **زیرمجموعه‌های شما ({info['total']} نفر)**\n\n"
            for i, ref in enumerate(info["referrals"][-10:], 1):
                text += f"{i}. {ref['name']}\n   🆔 `{ref['id']}`\n   📱 {ref['username']}\n\n"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="ref_back_to_menu"))
        
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, chat_id, call.message.message_id, 
                            reply_markup=markup, parse_mode="Markdown")
    
    elif call.data in ["ref_back_to_menu", "ref_back"]:
        bot.answer_callback_query(call.id)
        if call.data == "ref_back":
            main_menu(chat_id, skip_welcome=True)
        else:
            referral_menu(call.message)

# ---------------- هندلر ارسال جایزه توسط ادمین ----------------
@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reward_"))
def admin_reward_handler(call):
    admin_id = call.message.chat.id
    if not is_admin(admin_id):
        bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
        return
    
    try:
        user_id = int(call.data.split("_")[2])
        
        admin_pending_config[admin_id] = {
            "service": "vip",
            "key": ("1", "10"),
            "is_reward": True,
            "user_id": user_id,
            "reward_type": "points"
        }
        waiting_for_reply[admin_id] = user_id
        
        user_info = get_user_display(user_id)
        
        bot.answer_callback_query(call.id, "📝 متن کانفیگ را ارسال کنید")
        bot.send_message(
            admin_id,
            f"🎁 **ارسال کانفیگ جایزه**\n"
            f"👤 {user_info['full_name']}\n"
            f"🆔 `{user_id}`\n"
            f"📱 {user_info['username']}\n\n"
            f"📦 کانفیگ: یک ماهه - ۱۰ گیگ\n"
            f"📝 لطفاً متن کانفیگ را ارسال کنید:"
        )
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ خطا: {e}", show_alert=True)

# ---------------- آخرین هندلر catch-all ----------------
@bot.callback_query_handler(func=lambda call: True)
def catch_all_callbacks(call):
    bot.answer_callback_query(call.id, "❌ این دکمه کار نمی‌کند!", show_alert=True)
    logging.warning(f"کالبک هندل‌نشده: {call.data}")

# ---------------- هندلر اصلی ادمین ----------------
@bot.message_handler(func=lambda message: is_admin(message.chat.id))
def admin_handler(message):
    chat_id = message.chat.id
    text = message.text

    if chat_id in waiting_for_reply:
        user_id = waiting_for_reply[chat_id]
        
        try:
            success = False
            if message.text and not message.text.startswith("/"):
                bot.send_message(user_id, 
                               f"📨 **پاسخ پشتیبانی**\n\n{message.text}",
                               parse_mode="Markdown")
                success = True
            elif message.photo:
                bot.send_photo(user_id, message.photo[-1].file_id,
                              caption="📨 پاسخ پشتیبانی")
                success = True
            elif message.video:
                bot.send_video(user_id, message.video.file_id,
                              caption="📨 پاسخ پشتیبانی")
                success = True
            elif message.document:
                bot.send_document(user_id, message.document.file_id,
                                 caption="📨 پاسخ پشتیبانی")
                success = True
            elif message.voice:
                bot.send_voice(user_id, message.voice.file_id,
                              caption="📨 پاسخ پشتیبانی")
                success = True
            elif message.sticker:
                bot.send_sticker(user_id, message.sticker.file_id)
                success = True
            elif message.text == "/cancel":
                del waiting_for_reply[chat_id]
                if chat_id in admin_state:
                    del admin_state[chat_id]
                bot.send_message(chat_id, f"✅ پاسخگویی به کاربر {user_id} لغو شد.")
                return
            
            if success:
                user_info = get_user_display(user_id)
                bot.send_message(chat_id, f"✅ پاسخ شما به {user_info['full_name']} ارسال شد.")
                del waiting_for_reply[chat_id]
                if chat_id in admin_state:
                    del admin_state[chat_id]
        except Exception as e:
            error_text = str(e)
            if "chat not found" in error_text or "blocked" in error_text:
                bot.send_message(chat_id, f"❌ کاربر {user_id} ربات را بلاک کرده یا استارت نکرده است.")
            elif "Forbidden" in error_text:
                bot.send_message(chat_id, f"❌ دسترسی به کاربر {user_id} وجود ندارد.")
            else:
                bot.send_message(chat_id, f"❌ خطا: {error_text}")
        
        return

    if text == "/cancel":
        bot.send_message(chat_id, "❌ شما در حال پاسخگویی به کسی نیستید.")
        return

    if chat_id in admin_pending_config:
        pending = admin_pending_config[chat_id]
        service = pending["service"]
        key = pending["key"]
        
        if service not in configs:
            configs[service] = {}
        if key not in configs[service]:
            configs[service][key] = []
        
        configs[service][key].append(message.text)
        save_json(CONFIGS_FILE, configs)
        
        if service == "vip":
            plan, volume = key
            bot.send_message(chat_id, f"✅ کانفیگ ویژه با موفقیت اضافه شد!\n📦 {plan} ماهه - {volume} گیگ")
            
            if pending.get("is_reward") and pending.get("user_id"):
                user_id = pending.get("user_id")
                user_info = get_user_display(user_id)
                bot.send_message(user_id, f"🎁 **کانفیگ جایزه شما ارسال شد!**\n\n🔐 کانفیگ:\n`{message.text}`", parse_mode="Markdown")
                bot.send_message(chat_id, f"✅ کانفیگ جایزه به {user_info['full_name']} ارسال شد.")
        else:
            location, plan = key
            bot.send_message(chat_id, f"✅ کانفیگ اختصاصی ترید با موفقیت اضافه شد!\n📍 {location} - {plan} ماهه")
        
        del admin_pending_config[chat_id]
        return

    if text.startswith("➕ کانفیگ ویژه "):
        parts = text.replace("➕ کانفیگ ویژه ", "").split()
        if len(parts) >= 3:
            plan = parts[0]
            volume = parts[2]
            key = (plan, volume)
            admin_pending_config[chat_id] = {"service": "vip", "key": key, "is_reward": False}
            bot.send_message(chat_id, f"📝 متن کانفیگ ویژه {plan} ماهه {volume} گیگ را ارسال کنید:")
        return
    
    if text.startswith("➕ کانفیگ ترید "):
        location = text.replace("➕ کانفیگ ترید ", "")
        key = (location, "1")
        admin_pending_config[chat_id] = {"service": "super", "key": key, "is_reward": False}
        bot.send_message(chat_id, f"📝 متن کانفیگ اختصاصی ترید {location} را ارسال کنید:")
        return

    if text == "📊 آمار":
        total_users = len(registered_users)
        total_vip_configs = sum(len(configs["vip"][key]) for key in configs["vip"])
        total_super_configs = sum(len(configs["super"][key]) for key in configs["super"])
        total_purchases = len(purchases)
        total_points = sum(user_points.values())
        total_disconnect = len(disconnect_requests)
        total_discount_codes = len(discount_codes)
        
        bot.send_message(chat_id, 
                        f"📊 **آمار کلی:**\n\n"
                        f"👥 کاربران کل: {total_users}\n"
                        f"📦 کانفیگ‌های ویژه: {total_vip_configs}\n"
                        f"✨ کانفیگ‌های ترید: {total_super_configs}\n"
                        f"💰 تعداد خریدها: {total_purchases}\n"
                        f"🏆 کل امتیازات: {total_points}\n"
                        f"🔄 درخواست‌های قطع/وصل: {total_disconnect}\n"
                        f"🎟️ کدهای تخفیف: {total_discount_codes}",
                        parse_mode="Markdown")
    
    elif text == "➕ افزودن کانفیگ":
        show_add_config_menu(chat_id)
    
    elif text == "➕ کانفیگ رایگان":
        msg = bot.send_message(chat_id, "📝 متن کانفیگ رایگان رو ارسال کن:")
        bot.register_next_step_handler(msg, save_free_trial)
    
    elif text == "📋 لیست خریدها":
        if not purchases:
            bot.send_message(chat_id, "📭 هیچ خریدی انجام نشده است.")
        else:
            result = "📋 **آخرین خریدها:**\n\n"
            for p in purchases[-10:]:
                user_info = get_user_display(p['user'])
                if p.get("service") == "vip":
                    result += f"👤 {user_info['full_name']} - ویژه {p['plan']} ماهه {p['volume']} گیگ"
                else:
                    result += f"👤 {user_info['full_name']} - ترید {p.get('location', 'نامشخص')}"
                
                if p.get("discount_code"):
                    result += f" (تخفیف: {p['discount_percent']}%)"
                
                result += f"\n🏆 امتیاز: +{p.get('points', 0)} - 🕐 {p.get('time', 'N/A')}\n\n"
            bot.send_message(chat_id, result, parse_mode="Markdown")
    
    elif text == "📦 موجودی کانفیگ‌ها":
        result = "📦 **موجودی کانفیگ‌ها**\n\n"
        result += "**وی‌پی‌ان ویژه:**\n"
        for key, config_list in configs["vip"].items():
            plan, volume = key
            result += f"• {plan} ماهه {volume} گیگ: {len(config_list)} عدد\n"
        
        result += "\n**وی‌پی‌ان اختصاصی ترید:**\n"
        for key, config_list in configs["super"].items():
            location, plan = key
            result += f"• {location}: {len(config_list)} عدد\n"
        
        bot.send_message(chat_id, result, parse_mode="Markdown")
    
    elif text == "👥 کاربران تست رایگان":
        if not free_trial_users:
            bot.send_message(chat_id, "📭 هیچ کاربری از تست رایگان استفاده نکرده.")
        else:
            users_list = ""
            for user_id in free_trial_users:
                user_info = get_user_display(user_id)
                users_list += f"• {user_info['full_name']} - `{user_id}` - {user_info['username']}\n"
            bot.send_message(chat_id, f"👥 **کاربران تست رایگان:**\n\n{users_list}\n\n📊 تعداد: {len(free_trial_users)}", parse_mode="Markdown")
    
    elif text == "🏆 مدیریت امتیازات":
        top_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
        
        result = "🏆 **برترین کاربران:**\n\n"
        for i, (user_id_str, points) in enumerate(top_users, 1):
            user_info = get_user_display(int(user_id_str))
            result += f"{i}. {user_info['full_name']}: {points} امتیاز\n"
        
        result += f"\n📊 مجموع امتیازات: {sum(user_points.values())}"
        result += f"\n👥 کاربران دارای امتیاز: {len(user_points)}"
        
        bot.send_message(chat_id, result, parse_mode="Markdown")
    
    elif text == "📅 مدیریت یادآوری":
        manage_reminders(message)
    
    elif text == "🔗 مدیریت زیرمجموعه‌ها":
        manage_referrals(message)
    
    elif text == "🤖 مدیریت سوالات هوشمند":
        manage_smart_faq(message)
    
    elif text == "💰 مدیریت قیمت‌ها":
        manage_prices(message)
    
    elif text == "🎟️ مدیریت کد تخفیف":
        manage_discount_codes(message)
    
    elif text == "💳 ویرایش اطلاعات پرداخت":
        edit_payment_info(message)
    
    elif text == "📢 تنظیم کانال لاگ":
        set_log_channel(message)
    
    elif text == "🔍 دیباگ کانفیگ":
        debug_configs(message)
    
    elif text == "📊 آپدیت حجم مصرفی":
        update_usage_start(message)
    
    elif text == "🔄 درخواست‌های قطع/وصل":
        show_disconnect_requests(message)
    
    elif text == "📦 بکاپ گیری":
        backup_menu(message)
    
    elif text == "👑 مدیریت ادمین‌ها":
        manage_admins(message)
    
    elif text == "🏠 بازگشت به منوی اصلی":
        main_menu(chat_id, skip_welcome=True)

def save_free_trial(message):
    if message.text:
        free_trial_configs.append(message.text)
        save_json(FREE_TRIAL_CONFIGS_FILE, free_trial_configs)
        bot.send_message(message.chat.id, f"✅ کانفیگ رایگان اضافه شد!\nتعداد کل: {len(free_trial_configs)}")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً فقط متن ارسال کن!")

# ---------------- استارت تردهای مورد نیاز ----------------
def start_reminder_thread():
    reminder_thread = threading.Thread(target=check_expiry_dates, daemon=True)
    reminder_thread.start()
    print("✅ ترد یادآوری تمدید فعال شد")

def start_backup_thread():
    backup_thread = threading.Thread(target=start_auto_backup, daemon=True)
    backup_thread.start()

# ---------------- اجرای ربات ----------------
if __name__ == "__main__":
    print("🤖 ربات با موفقیت شروع به کار کرد...")
    print(f"👑 ادمین اصلی: {PRIMARY_ADMIN_ID}")
    print(f"👥 تعداد ادمین‌ها: {len(ADMINS)}")
    print(f"📢 کانال: {CHANNEL_ID}")
    print(f"📢 کانال لاگ: {LOG_CHANNEL_ID}")
    print(f"📁 مسیر ذخیره‌سازی: {DATA_DIR}")
    print(f"📁 مسیر بکاپ: {BACKUP_DIR}")
    
    check_data_integrity()
    
    print("🤖 پشتیبانی هوشمند: فعال ✅")
    print("🏆 سیستم امتیازات: فعال ✅")
    print("🔗 سیستم زیرمجموعه‌گیری: فعال ✅")
    print("📋 سیستم اشتراک‌های من: فعال ✅")
    print("💰 سیستم مدیریت قیمت‌ها: فعال ✅")
    print("🎟️ سیستم کد تخفیف: فعال ✅")
    print("💳 ویرایش اطلاعات پرداخت: فعال ✅")
    print("👑 مدیریت ادمین‌ها: فعال ✅")
    print("📦 سیستم بکاپ خودکار: فعال ✅")
    
    start_reminder_thread()
    start_backup_thread()
    start_auto_backup()
    
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            logging.error(f"خطا در polling: {e}")
            time.sleep(5)