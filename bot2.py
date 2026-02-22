# bot2.py
print("✅ فایل bot2 با موفقیت لود شد!")
print("⏳ آماده برای اضافه کردن قابلیت‌های جدید...")

import json
import os
from telebot import types

editing_config = {}

def setup_config_management(bot, is_admin_func):
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    configs_file = os.path.join(data_dir, "configs.json")
    
    @bot.message_handler(func=lambda message: message.text == "📋 مدیریت کانفیگ")
    def config_management_menu(message):
        if not is_admin_func(message.chat.id):
            return
            
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📋 مشاهده همه کانفیگ‌ها", callback_data="view_configs"),
            types.InlineKeyboardButton("➕ افزودن کانفیگ جدید", callback_data="add_config"),
            types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_admin")
        )
        bot.send_message(
            message.chat.id,
            "📋 **مدیریت کانفیگ‌ها**\n\nلطفاً یک گزینه را انتخاب کنید:",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "view_configs")
    def view_configs(call):
        admin_id = call.message.chat.id
        if not is_admin_func(admin_id):
            bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
            return
        
        try:
            if os.path.exists(configs_file):
                with open(configs_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            else:
                configs = {"vip": {}, "super": {}}
            
            text = "📋 **لیست کانفیگ‌ها**\n\n"
            markup = types.InlineKeyboardMarkup(row_width=1)
            
            # کانفیگ‌های ویژه
            vip_count = 0
            for key, config_list in configs.get("vip", {}).items():
                if config_list:
                    key_str = str(key)
                    plan = key_str.split(",")[0].replace("('", "").replace("'", "").strip()
                    volume = key_str.split(",")[1].replace("')", "").replace("'", "").strip() if "," in key_str else "نامشخص"
                    
                    for i, config in enumerate(config_list):
                        config_id = f"vip_{i}"
                        short_config = config[:50] + "..." if len(config) > 50 else config
                        text += f"📦 **ویژه {plan} ماهه - {volume} گیگ**\n"
                        text += f"🔐 `{short_config}`\n\n"
                        markup.add(
                            types.InlineKeyboardButton(f"🗑 حذف کانفیگ {i+1}", callback_data=f"delete_vip_{i}_{plan}_{volume}")
                        )
                        vip_count += 1
            
            if vip_count == 0:
                text += "❌ هیچ کانفیگ ویژه‌ای وجود ندارد\n"
            
            markup.add(types.InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_config_menu"))
            
            bot.answer_callback_query(call.id)
            bot.edit_message_text(text, admin_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
            
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا: {str(e)}", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_vip_"))
    def delete_vip_config(call):
        admin_id = call.message.chat.id
        if not is_admin_func(admin_id):
            bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
            return
        
        parts = call.data.split("_")
        index = int(parts[2])
        plan = parts[3]
        volume = parts[4]
        
        try:
            if os.path.exists(configs_file):
                with open(configs_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            else:
                configs = {"vip": {}, "super": {}}
            
            # پیدا کردن کلید مناسب
            target_key = None
            for key in configs["vip"].keys():
                key_str = str(key)
                if plan in key_str and volume in key_str:
                    target_key = key
                    break
            
            if target_key and len(configs["vip"][target_key]) > index:
                deleted_config = configs["vip"][target_key][index]
                
                # نمایش پیام تایید با متن کانفیگ
                markup = types.InlineKeyboardMarkup()
                markup.add(
                    types.InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"confirm_delete_{index}_{plan}_{volume}"),
                    types.InlineKeyboardButton("❌ خیر، انصراف", callback_data="cancel_delete")
                )
                
                bot.edit_message_text(
                    f"⚠️ **آیا از حذف این کانفیگ اطمینان دارید؟**\n\n"
                    f"📦 **ویژه {plan} ماهه - {volume} گیگ**\n"
                    f"🔐 کانفیگ:\n`{deleted_config}`",
                    admin_id,
                    call.message.message_id,
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!", show_alert=True)
        
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطا: {str(e)}", show_alert=True)
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_delete_"))
    def confirm_delete(call):
        admin_id = call.message.chat.id
        if not is_admin_func(admin_id):
            bot.answer_callback_query(call.id, "⛔ شما ادمین نیستید!", show_alert=True)
            return
        
        parts = call.data.split("_")
        index = int(parts[2])
        plan = parts[3]
        volume = parts[4]
        
        try:
            if os.path.exists(configs_file):
                with open(configs_file, 'r', encoding='utf-8') as f:
                    configs = json.load(f)
            else:
                configs = {"vip": {}, "super": {}}
            
            # پیدا کردن کلید مناسب
            target_key = None
            for key in configs["vip"].keys():
                key_str = str(key)
                if plan in key_str and volume in key_str:
                    target_key = key
                    break
            
            if target_key and len(configs["vip"][target_key]) > index:
                deleted_config = configs["vip"][target_key].pop(index)
                if not configs["vip"][target_key]:
                    del configs["vip"][target_key]
                
                with open(configs_file, 'w', encoding='utf-8') as f:
                    json.dump(configs, f, ensure_ascii=False, indent=4)
                
                bot.edit_message_text(
                    f"✅ **کانفیگ با موفقیت حذف شد!**\n\n"
                    f"📦 **ویژه {plan} ماهه - {volume} گیگ**\n"
                    f"🔐 کانفیگ حذف شده:\n`{deleted_config}`",
                    admin_id,
                    call.message.message_id,
                    parse_mode="Markdown"
                )
            else:
                bot.answer_callback_query(call.id, "❌ کانفیگ یافت نشد!", show_alert=True)
        
        except Exception as e:
            bot.edit_message_text(f"❌ خطا: {str(e)}", admin_id, call.message.message_id)
    
    @bot.callback_query_handler(func=lambda call: call.data == "cancel_delete")
    def cancel_delete(call):
        admin_id = call.message.chat.id
        bot.answer_callback_query(call.id, "❌ عملیات لغو شد")
        view_configs(call)
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_config_menu")
    def back_to_config_menu(call):
        admin_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        config_management_menu(call.message)
    
    @bot.callback_query_handler(func=lambda call: call.data == "back_to_admin")
    def back_to_admin(call):
        admin_id = call.message.chat.id
        bot.answer_callback_query(call.id)
        bot.send_message(admin_id, "👑 بازگشت به پنل ادمین")