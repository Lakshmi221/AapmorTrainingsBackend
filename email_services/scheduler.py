from apscheduler.schedulers.background import BackgroundScheduler
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta, timezone
from email_services.email_utils import send_training_email
import os
from dotenv import load_dotenv

load_dotenv()

def check_due_trainings():
    try:
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client[os.getenv("DB_NAME")]

        today = datetime.now(timezone.utc)
        one_week_later = today + timedelta(days=7)

        trainings = db['trainings'].find({
            "assigned_to.due_date": {"$lte": one_week_later, "$gte": today}
        })

        for training in trainings:
            title = training.get("title")
            assigned_list = training.get("assigned_to", [])

            for assignment in assigned_list:
                due_date = assignment.get("due_date")
                status = assignment.get("status")
                emp_id = assignment.get("emp_id")

                if due_date and status == "assigned":
                    
                    due = due_date if isinstance(due_date, datetime) else datetime.fromisoformat(due_date)

                    
                    if 0 < (due - today).days <= 7:
                        
                        user = db['users'].find_one({"emp_id": emp_id})
                        if not user:
                            continue

                        name = user.get("name", "Employee")
                        email = user.get("email")

                        if not email:
                            continue

                        send_training_email(
                            to=email,
                            name=name,
                            title=title,
                            due_date=due.strftime("%Y-%m-%d"),
                            subject="Training Due Reminder",
                            heading="Training Due Soon",
                            type="reminder"
                        )
                        print(f"Reminder sent to {name} ({email})")

    except Exception as e:
        print(" Error in due reminder scheduler:", e)

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=check_due_trainings, trigger="interval", hours=24)
    scheduler.start()
