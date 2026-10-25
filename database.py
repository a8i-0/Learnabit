import sqlite3
import os
from datetime import date, datetime, time, timedelta


ACHIEVEMENTS = [
    ("First Step", "Complete your first quest.", 1),
    ("Quest Starter", "Complete 5 quests.", 5),
    ("Quest Collector (25)", "Complete 25 quests.", 25),
    ("Quest Collector (100)", "Complete 100 quests.", 100),
    ("Quest Collector (250)", "Complete 250 quests.", 250),
    ("Three-Day Groove", "Complete a quest on 3 consecutive days.", 3),
    ("Seven-Day Spark", "Complete a quest on 7 consecutive days.", 7),
    ("Comeback Win", "Complete a quest after at least one day without a completion.", 1),
    ("Well-Rounded", "Complete quests from 3 different categories.", 3),
    ("Early Bird", "Complete a quest before 9 a.m.", 1),
    ("Night Owl", "Complete a quest after 8 p.m.", 1),
    ("Big XP Energy", "Earn at least 100 XP in one day.", 100),
    ("Level Up (5)", "Reach level 5.", 5),
    ("Level Up (10)", "Reach level 10.", 10),
    ("Level Up (25)", "Reach level 25.", 25),
    ("Quest Marathon", "Complete the same quest 5 times in one day.", 5),
]

