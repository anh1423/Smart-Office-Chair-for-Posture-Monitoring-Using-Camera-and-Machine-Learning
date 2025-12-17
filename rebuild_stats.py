#!/usr/bin/env python3
"""
Rebuild daily_statistics from posture_logs
Run this script to recalculate statistics from all posture logs
"""
import sys
from datetime import date
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from database import DBManager
from database.models import PostureLog, DailyStatistics

def rebuild_daily_statistics(target_date=None):
    """Rebuild daily statistics from posture logs"""
    if target_date is None:
        target_date = date.today()
    
    db_manager = DBManager()
    session = db_manager.get_session()
    
    try:
        print(f"Rebuilding statistics for {target_date}...")
        
        # Get all posture logs for the date
        logs = session.query(PostureLog).filter(
            PostureLog.timestamp >= target_date,
            PostureLog.timestamp < target_date.replace(day=target_date.day + 1)
        ).all()
        
        if not logs:
            print(f"No logs found for {target_date}")
            return
        
        print(f"Found {len(logs)} posture logs")
        
        # Calculate statistics
        total_detections = len(logs)
        total_warnings = sum(1 for log in logs if log.warning_flag)
        correct_posture_count = sum(1 for log in logs if log.posture == 'Correct_posture')
        bad_posture_count = sum(1 for log in logs if log.posture != 'Correct_posture')
        
        # Count posture distribution
        posture_counts = Counter(log.posture for log in logs)
        posture_distribution = dict(posture_counts)
        
        print(f"\nStatistics:")
        print(f"  Total detections: {total_detections}")
        print(f"  Total warnings: {total_warnings}")
        print(f"  Correct postures: {correct_posture_count}")
        print(f"  Bad postures: {bad_posture_count}")
        print(f"\nPosture distribution:")
        for posture, count in sorted(posture_distribution.items(), key=lambda x: x[1], reverse=True):
            print(f"  {posture}: {count}")
        
        # Delete existing statistics
        session.query(DailyStatistics).filter_by(date=target_date).delete()
        
        # Create new statistics
        stats = DailyStatistics(
            date=target_date,
            total_detections=total_detections,
            total_warnings=total_warnings,
            correct_posture_count=correct_posture_count,
            bad_posture_count=bad_posture_count,
            posture_distribution=posture_distribution
        )
        session.add(stats)
        session.commit()
        
        print(f"\n✅ Statistics rebuilt successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db_manager.close_session(session)

if __name__ == '__main__':
    rebuild_daily_statistics()
