from datetime import datetime, timedelta


def compute_due_date(training):
    timestamp = training.get('timestamp')
    time_period = training.get('time_period', 0)
    if not timestamp:
        return None
    try:
        created_at = datetime.fromisoformat(timestamp)
        due_date = created_at + timedelta(days=time_period)
        return due_date.strftime('%Y-%m-%d')
    except Exception:
        return None