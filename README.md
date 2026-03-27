# ScreenTimePC

A lightweight **Windows-only** screen-time monitor for parents who trust their kids — but also believe in data.

Built because "I was just doing homework" needed a fact-check. Spoiler: it was Minecraft.

## What This Does

- **Tracks active windows** every 5 seconds
- **Detects idle time** — no keyboard/mouse for 2+ minutes = probably getting a snack
- **Categorises automatically** — gaming, homework, social media, streaming, and the ever-mysterious "Other"
- **Runs as a hidden logon task** — starts when the user logs in, invisible, survives reboots, and most teenagers
- **Web dashboard** at `http://localhost:5123` — viewable remotely from any device on the same network
- **Watchdog** — a scheduled task that restarts the tracker if someone *accidentally* kills it

No cloud. No accounts. No "please sign in with Google." Everything stays on the local machine.

> **Note:** This is a Windows-only tool. The tracker uses Windows APIs (`win32gui`) to read foreground windows. macOS/Linux are not supported for tracking, but the dev/simulation mode works on macOS for testing.

## Quick Start

### Prerequisites

- **Windows 10 or 11**
- **[Python 3.10+](https://python.org)**
  - During install, **check "Add Python to PATH"** — this is critical. Future you will thank present you.
  - To verify after install, open a **new** Command Prompt and run: `python --version`
- **Administrator access** to the target PC

### Install

```cmd
:: 1. Copy the project folder to the target PC, then:
cd C:\ScreenTimePC

:: 2. Install dependencies (does NOT require admin)
python -m pip install -r requirements.txt

:: 3. Right-click Command Prompt → "Run as Administrator", then:
python scripts\install_service.py
```

> **Tip:** If `pip` doesn't work, use `python -m pip` instead — it's more reliable on fresh Python installs.

The installer will:

1. Copy config to `%LOCALAPPDATA%\ScreenTimePC\config\`
2. Remove any old Windows service from a previous install
3. Create a **logon task** that starts tracking when the user logs in (runs hidden via `pythonw.exe` — no console window)
4. Start the tracker **immediately** (no reboot needed)
5. Create a watchdog scheduled task (checks every 5 min, because trust issues)
6. Add a **Windows Firewall rule** to allow remote dashboard access on port 5123

> **Why not a Windows service?** Services run in Session 0, which is completely walled off from the user's desktop on Windows 10/11. `GetForegroundWindow()` returns nothing there — the tracker would silently collect zero data. The logon task runs in the user's interactive session instead, with full desktop access.

### Verify It's Working

On the target PC, open a browser and go to:

```
http://localhost:5123
```

You should see the dashboard with data appearing within a minute. If it shows all zeros, check the log:

```cmd
type %LOCALAPPDATA%\ScreenTimePC\screentime.log
```

### View Remotely

The dashboard binds to `0.0.0.0:5123`, so you can check it from the comfort of your own couch:

```
http://<kids-pc-ip>:5123
```

**To find the IP:** run `ipconfig` on the target PC and look for the IPv4 address. Or just ask your teenager — they probably know more about networking than you do.

**Remote access not working?** The installer adds a firewall rule automatically, but if it still doesn't work:

```cmd
:: Run as Administrator on the target PC:
netsh advfirewall firewall add rule name="ScreenTimePC Dashboard" dir=in action=allow protocol=tcp localport=5123
```

Also make sure both devices are on the **same Wi-Fi / LAN network**.

### Uninstall

```cmd
:: Run as Administrator:
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
python -m pip install -r requirements.txt
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
│   └── service/               # The survivor (watchdog)
├── scripts/
│   ├── install_service.py     # Install on target PC (as Admin)
│   ├── uninstall_service.py   # Remove from target PC (as Admin)
│   ├── run_tracker.py         # Production runner (launched by logon task)
│   └── run_dev.py             # Dev/test runner (with simulation mode)
├── tests/
└── requirements.txt
```

## Troubleshooting

| Problem | Solution |
| ------- | -------- |
| `python` not recognized | Reinstall Python, check **"Add Python to PATH"** |
| `pip` not recognized | Use `python -m pip` instead |
| Dashboard shows 0 minutes | Check `%LOCALAPPDATA%\ScreenTimePC\screentime.log` for errors |
| Can't reach dashboard remotely | Run the `netsh` firewall command above. Check both devices are on the same network. |
| Installer says "not Administrator" | Right-click Command Prompt → **Run as Administrator** |

## Requirements

- Python 3.10+
- `pywin32` (Windows API access — auto-skipped on macOS/Linux)
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
