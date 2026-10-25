import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import database as db
import game_mechanics as game
import html
import random
from datetime import date, timedelta

# 1. Turn on the database
db.init_db()

# 2. Setup the website tab name
st.set_page_config(page_title="Learnabit", layout="wide")

# --- CUSTOM PROGRESS BAR WIDGET ---
def render_block_progress(label, current, total, total_blocks=20):
    if total == 0:
        ratio = 0
    else:
        ratio = current / total
    
    ratio = min(ratio, 1.0)
    filled_blocks = int(ratio * total_blocks)
    empty_blocks = total_blocks - filled_blocks
    
    filled_html = '<div style="width: 14px; height: 14px; background-color: #ffe600; display: inline-block; margin-right: 4px;"></div>' * filled_blocks
    empty_html = '<div style="width: 14px; height: 14px; background-color: #3b3f4e; display: inline-block; margin-right: 4px;"></div>' * empty_blocks
    
    html = f"""
    <div style="background-color: #20222a; border: 2px solid white; padding: 12px 15px; display: flex; align-items: center; margin-bottom: 15px; width: fit-content; box-shadow: 4px 4px 0px black;">
        <div style="color: white; font-family: 'Press Start 2P', cursive; font-size: 12px; margin-right: 30px; white-space: nowrap;">
            {label}
        </div>
        <div style="display: flex; flex-wrap: nowrap;">
            {filled_html}{empty_html}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- SIDEBAR & THEME TOGGLE ---
st.sidebar.title("Learnabit")
theme_mode = st.sidebar.radio("Theme", ["Light Mode", "Dark Mode"])

# --- INJECT DYNAMIC CSS BASED ON TOGGLE ---
if theme_mode == "Light Mode":
    st.markdown("""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] { background-color: #fcfaf5 !important; background-image: radial-gradient(#dcd8c0 1px, transparent 1px) !important; background-size: 20px 20px !important; }
        h1, h2, h3, p, span, label, .stMarkdown { color: #000000 !important; }
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background-color: #ffffff !important; border-right: 3px solid black !important; }
        [data-testid="stHeader"] { background-color: transparent !important; }
        [data-testid="stHeader"] * { color: #000000 !important; fill: #000000 !important; }
        [data-testid="stMetricValue"] { color: #000000 !important; }
        div[data-testid="stMetric"] { background-color: white; border: 2px solid black; box-shadow: 4px 4px 0px black; border-radius: 12px; padding: 15px; }
        /* Style standard inputs */
        .stSelectbox div[data-baseweb="select"] > div, .stTextInput input { border: 2px solid black !important; border-radius: 8px !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewBlockContainer"] { background-color: #151b2b !important; background-image: radial-gradient(#3a4a6b 1px, transparent 1px) !important; background-size: 20px 20px !important; }
        h1, h2, h3, p, span, label, .stMarkdown { color: #f8f9fa !important; }
        [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background-color: #0f131f !important; border-right: 3px solid #3a4a6b !important; }
        [data-testid="stHeader"] { background-color: transparent !important; }
        [data-testid="stHeader"] * { color: #f8f9fa !important; fill: #f8f9fa !important; }
        [data-testid="stMetricValue"] { color: #f8f9fa !important; }
        div[data-testid="stMetric"] { background-color: #0f131f; border: 2px solid #3a4a6b; box-shadow: 4px 4px 0px #3a4a6b; border-radius: 12px; padding: 15px; }
        /* Style standard inputs */
        .stSelectbox div[data-baseweb="select"] > div, .stTextInput input { border: 2px solid #3a4a6b !important; border-radius: 8px !important; background-color: #0f131f !important; color: white !important;}
    </style>
    """, unsafe_allow_html=True)

# --- COMMON CSS (Buttons, Sidebar Poppy Theme, Blocky Slider, Fonts) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    h1, h2, h3 { font-family: 'Press Start 2P', cursive !important; line-height: 1.5 !important; }
    
    div.stButton > button {
        background-color: #ccff00 !important; color: black !important;
        border: 2px solid black !important; border-radius: 12px !important;
        box-shadow: 4px 4px 0px black !important;
        font-family: 'Press Start 2P', cursive !important; 
        font-size: 0.8rem !important; font-weight: 900 !important;
        padding: 10px 20px !important; transition: all 0.1s ease;
    }
    div.stButton > button:active { transform: translate(4px, 4px); box-shadow: 0px 0px 0px black !important; }
    
    div[role="radiogroup"] label div:first-child { display: none !important; }
    
    div[role="radiogroup"] label { 
        padding: 12px 15px; margin-bottom: 12px; 
        border-radius: 12px; border: 2px solid black !important; 
        box-shadow: 4px 4px 0px black !important;
        transition: all 0.1s ease; cursor: pointer;
    }
    div[role="radiogroup"] label p { color: black !important; font-weight: 900 !important; font-family: 'Press Start 2P', cursive !important; font-size: 0.7rem !important; }
    div[role="radiogroup"] label:active { transform: translate(4px, 4px); box-shadow: 0px 0px 0px black !important; }
    
    div[role="radiogroup"] label:nth-child(1) { background-color: #ffb3ba !important; } 
    div[role="radiogroup"] label:nth-child(2) { background-color: #bae1ff !important; } 
    div[role="radiogroup"] label:nth-child(3) { background-color: #baffc9 !important; } 
    div[role="radiogroup"] label:nth-child(4) { background-color: #ffffba !important; } 
    div[role="radiogroup"] label[aria-checked="true"] { background-color: #d1b3ff !important; }
    
    .achievement-card { text-align: center; padding: 20px; border: 2px solid black; border-radius: 8px; margin-bottom: 15px; box-shadow: 4px 4px 0px black; }
    .achievement-card, .achievement-card h2, .achievement-card p, .achievement-card strong { color: #17202a !important; }
    .achievement-card.locked { filter: saturate(0.58); opacity: 0.74; }
    .achievement-card.unlocked { opacity: 1; }
    .achievement-card .achievement-name { font-family: 'Press Start 2P', cursive !important; font-size: 0.62rem; line-height: 1.8; overflow-wrap: anywhere; }
    .achievement-card .achievement-description, .achievement-card .achievement-status { font-family: Arial, sans-serif !important; font-size: 0.95rem; line-height: 1.5; }

    div[class*="st-key-quest-card-"] {
        border: 2px solid #111 !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        background: transparent !important;
        margin-bottom: 0.75rem !important;
    }
    div[class*="st-key-quest-card-completed-"] { opacity: 0.48; }
    
    /* --- NEW: Retro Pixelated Slider Styling --- */
    div[data-baseweb="slider"] div[role="slider"] {
        border-radius: 0px !important;
        background-color: #ccff00 !important;
        border: 2px solid black !important;
        box-shadow: 3px 3px 0px black !important;
        width: 22px !important;
        height: 22px !important;
    }
    div[data-baseweb="slider"] div[data-testid="stTickBar"] { display: none; } /* Hides standard ticks */
</style>
""", unsafe_allow_html=True)

st.sidebar.divider()
page = st.sidebar.radio("Menu", ["Dashboard", "Add Quests", "Achievements", "Statistics"])

stats = db.get_user_stats()
current_xp, current_level, current_streak, longest_streak, last_active, total_quests_done = stats

if page == "Dashboard":
    st.title("Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.write(f"### Lvl: {current_level}")
    col2.write(f"### XP: {current_xp}")
    col3.write(f"### Streak: {current_streak}")
    
    st.write("") 
    
    xp_into_current_level = current_xp % 100
    render_block_progress(f"XP {xp_into_current_level}/100", xp_into_current_level, 100)
    
    habits = db.get_habits()
    total_quests = len(habits)
    completed_habit_ids = db.get_completed_habit_ids()
    completed_today = len(completed_habit_ids)
    
    render_block_progress(f"QUEST {completed_today}/{total_quests}", completed_today, total_quests)
    
    st.markdown("<hr style='border-top: 3px solid #888;'>", unsafe_allow_html=True)
    st.subheader("Today's Quests")
    
    if not habits:
        st.info("No quests yet! Go to 'Add Quests' in the menu to create some.")
        
    for index, habit in enumerate(habits, start=1):
        habit_id, habit_name, cat, diff, xp_reward = habit
        completed = habit_id in completed_habit_ids
        card_key = f"quest-card-completed-{habit_id}" if completed else f"quest-card-{habit_id}"
        with st.container(key=card_key):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{index}. {habit_name}** | `{cat}` · `{diff}` (+{xp_reward} XP)")
            with col2:
                if st.button("Completed" if completed else "Complete", key=f"btn_{habit_id}", disabled=completed):
                    new_total_xp = current_xp + xp_reward
                    new_level = game.calculate_level(new_total_xp)
                    new_streak, new_longest, today_str = game.process_streak(last_active, current_streak, longest_streak)
                    
                    db.update_stats(xp_reward, new_level, new_streak, new_longest, today_str)
                    db.log_completion(habit_name, xp_reward, cat, habit_id)
                    
                    db.unlock_badge("First Quest Done", "Badge")
                    if new_streak >= 3: db.unlock_badge("3-Day Streak", "Badge")
                    if new_level >= 2: db.unlock_badge("Level 2 Reached", "Badge")
                    if new_level >= 5: db.unlock_badge("Level 5 Veteran", "Badge")
                    
                    st.rerun()

elif page == "Add Quests":
    st.title("Start Quest")
    
    # --- NEW: Dynamic XP Logic ---
    # Setup default state for the slider
    if "quest_xp" not in st.session_state:
        st.session_state.quest_xp = 10
        
    def update_xp_from_difficulty():
        diff = st.session_state.quest_diff_select
        if diff == "Easy": st.session_state.quest_xp = 10
        elif diff == "Medium": st.session_state.quest_xp = 20
        elif diff == "Hard": st.session_state.quest_xp = 30
    
    # UI Inputs
    quest_name = st.text_input("Quest name", placeholder="e.g. Read for 20 minutes")
    
    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox("Category", ["Learning", "Wellness", "Creative", "Life", "Personal"])
    with col2:
        difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"], key="quest_diff_select", on_change=update_xp_from_difficulty)
    
    st.write("")
    quest_xp = st.slider("XP Reward Override", min_value=10, max_value=50, step=10, key="quest_xp")
    
    st.write("")
    if st.button("Add quest"):
        if quest_name:
            db.add_habit(quest_name, category, difficulty, quest_xp)
            st.success(f"Quest added!")
        else:
            st.error("Please type a name.")

elif page == "Achievements":
    st.title("Trophy Room")
    achievements = db.get_achievement_status()
    pastel_colors = ["#FFB3BA", "#BAE1FF", "#BAFFC9", "#FFFFBA", "#F4C2F4", "#C9F2E3"]
    cols = st.columns(3)
    for index, achievement in enumerate(achievements):
        with cols[index % 3]:
            status = "Unlocked" if achievement["earned"] else "Locked"
            marker = "★" if achievement["earned"] else "☆"
            card_color = random.Random(achievement["name"]).choice(pastel_colors)
            card_state = "unlocked" if achievement["earned"] else "locked"
            name = html.escape(achievement["name"])
            description = html.escape(achievement["description"])
            st.markdown(
                f"<div class='achievement-card {card_state}' style='background-color: {card_color};'>"
                f"<h2>{marker}</h2><p class='achievement-name'><strong>{name}</strong></p>"
                f"<p class='achievement-description'>{description}</p>"
                f"<p class='achievement-status'><strong>{status}</strong></p></div>",
                unsafe_allow_html=True,
            )
            if not achievement["earned"]:
                st.progress(achievement["progress"] / achievement["target"])
                st.caption(f"{achievement['progress']} / {achievement['target']}")

elif page == "Statistics":
    st.title("Statistics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Quests completed", total_quests_done)
    col2.metric("Current streak", f"{current_streak} days")
    col3.metric("Longest streak", f"{longest_streak} days")
    
    st.write("")
    st.markdown("<hr style='border-top: 3px solid #888;'>", unsafe_allow_html=True)
    st.subheader("XP Earned · last 14 days")
    
    chart_color = "black" if theme_mode == "Light Mode" else "white"
    grid_color = "rgba(0, 0, 0, 0.1)" if theme_mode == "Light Mode" else "rgba(255, 255, 255, 0.1)"
    
    logs = db.get_logs()
    if logs:
        df = pd.DataFrame(logs, columns=["Date", "Quest", "XP Earned"])
        
        fig = px.bar(
            df, x="Date", y="XP Earned", color="Quest", 
            hover_data={"Quest": True, "XP Earned": True},
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
            font=dict(family="Arial", color=chart_color),
            legend=dict(font=dict(color=chart_color), title_font=dict(color=chart_color)),
            xaxis=dict(color=chart_color, tickfont=dict(color=chart_color), showline=True, linewidth=2, linecolor=chart_color, gridcolor=grid_color),
            yaxis=dict(color=chart_color, tickfont=dict(color=chart_color), showline=True, linewidth=2, linecolor=chart_color, gridcolor=grid_color)
        )
        st.plotly_chart(fig, width="stretch", theme=None)
        
        st.markdown("<hr style='border-top: 3px solid #888;'>", unsafe_allow_html=True)
        st.subheader("Activity calendar")
        
        heatmap_data = db.get_activity_heatmap_data()
        if heatmap_data:
            heat_df = pd.DataFrame(heatmap_data, columns=["Date", "Quests"])
            heat_df["Date"] = pd.to_datetime(heat_df["Date"])
            
            end_date = date.today()
            start_date = end_date - timedelta(days=27)
            date_range = pd.date_range(start=start_date, end=end_date)
            
            z_data = [[0 for _ in range(4)] for _ in range(7)]
            for d in date_range:
                week_idx = (d.date() - start_date).days // 7
                day_idx = d.weekday()
                quests = heat_df[heat_df["Date"].dt.date == d.date()]["Quests"]
                if not quests.empty:
                    z_data[day_idx][week_idx] = quests.values[0]

            empty_cell = "#1f2233" if theme_mode == "Dark Mode" else "#e0e0e0"
            active_cell = "#47e5c3" 

            fig_heat = go.Figure(data=go.Heatmap(
                z=z_data, x=["Wk 1", "Wk 2", "Wk 3", "Wk 4"], y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                colorscale=[[0, empty_cell], [1, active_cell]], showscale=False, xgap=3, ygap=3
            ))
            
            fig_heat.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Arial", color=chart_color),
                yaxis=dict(autorange="reversed"), height=300, margin=dict(t=20, b=20, l=40, r=20)
            )
            st.plotly_chart(fig_heat, width="stretch", theme=None)

    else:
        st.info("Complete some quests to see your XP charts here!")