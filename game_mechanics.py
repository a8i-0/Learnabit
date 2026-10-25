from datetime import date, datetime, timedelta

def calculate_level(total_xp):
    return int(total_xp / 100) + 1

def process_streak(last_active_str, current_streak, longest_streak):
    today = date.today()
    try:
        last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date()
    except:
        last_active = today - timedelta(days=2) # If error, default to broken streak

    # If already completed a quest today, streak stays the same
    if last_active == today:
        return current_streak, longest_streak, str(today)
        
    yesterday = today - timedelta(days=1)
    
    # If completed yesterday, streak goes up! Otherwise, reset to 1.
    if last_active == yesterday:
        new_streak = current_streak + 1
    else:
        new_streak = 1 
        
    new_longest = max(new_streak, longest_streak)
    return new_streak, new_longest, str(today)