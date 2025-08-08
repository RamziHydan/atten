#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.attendance.models import CheckIn
from collections import defaultdict

def verify_timestamps():
    print("Verifying attendance record timestamps...")
    print("=" * 50)
    
    # Get all check-in records
    checkins = CheckIn.objects.all().order_by('timestamp')
    
    if not checkins.exists():
        print("No check-in records found!")
        return
    
    print(f"Total check-in records: {checkins.count()}")
    
    # Group by date
    dates = defaultdict(int)
    for checkin in checkins:
        dates[checkin.timestamp.date()] += 1
    
    print(f"\nRecords distributed across {len(dates)} different dates:")
    print("-" * 50)
    
    # Show first 10 dates with counts
    for i, (date, count) in enumerate(sorted(dates.items())[:10]):
        print(f"{date}: {count} records")
    
    if len(dates) > 10:
        print(f"... and {len(dates) - 10} more dates")
    
    # Show sample records with different timestamps
    print(f"\nSample records with timestamps:")
    print("-" * 50)
    
    sample_records = checkins[:10]
    for checkin in sample_records:
        print(f"{checkin.employee.username}: {checkin.get_type_display()} at {checkin.timestamp.strftime('%Y-%m-%d %H:%M:%S')} ({checkin.get_status_display()})")
    
    # Check if timestamps are realistic (not all the same)
    unique_timestamps = set(checkin.timestamp for checkin in checkins)
    print(f"\nTimestamp diversity: {len(unique_timestamps)} unique timestamps out of {checkins.count()} records")
    
    if len(unique_timestamps) > checkins.count() * 0.8:  # At least 80% unique
        print("✅ PASS: Timestamps are properly distributed and realistic!")
    else:
        print("❌ FAIL: Timestamps appear to be too similar or not properly distributed")
    
    # Show date range
    first_record = checkins.first()
    last_record = checkins.last()
    print(f"\nDate range: {first_record.timestamp.date()} to {last_record.timestamp.date()}")

if __name__ == "__main__":
    verify_timestamps()
