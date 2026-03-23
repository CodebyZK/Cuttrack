# CutTrack

> Your cut. Your data. Your server.

A self-hosted fitness dashboard for tracking calories, workouts, sleep, and weight during a cut.
Syncs automatically with your Apple Watch every hour. Password protected. Runs on your own hardware.

---

## Project structure

```
cuttrack/
├── app.py              # Flask backend + all API routes
├── database.py         # SQLite setup and queries
├── requirements.txt    # Python dependencies
├── static/
│   ├── style.css       # All styles + dark/light theme
│   ├── app.js          # Frontend logic, chart, API calls
│   └── theme.js        # Theme toggle (applies before paint)
└── templates/
    ├── base.html       # Shared HTML shell
    ├── login.html      # Login page
    ├── register.html   # First-run account creation
    └── index.html      # Main dashboard
```

---

## Setup on zkserver

### 1. Install dependencies

```bash
cd ~/cuttrack
pip3 install -r requirements.txt
```

### 2. Change secrets

Open `app.py` and change these two lines:

```python
app.secret_key = "change-this-to-a-random-string-in-production"
WATCH_TOKEN = "change-this-to-a-secret-watch-token"
```

Pick anything random — e.g. run `python3 -c "import secrets; print(secrets.token_hex(32))"` twice.

### 3. Run it

```bash
python3 app.py
```

The app starts on port 5000. Visit `http://192.168.5.78:5000` from anything on your LAN.

On first visit you'll be redirected to `/register` to create your account.
After that, registration is locked — only your account can log in.

### 4. Run it with systemd (so it starts on boot)

Create `/etc/systemd/system/cuttrack.service`:

```ini
[Unit]
Description=CutTrack Flask App
After=network.target

[Service]
User=your-username
WorkingDirectory=/home/your-username/cuttrack
ExecStart=/usr/bin/python3 /home/your-username/cuttrack/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cuttrack
sudo systemctl start cuttrack
```

### 5. Optional: serve through Nginx

Add to your Nginx config:

```nginx
location /fitness/ {
    proxy_pass http://127.0.0.1:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

---

## Apple Watch / iOS Shortcut setup

This is how your Apple Watch calorie data gets to the server every hour automatically.

### What you need
- iPhone with the Shortcuts app
- Apple Watch paired and syncing to Health app

### Step 1 — Create the Shortcut

1. Open the **Shortcuts** app on your iPhone
2. Tap **+** to create a new shortcut
3. Add these actions in order:

**Action 1: Get Health Sample**
- Action: *Find Health Samples*
- Type: *Active Energy Burned*
- Sort by: *Start Date*, Descending
- Limit: 1
- Time range: *Today*
- Aggregate: *Sum*

**Action 2: Set variable**
- Name: `ActiveCals`
- Value: result from Action 1

**Action 3: Get Health Sample**
- Action: *Find Health Samples*
- Type: *Resting Energy Burned*
- Sort by: *Start Date*, Descending
- Limit: 1
- Time range: *Today*
- Aggregate: *Sum*

**Action 4: Set variable**
- Name: `RestingCals`
- Value: result from Action 3

**Action 5: Get Contents of URL**
- URL: `http://192.168.5.78:5000/api/watch/sync`
- Method: POST
- Headers:
  - `Content-Type`: `application/json`
  - `X-Watch-Token`: `[your WATCH_TOKEN from app.py]`
- Body type: JSON
- Body:
  ```json
  {
    "active_calories": [ActiveCals variable],
    "resting_calories": [RestingCals variable]
  }
  ```

### Step 2 — Set up the Automation

1. Go to the **Automation** tab in Shortcuts
2. Tap **+** → **Personal Automation**
3. Choose **Time of Day**
4. Set it to repeat **Every Hour** (or pick specific hours)
5. Select your new shortcut to run
6. Turn off **Ask Before Running** so it fires silently

### Notes
- The sync only works when your iPhone is on your home WiFi (same network as zkserver)
- If you're away from home, data just won't sync that hour — it picks back up when you return
- The dashboard auto-refreshes Watch data every 5 minutes in the browser

---

## Database

SQLite file is created automatically as `cuttrack.db` in the project folder on first run.
No setup needed. Back it up by just copying the file.

```bash
cp cuttrack.db cuttrack.db.bak
```