def get_connection():
    os.makedirs("data", exist_ok=True)
    return sqlite3.connect("data/learnabit.db", check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS user_stats 
                 (id INTEGER PRIMARY KEY, total_xp INTEGER, level INTEGER, current_streak INTEGER, longest_streak INTEGER, last_active DATE, total_quests INTEGER)''')
    c.execute("PRAGMA table_info(user_stats)")
    user_stats_columns = {row[1] for row in c.fetchall()}
    if "total_quests" not in user_stats_columns:
        c.execute("ALTER TABLE user_stats ADD COLUMN total_quests INTEGER NOT NULL DEFAULT 0")
    
    c.execute('''CREATE TABLE IF NOT EXISTS habits 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, category TEXT, difficulty TEXT, xp_reward INTEGER)''')
    c.execute("PRAGMA table_info(habits)")
    habit_columns = {row[1] for row in c.fetchall()}
    if "category" not in habit_columns:
        c.execute("ALTER TABLE habits ADD COLUMN category TEXT NOT NULL DEFAULT 'Personal'")
    if "difficulty" not in habit_columns:
        c.execute("ALTER TABLE habits ADD COLUMN difficulty TEXT NOT NULL DEFAULT 'Easy'")
                 
    c.execute('''CREATE TABLE IF NOT EXISTS habit_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, habit_name TEXT, xp_earned INTEGER, date_completed DATE,
                  category TEXT, habit_id INTEGER, completed_at TEXT)''')
    c.execute("PRAGMA table_info(habit_logs)")
    log_columns = {row[1] for row in c.fetchall()}
    if "category" not in log_columns:
        c.execute("ALTER TABLE habit_logs ADD COLUMN category TEXT")
    if "habit_id" not in log_columns:
        c.execute("ALTER TABLE habit_logs ADD COLUMN habit_id INTEGER")
    if "completed_at" not in log_columns:
        c.execute("ALTER TABLE habit_logs ADD COLUMN completed_at TEXT")

    c.execute("""UPDATE habit_logs
                 SET habit_id = (SELECT MIN(id) FROM habits WHERE habits.name = habit_logs.habit_name),
                     category = (SELECT MIN(category) FROM habits WHERE habits.name = habit_logs.habit_name)
                 WHERE habit_id IS NULL
                   AND (SELECT COUNT(*) FROM habits WHERE habits.name = habit_logs.habit_name) = 1""")
    c.execute('''CREATE TABLE IF NOT EXISTS unlocked_badges 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, badge_name TEXT, icon TEXT)''')
    
    c.execute("SELECT * FROM user_stats WHERE id = 1")
    if not c.fetchone():
        past_date = str(date.today() - timedelta(days=2))
        c.execute("INSERT INTO user_stats (id, total_xp, level, current_streak, longest_streak, last_active, total_quests) VALUES (1, 0, 1, 0, 0, ?, 0)", (past_date,))
    conn.commit()
    conn.close()

def get_user_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT total_xp, level, current_streak, longest_streak, last_active, total_quests FROM user_stats WHERE id = 1")
    stats = c.fetchone()
    conn.close()
    return stats

def update_stats(gained_xp, new_level, new_streak, new_longest, today_str):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE user_stats SET total_xp = total_xp + ?, level = ?, current_streak = ?, longest_streak = ?, last_active = ?, total_quests = total_quests + 1 WHERE id = 1", 
              (gained_xp, new_level, new_streak, new_longest, today_str))
    conn.commit()
    conn.close()

# NEW: Function updated to save category and difficulty
def add_habit(name, category, difficulty, xp_reward):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO habits (name, category, difficulty, xp_reward) VALUES (?, ?, ?, ?)", 
              (name, category, difficulty, xp_reward))
    conn.commit()
    conn.close()

def get_habits():
    conn = get_connection()
    c = conn.cursor()
    # NEW: Fetches the new columns
    c.execute("SELECT id, name, category, difficulty, xp_reward FROM habits")
    habits = c.fetchall()
    conn.close()
    return habits


def get_completed_habit_ids(completed_date=None):
    completed_date = completed_date or date.today()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT habit_id, habit_name FROM habit_logs WHERE date_completed = ?",
        (completed_date.isoformat(),),
    )
    completed_rows = cursor.fetchall()
    cursor.execute("SELECT id, name FROM habits")
    habits = cursor.fetchall()
    conn.close()

    completed_ids = {habit_id for habit_id, _ in completed_rows if habit_id is not None}
    completed_names = {name for habit_id, name in completed_rows if habit_id is None}
    completed_ids.update(
        habit_id for habit_id, name in habits if name in completed_names
    )
    return completed_ids

def log_completion(habit_name, xp_earned, category=None, habit_id=None, completed_at=None):
    conn = get_connection()
    c = conn.cursor()
    completed_time = datetime.fromisoformat(completed_at) if isinstance(completed_at, str) else completed_at
    completed_time = completed_time or datetime.now()
    c.execute(
        "INSERT INTO habit_logs (habit_name, xp_earned, date_completed, category, habit_id, completed_at) VALUES (?, ?, ?, ?, ?, ?)",
        (habit_name, xp_earned, completed_time.date().isoformat(), category, habit_id, completed_time.isoformat(timespec="seconds")),
    )
    _sync_achievements(c)
    conn.commit()
    conn.close()

def get_logs():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT date_completed, habit_name, SUM(xp_earned) FROM habit_logs GROUP BY date_completed, habit_name ORDER BY date_completed")
    logs = c.fetchall()
    conn.close()
    return logs

def get_activity_heatmap_data():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT date_completed, COUNT(*) FROM habit_logs GROUP BY date_completed")
    activity = c.fetchall()
    conn.close()
    return activity

def unlock_badge(badge_name, icon):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM unlocked_badges WHERE badge_name = ?", (badge_name,))
    if not c.fetchone():
        c.execute("INSERT INTO unlocked_badges (badge_name, icon) VALUES (?, ?)", (badge_name, icon))
    conn.commit()
    conn.close()

def get_badges():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT badge_name, icon FROM unlocked_badges")
    badges = c.fetchall()
    conn.close()
    return badges


def _achievement_progress(cursor):
    cursor.execute("SELECT date_completed, habit_name, xp_earned, category, habit_id, completed_at FROM habit_logs")
    logs = cursor.fetchall()
    cursor.execute("SELECT total_quests, level FROM user_stats WHERE id = 1")
    stats = cursor.fetchone() or (0, 1)

    dates = sorted({date.fromisoformat(str(row[0])[:10]) for row in logs if row[0]})
    max_streak = 0
    streak = 0
    prior_day = None
    for completion_day in dates:
        streak = streak + 1 if prior_day and completion_day == prior_day + timedelta(days=1) else 1
        max_streak = max(max_streak, streak)
        prior_day = completion_day

    total_quests = max(len(logs), stats[0] or 0)
    distinct_categories = {row[3] for row in logs if row[3]}
    comeback = any((later - earlier).days > 1 for earlier, later in zip(dates, dates[1:]))

    xp_by_day = {}
    quests_by_day = {}
    early_bird = False
    night_owl = False
    for completed_day, name, xp, category, habit_id, completed_at in logs:
        day_key = str(completed_day)[:10]
        xp_by_day[day_key] = xp_by_day.get(day_key, 0) + (xp or 0)
        quest_key = habit_id if habit_id is not None else name
        quests_by_day[(day_key, quest_key)] = quests_by_day.get((day_key, quest_key), 0) + 1
        if completed_at:
            try:
                completion_time = datetime.fromisoformat(completed_at).time()
                early_bird = early_bird or completion_time < time(9, 0)
                night_owl = night_owl or completion_time > time(20, 0)
            except ValueError:
                pass

    best_day_xp = max(xp_by_day.values(), default=0)
    same_quest_day_max = max(quests_by_day.values(), default=0)
    level = stats[1] or 1
    return {
        "First Step": (total_quests, 1),
        "Quest Starter": (total_quests, 5),
        "Quest Collector (25)": (total_quests, 25),
        "Quest Collector (100)": (total_quests, 100),
        "Quest Collector (250)": (total_quests, 250),
        "Three-Day Groove": (max_streak, 3),
        "Seven-Day Spark": (max_streak, 7),
        "Comeback Win": (int(comeback), 1),
        "Well-Rounded": (len(distinct_categories), 3),
        "Early Bird": (int(early_bird), 1),
        "Night Owl": (int(night_owl), 1),
        "Big XP Energy": (best_day_xp, 100),
        "Level Up (5)": (level, 5),
        "Level Up (10)": (level, 10),
        "Level Up (25)": (level, 25),
        "Quest Marathon": (same_quest_day_max, 5),
    }


def _sync_achievements(cursor):
    progress = _achievement_progress(cursor)
    cursor.execute("SELECT badge_name FROM unlocked_badges")
    unlocked = {row[0] for row in cursor.fetchall()}
    for name, description, target in ACHIEVEMENTS:
        current, _ = progress[name]
        if current >= target and name not in unlocked:
            cursor.execute("INSERT INTO unlocked_badges (badge_name, icon) VALUES (?, ?)", (name, "Badge"))
            unlocked.add(name)


def get_achievement_status():
    conn = get_connection()
    cursor = conn.cursor()
    progress = _achievement_progress(cursor)
    _sync_achievements(cursor)
    cursor.execute("SELECT badge_name FROM unlocked_badges")
    unlocked = {row[0] for row in cursor.fetchall()}
    statuses = []
    for name, description, target in ACHIEVEMENTS:
        current, _ = progress[name]
        statuses.append({
            "name": name,
            "description": description,
            "progress": min(current, target),
            "target": target,
            "earned": name in unlocked or current >= target,
        })

    achievement_names = {name for name, _, _ in ACHIEVEMENTS}
    cursor.execute("SELECT badge_name FROM unlocked_badges")
    for (name,) in cursor.fetchall():
        if name not in achievement_names:
            statuses.append({
                "name": name,
                "description": "Previously unlocked achievement.",
                "progress": 1,
                "target": 1,
                "earned": True,
            })
    conn.commit()
    conn.close()
    return statuses