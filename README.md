# ScreenTimePC

A lightweight **Windows-only** screen-time monitor for parents who trust their kids — but also believe in data.

Built because "I was just doing homework" needed a fact-check. Spoiler: it was Minecraft.

## What This Does

- **Tracks active windows** every 5 seconds 
- **Detects idle time** — no keyboard/mouse for 2+ minutes = probably getting a snack
- **Categorises automatically** — gaming, homework, social media, streaming, and the ever-mysterious "Other"
- **Runs as a Windows service** — starts on boot, invisible, survives reboots, and most teenagers
- **Web dashboard** at `http://localhost:5123` 
- **Watchdog** — a scheduled task that restarts the service if someone *accidentally* kills it

No cloud. No accounts. No "please sign in with Google." Everything stays on the local machine.

## Quick Start

### Prerequisites

- Windows 10 or 11
- [Python 3.10+](https://python.org) (check **"Add Python to PATH"** during install — future you will thank present you)
- Administrator access to the target PC

### Install

```cmd
:: Copy the project folder to the target PC, then:
cd C:\ScreenTimePC
pip install -r requirements.txt
python scripts\install_service.py
```

The installer will:

- Copy config to `%LOCALAPPDATA%\ScreenTimePC\config\`
- Install + start the Windows service (auto-starts on boot)
- Create a watchdog scheduled task (checks every 5 min, because trust issues)

Open `http://localhost:5123` — dashboard should appear within a minute. The truth takes a little longer.

### View Remotely

The dashboard binds to `0.0.0.0:5123`, so you can check it from the comfort of your own couch:

```
http://<kids-pc-ip>:5123
```

Run `ipconfig` on the target PC to find its IP. Or just ask your teenager — they probably know more about networking than you do.

### Uninstall

```cmd
cd C:\ScreenTimePC
python scripts\uninstall_service.py
```

For when they finally move out. Or turn 18. Whichever comes first.

## Configuration

### Categories (`config/categories.json`)

Two types of rules:

- `**app_rules**` — match by process name (e.g., `"minecraft*"` → Gaming)
- `**title_rules**` — match by window title (e.g., `"*youtube*"` → Video/Streaming... even if they claim it was an educational video)

Patterns use wildcard matching. You can also reclassify sessions from the dashboard, because sometimes Wikipedia really is homework.

### Default Categories


| Category        | Examples                                                     |
| --------------- | ------------------------------------------------------------ |
| Gaming          | Minecraft, Fortnite, Steam, Epic Games, Valorant, Roblox     |
| Homework/School | Google Docs/Sheets/Slides, Canvas, Khan Academy, Zoom, Teams |
| Social Media    | Discord, Instagram, Reddit, TikTok, Twitter/X, Snapchat      |
| Video/Streaming | YouTube, Netflix, Twitch, Spotify, Disney+                   |
| Productivity    | Word, Excel, PowerPoint, VS Code, Notepad                    |
| Other           | Anything not matching a rule. The digital junk drawer.       |


### Supported Browsers

Chrome, Edge, Firefox, Brave, Opera — all categorised by window title. Yes, even Brave. We see you.

## Development

Test locally with simulated data (works on macOS too — no teenagers required):

```bash
pip install -r requirements.txt
SCREENTIME_DEV_SIMULATE=1 python scripts/run_dev.py
```

Then open `http://localhost:5123`. The simulated teenager is somehow doing homework and gaming at the same time. Realistic.

## Architecture

```
ScreenTimePC/
├── config/
│   └── categories.json       # The rule book
├── screentime/
│   ├── tracker/               # The watcher
│   ├── categoriser/           # The judge
│   ├── db/                    # The memory
│   ├── dashboard/             # The snitch
│   └── service/               # The survivor
├── scripts/
│   ├── install_service.py     # Install on target PC
│   ├── uninstall_service.py   # Remove from target PC
│   └── run_dev.py             # Dev/test runner
├── tests/
└── requirements.txt
```

## Requirements

- Python 3.10+
- `pywin32` (Windows service support — auto-skipped on macOS/Linux)
- `psutil` (process info)
- `flask` (dashboard)
- Patience (parenting)

## Contributing

Contributions welcome. If you're a fellow parent with ideas, or a teenager trying to add a blind spot — we'll review both.

1. Fork the repo
2. Create a branch (`git checkout -b my-feature`)
3. Commit your changes
4. Open a pull request

Keep it simple. This is a parent's tool, not enterprise software.

## License

MIT — do whatever you want with it. See [LICENSE](LICENSE) for details.

## Credits

Built by @bibhudc with [Claude Code](https://claude.ai/claude-code).

*Dedicated to every parent who's ever walked past a screen that was suspiciously alt-tabbed.*