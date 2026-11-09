import os
import staypresent

# این خط باعث میشه یه وب‌سرور کوچیک باز بشه تا Koyeb فکر نکنه ربات خوابیده
staypresent.web.json({"status": "running"})

# ربات اصلی رو اجرا میکنه و پورت رو dynamically می‌خونه
staypresent.run(
    "clinic_bot.py",
    port=int(os.getenv("PORT", 8080))
)
