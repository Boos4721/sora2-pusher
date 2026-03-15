<p align="center">
  <h1 align="center">🎬 douyin</h1>
  <p align="center">AI-powered Douyin (抖音/TikTok China) automation — search, download, publish, engage, and analyze.</p>
</p>

<p align="center">
  <a href="#cli-quick-start">CLI Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#commands">Commands</a> •
  <a href="#scripts">Scripts</a> •
  <a href="#claude-code-integration">Claude Code</a> •
  <a href="./LICENSE">License</a>
</p>

---

## CLI Quick Start

The fastest way to get started — **3 commands** from zero to searching:

```bash
# 1. Clone
git clone https://github.com/your-username/douyin.git
cd douyin

# 2. One-click install (auto: Python check → venv → pip install → Playwright Chromium)
bash setup.sh

# 3. Initialize (auto: install Chromium → config → QR login)
source activate.sh && dy init
```

Then just use:

```bash
dy search "AI创业"                                            # Search
dy trending                                                    # Hot trending
dy download https://v.douyin.com/xxxxx/                        # Download (no watermark)
dy publish -t "Hello" -c "My first post" -v video.mp4         # Publish
dy live info ROOM_ID                                           # Live stream info
dy analytics                                                   # Dashboard
dy --help                                                      # All commands
```

> 📖 Full CLI guide: [docs/cli-guide.md](docs/cli-guide.md)

---

## What is this?

A complete toolkit for automating Douyin (抖音/TikTok China) operations through two complementary engines:

| Engine | Technology | Use Cases | Startup |
|--------|-----------|-----------|---------|
| **API Client** | Python httpx, reverse-engineered API | Search, download, comments, trending, live | Instant |
| **Playwright** | Python Playwright, browser automation | Publish, login, analytics dashboard | On-demand |

