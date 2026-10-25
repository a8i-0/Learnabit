# Lernabit

Lernabit is a habit-building app that turns daily quests into XP, streaks, and achievements. It is built with Streamlit and stores data in a local SQLite database.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

The app creates `data/learnabit.db` on first run. The database is intentionally excluded from Git so personal quest and progress data stays local.

## Project files

- `app.py` contains the Streamlit interface.
- `database.py` manages SQLite storage and achievement progress.
- `game_mechanics.py` handles XP levels and streak calculations.