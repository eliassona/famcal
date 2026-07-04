# 🏠 FamilyCal — Raspberry Pi Family Calendar

A shared family calendar that runs on your Raspberry Pi.
Every phone, tablet, and laptop on your home network shares the same data.

---

## Quick Start

### 1. Copy files to your Pi

Copy the `familycal/` folder to your Pi. For example:

```bash
scp -r familycal/ pi@raspberrypi.local:~/familycal
```

### 2. Install Flask

SSH into your Pi, then:

```bash
cd ~/familycal
pip3 install -r requirements.txt
```

### 3. Run the server

```bash
python3 server.py
```

The default port is **5000**. You can change it three ways:

```bash
# Command-line flag
python3 server.py --port 8080
python3 server.py -p 8080

# Environment variable
PORT=8080 python3 server.py
```

You'll see:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  🏠 FamilyCal server starting…
  Open http://localhost:8080 in your browser
  Or from other devices: http://<pi-ip>:8080
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 4. Find your Pi's IP address

```bash
hostname -I
```

Then open `http://<that-ip>:5000` on any device in your home.

---

## Run automatically on boot (optional)

To have the calendar start automatically when the Pi boots:

```bash
sudo nano /etc/systemd/system/familycal.service
```

Paste this (adjust the path if needed):

```ini
[Unit]
Description=FamilyCal
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/familycal/server.py --port 5000
WorkingDirectory=/home/pi/familycal
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

Change `--port 5000` to any port you like.

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable familycal
sudo systemctl start familycal
```

---

## Data

All calendar data is stored in `calendar.json` in the same folder as `server.py`.
Back it up with:

```bash
cp calendar.json calendar.backup.json
```

---

## File structure

```
familycal/
├── server.py          ← Flask backend (run this)
├── requirements.txt   ← Python dependencies
├── calendar.json      ← Your data (auto-created on first run)
├── README.md          ← This file
└── static/
    └── index.html     ← The calendar web app
```
