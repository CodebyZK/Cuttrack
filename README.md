# CutTrack

Self-hosted fitness tracking web app for a single-user cut.

## Stack

- Backend: Flask + Jinja2
- Database: SQLite via raw sqlite3
- Frontend: Vanilla JS + Chart.js
- Auth: Flask sessions + Werkzeug password hashing
- Styling: Pure CSS variables with dark/light themes

## Features

- Food logging with calorie and protein tracking
- Daily progress bars against targets: 1,400 calories and 140g protein
- Workout logging with sets/reps and preset split exercises
- Sleep logging with automatic duration and Good/Short/Long quality badge
- Weight logging with 30-day trend graph and 145 lb goal line
- Apple Watch sync endpoint: POST /api/watch/sync using X-Watch-Token
- Theme toggle persisted in localStorage and applied before paint
- JSON API responses; frontend uses fetch and reloads after mutations
- Single-user registration lock after first account

## Project Structure

- app.py: Flask app, routes, auth decorators, Apple Watch sync endpoint
- database.py: init_db and grouped query functions
- requirements.txt: Python dependencies
- static/style.css: Full theme and responsive styling
- static/app.js: Dashboard interaction and API calls
- static/theme.js: Early localStorage theme application
- templates/base.html: Shared shell and imports
- templates/index.html: Main dashboard
- templates/login.html: Login page
- templates/register.html: First-run registration page

## Hardcoded Targets

- Calories per day: 1,400
- Protein per day: 140g
- Sleep target: 7 to 9 hours
- Goal weight: 145 lbs
- Start weight: 165 lbs

## Setup

1. Install dependencies:

   pip install -r requirements.txt

2. Set environment variables (recommended):

   - CUTTRACK_SECRET_KEY
   - CUTTRACK_WATCH_TOKEN

3. Run:

   python app.py

4. Open:

   http://127.0.0.1:5000
