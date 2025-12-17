#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

from database import DBManager
from database.models import PostureLog, DailyStatistics
from sqlalchemy import func
from collections import Counter
from datetime import datetime, timedelta

db = DBManager()
session = db.get_session()

# Rebuild for 2025-12-02
target_date = datetime(2025, 12, 2).date()

print(f"Rebuilding statistics for {target_date}...")

# Get all logs for that day
logs = session.query(PostureLog).filter(
    func.date(PostureLog.timestamp) == target_date
).all()

print(f"Found {len(logs)} logs")

if logs:
    # Get or create stats
    stats = session.query(DailyStatistics).filter_by(date=target_date).first()
    if not stats:
        from database.models import DailyStatistics
        stats = DailyStatistics(date=target_date)
        session.add(stats)
    
    # Recalculate
    stats.total_detections = len(logs)
    stats.total_warnings = sum(1 for l in logs if l.warning_flag)
    stats.correct_posture_count = sum(1 for l in logs if l.posture == 'Sitting_upright')
    stats.bad_posture_count = sum(1 for l in logs if l.posture != 'Sitting_upright')
    
    posture_counts = Counter(l.posture for l in logs)
    stats.posture_distribution = dict(posture_counts)
    
    session.commit()
    
    print(f"✅ Statistics rebuilt:")
    print(f"  Total: {stats.total_detections}")
    print(f"  Correct: {stats.correct_posture_count}")
    print(f"  Bad: {stats.bad_posture_count}")
    print(f"  Warnings: {stats.total_warnings}")
    print(f"  Distribution: {stats.posture_distribution}")
else:
    print("No logs found")

db.close_session(session)
