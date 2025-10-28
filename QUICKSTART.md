# 🎬 Ticket Booth - Quick Start Guide

## 🚀 First Time Setup & Run

Run one of these scripts (they do everything automatically):

```bash
# For Bash users:
./run-dev.sh

# For Fish shell users:
./run-dev.fish
```

**What it does:**
1. ✅ Creates Python virtual environment
2. ✅ Installs all dependencies  
3. ✅ Compiles Blueprint UI files
4. ✅ Generates resource bundles
5. ✅ Configures the app
6. ✅ Launches Ticket Booth!

**First run takes ~1-2 minutes** (downloading dependencies)

---

## ⚡ Subsequent Runs (Much Faster!)

After the first build, use the quick launcher:

```bash
# For Bash:
./quick-run.sh

# For Fish:
./quick-run.fish
```

**Starts in seconds!** No rebuild needed unless you change UI files.

---

## 📁 What Gets Created

```
titles/
├── _venv/          # Python virtual environment (ignore this)
├── _build/         # Compiled files (ignore this)
├── run-dev.sh      # Full build + run script
├── run-dev.fish    # Fish version
├── quick-run.sh    # Fast launcher (after first build)
└── quick-run.fish  # Fish version
```

---

## 🛠️ When to Use Each Script

| Scenario | Script to Use | Why |
|----------|--------------|-----|
| First time ever | `run-dev.sh/.fish` | Builds everything from scratch |
| Changed Python code | `quick-run.sh/.fish` | Python loads new code automatically |
| Changed UI (.blp files) | `run-dev.sh/.fish` | Needs to recompile blueprints |
| Changed CSS | `run-dev.sh/.fish` | Needs to copy CSS to build dir |
| Just want to run | `quick-run.sh/.fish` | Fastest way to start |

---

## 📦 Prerequisites

You need these installed on your system:

**Fedora:**
```bash
sudo dnf install python3 gtk4 libadwaita blueprint-compiler glib2-devel
```

**Ubuntu:**
```bash
sudo apt install python3 gir1.2-gtk-4.0 gir1.2-adw-1 blueprint-compiler libglib2.0-dev-bin
```

**Arch:**
```bash
sudo pacman -S python gtk4 libadwaita blueprint-compiler
```

---

## 🐛 Troubleshooting

**App won't start?**
- Check logs: `~/.local/share/ticketbooth-dev/logs/ticketbooth.log`

**Missing dependencies?**
- Delete `_venv/` and run `run-dev.sh/.fish` again

**UI looks broken?**
- Delete `_build/` and run `run-dev.sh/.fish` again

**Start completely fresh?**
```bash
rm -rf _build _venv src/shared.py
./run-dev.sh  # or .fish
```

---

## 💡 Tips

- **Development data** is stored separately in `~/.local/share/ticketbooth-dev/`
- **Main app data** (if installed) stays in `~/.local/share/ticketbooth/`
- Use **Ctrl+C** to stop the app when running from terminal
- Check **DEVELOPMENT.md** for detailed information

---

## 🎯 Quick Reference

```bash
# First time or after UI changes:
./run-dev.fish

# Quick runs (after first build):
./quick-run.fish

# Clean everything and start over:
rm -rf _build _venv src/shared.py && ./run-dev.fish
```

---

**Happy Developing! 🎉**

For more details, see [DEVELOPMENT.md](DEVELOPMENT.md)