Built as an [OpenClaw](https://github.com/openclaw/openclaw) Skill, but works standalone or with any MCP-compatible client (Claude Code, Cursor, etc.).

## Features

- 🔍 **Search** — Keyword search with filters (sort, time, type)
- 📥 **Download** — No-watermark video/image download with progress bar
- 📝 **Publish** — Video and image posts with tags, scheduling, visibility
- 🔥 **Trending** — Real-time hot search rankings with watch mode
- 📺 **Live** — Live stream info, stream URL extraction, ffmpeg recording
- 💬 **Engage** — Comment, like, favorite, follow
- 📊 **Analytics** — Creator dashboard data export (CSV)
- 🔔 **Notifications** — Fetch interaction notifications
- 👤 **Profile** — Fetch any user's profile and posts
- 👥 **Multi-Account** — Isolated cookie storage per account
- 🔐 **QR Code Login** — Scan-to-login via Playwright, persistent cookie storage

## Quick Start

### Prerequisites

- Python 3.10+
- Playwright Chromium (auto-installed by `setup.sh`)
- ffmpeg (optional, for live recording: `brew install ffmpeg`)

### 1. Clone & Install

```bash
git clone https://github.com/your-username/douyin.git
cd douyin
bash setup.sh
```

### 2. Initialize & Login

```bash
source activate.sh
dy init
```

This will:
1. Check your environment
2. Install Playwright Chromium
3. Configure proxy (optional)
4. Open browser for QR code login

### 3. Start Using

```bash
dy search "旅行"           # Search
dy trending                 # Hot topics
dy download URL             # Download video
```

---

## Commands

### Search & Discovery

```bash
dy search "关键词"                          # Basic search
dy search "咖啡" --sort 最多点赞            # Sort by likes
dy search "春招" --time 一天内 --type video  # Filters
dy trending                                  # Hot trending list
dy trending --watch                          # Auto-refresh every 5 min
dy trending --json-output                    # JSON output
```

### Download

```bash
dy download https://v.douyin.com/xxxxx/      # Share link
dy download https://www.douyin.com/video/123  # Full link
dy download 1234567890                        # Video ID
dy download URL --music                       # Also download BGM
dy download URL -o ~/Videos                   # Custom output dir
```

### Publish

```bash
# Video
dy publish -t "标题" -c "描述" -v video.mp4

# Image post
dy publish -t "标题" -c "描述" -i img1.jpg -i img2.jpg

# With tags
dy publish -t "旅行日记" -c "巴厘岛" -v trip.mp4 --tags 旅行 --tags 巴厘岛

# Private (test)
dy publish -t "测试" -c "测试" -v test.mp4 --visibility 仅自己可见

# Scheduled
dy publish -t "早安" -c "新的一天" -v morning.mp4 --schedule "2026-03-16T08:00:00+08:00"

# Preview only
dy publish -t "标题" -c "描述" -v video.mp4 --dry-run
```

### Video Detail & Comments

```bash
dy detail AWEME_ID                          # Video detail
dy detail AWEME_ID --comments               # With comments
dy comments AWEME_ID                        # Comments only
```

### Interaction

```bash
dy like AWEME_ID                            # Like
dy favorite AWEME_ID                        # Favorite
dy comment AWEME_ID -c "Great!"             # Comment
dy follow SEC_USER_ID                       # Follow user
```

### Live Stream

```bash
dy live info ROOM_ID                        # Live info + stream URLs
dy live record ROOM_ID                      # Record with ffmpeg
dy live record ROOM_ID --quality HD1        # Specific quality
```

### Analytics & Notifications

```bash
dy analytics                                # Creator dashboard
dy analytics --csv data.csv                 # Export CSV
dy notifications                            # Messages
```

### User Profile

```bash
dy me                                       # My info
dy profile SEC_USER_ID                      # User profile
dy profile SEC_USER_ID --posts              # With post list
```

### Multi-Account

```bash
dy account list                             # List accounts
dy account add work                         # Add & login
dy account default work                     # Set default
dy account remove work                      # Remove
```

### Configuration

```bash
dy config show                              # Show config
dy config set api.proxy http://127.0.0.1:7897
dy config set default.download_dir ~/Videos
dy config reset                             # Reset to defaults
```

### Command Aliases

| Alias | Full Command |
|-------|-------------|
| `dy pub` | `dy publish` |
| `dy s` | `dy search` |
| `dy dl` | `dy download` |
| `dy t` | `dy trending` |
| `dy fav` | `dy favorite` |
| `dy noti` | `dy notifications` |
| `dy stat` | `dy status` |
| `dy acc` | `dy account` |
| `dy cfg` | `dy config` |

---

## Engine Architecture

| Engine | Features | Technology |
|--------|----------|------------|
| **API Client** | Search, download, comments, trending, live, user profile | httpx + reverse-engineered API |
| **Playwright** | Publish, login, analytics, notifications | Playwright browser automation |

Most commands auto-select the best engine. Only `publish`, `analytics`, and `login` require Playwright.

---

## Scripts

Standalone Python scripts for direct use without the CLI:

```bash
# Login
python scripts/douyin_login.py --account default

# Publish video
python scripts/douyin_publisher.py -t "标题" -c "描述" -v video.mp4

# Publish images
python scripts/douyin_publisher.py -t "标题" -c "描述" -i img1.jpg img2.jpg

# Analytics
python scripts/douyin_analytics.py --csv output.csv

# Chrome management
python scripts/chrome_launcher.py
python scripts/chrome_launcher.py --kill
```

---

## Claude Code Integration

See [docs/claude-code-integration.md](docs/claude-code-integration.md) for setup instructions.

## Project Structure

```
douyin/
├── README.md                          # This file
├── SKILL.md                           # OpenClaw skill definition
├── pyproject.toml                     # CLI package config
├── manifest.json                      # Skill metadata
├── LICENSE                            # MIT License
├── requirements.txt                   # Python dependencies
├── setup.sh                           # One-click install (macOS/Linux)
├── setup.bat                          # One-click install (Windows)
├── activate.sh                        # Environment activation
├── src/dy_cli/                        # ⭐ CLI package
│   ├── main.py                        # Unified entry point (dy command)
│   ├── engines/
│   │   ├── api_client.py              # Reverse-engineered API client
│   │   └── playwright_client.py       # Playwright browser automation
│   ├── commands/
│   │   ├── init.py                    # dy init (guided setup)
│   │   ├── auth.py                    # dy login/logout/status
│   │   ├── publish.py                 # dy publish (Playwright)
│   │   ├── search.py                  # dy search/detail (API)
│   │   ├── download.py                # dy download (API) ⭐
│   │   ├── interact.py                # dy like/comment/favorite/follow
│   │   ├── trending.py                # dy trending (API) ⭐
│   │   ├── live.py                    # dy live info/record ⭐
│   │   ├── analytics.py               # dy analytics (Playwright)
│   │   ├── profile.py                 # dy me/profile
│   │   ├── account.py                 # dy account management
│   │   └── config_cmd.py              # dy config
│   └── utils/
│       ├── config.py                  # ~/.dy/config.json management
│       ├── output.py                  # Rich formatted output
│       └── signature.py               # Douyin signature utilities
├── scripts/
│   ├── douyin_login.py                # Login script
│   ├── douyin_publisher.py            # Publish script
│   ├── douyin_analytics.py            # Analytics script
│   └── chrome_launcher.py             # Chrome lifecycle
├── config/
│   └── accounts.json.example
└── docs/
    ├── cli-guide.md                   # CLI usage guide
    └── claude-code-integration.md     # Claude Code setup
```

## Platform Support

| Component | macOS | Linux | Windows |
|-----------|:-----:|:-----:|:-------:|
| **dy CLI** | ✅ | ✅ | ✅ |
| API Client | ✅ | ✅ | ✅ |
| Playwright | ✅ | ✅ | ✅ |

## Tips & Known Issues

- **Signature algorithm**: Douyin frequently updates `a-bogus`/`x-bogus` — some API calls may need browser-based signing
- **Login**: Cookie expires periodically, re-login with `dy login`
- **Rate limiting**: Avoid rapid-fire requests, add delays between batch operations
- **Proxy**: Outside China may need proxy: `dy config set api.proxy http://...`
- **Live recording**: Requires ffmpeg: `brew install ffmpeg` (macOS)

## Contributing

Issues and PRs welcome! Areas where help is needed:

- [ ] Improved `a-bogus` signature algorithm
- [ ] Batch download by user/hashtag
- [ ] Playwright interaction (like/comment/follow)
- [ ] More analytics data points
- [ ] Test suite

## License

[MIT](./LICENSE)
