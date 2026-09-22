#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BeyondEra Tech - Obsidian Vault Synchronizer & Bridge.
Automatically connects the YouTube Content Engine with Obsidian:
1. Syncs 30-Day Master Content Plan into linked Obsidian Markdown notes with frontmatter & wikilinks.
2. Creates Map of Content (MOC), Kanban-ready tags, and live production dashboard.
3. Syncs Channel Intelligence, Competitor Trends, and Research DB.
4. Updates note statuses dynamically (pending -> ready_to_upload -> published).
"""

import os
import sys
import json
import glob
from datetime import datetime
from typing import Dict, Any, List

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)

# Vault Directory Resolution
DEFAULT_VAULT_PATH = os.path.expanduser("~/Documents/Obsidian Vault/BeyondEra_Tech")
VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", DEFAULT_VAULT_PATH)


def ensure_vault_directories():
    """Creates the standard directory tree inside the Obsidian Vault."""
    subdirs = [
        "",
        ".obsidian",
        "00 - Overview & Dashboards",
        "01 - 30-Day Content Plan",
        "02 - Channel Intelligence",
        "03 - Video Production",
        "04 - Automation & Infrastructure"
    ]
    for sub in subdirs:
        p = os.path.join(VAULT_PATH, sub)
        os.makedirs(p, exist_ok=True)

    # Basic obsidian app config
    app_json = os.path.join(VAULT_PATH, ".obsidian", "app.json")
    if not os.path.exists(app_json):
        with open(app_json, "w", encoding="utf-8") as f:
            json.dump({
                "alwaysUpdateLinks": True,
                "newFileLocation": "current",
                "useMarkdownLinks": False
            }, f, indent=2)


def sync_dashboard():
    """Generates the main interactive Map of Content (MOC) dashboard."""
    state_file = os.path.join(PROJECT_ROOT, "assets/30_day_state.json")
    state_data = {}
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = json.load(f)

    last_day = state_data.get("last_completed_day", 0)
    next_day = state_data.get("next_day", 1)

    # Count ready videos
    ready_dir = os.path.join(PROJECT_ROOT, "workspace/ready_to_upload")
    ready_count = len(glob.glob(os.path.join(ready_dir, "*.mp4"))) if os.path.exists(ready_dir) else 0

    content = f"""---
title: "BeyondEra Tech — Master Content OS"
aliases: ["Dashboard", "BeyondEra MOC"]
tags: [dashboard, youtube, ai_automation, beyond_era]
updated_at: "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
---

# 🚀 BeyondEra Tech — Master Content OS

> **Niche:** Autonomous AI, Humanoid Robotics, Quantum Systems, Brain-Computer Interfaces  
> **Target Upload Cadence:** Daily at 19:00 (Tashkent Time / UTC+5)  
> **Server Status:** 🟢 Local Dedicated Host Running (Systemd Daemons Active)

---

## 📊 Live Production Telemetry

| Metric | Status / Count | Link |
| :--- | :--- | :--- |
| **30-Day Master Roadmap** | 30 Days Scheduled | [[30-Day Master Roadmap]] |
| **Completed & Rendered** | **{last_day} / 30 Days** | [[01 - 30-Day Content Plan/]] |
| **Ready for YouTube Upload** | **{ready_count} Videos** in Storage | `workspace/ready_to_upload/` |
| **Next Day in Queue** | **Day #{next_day}** | [[Day {next_day:02d} - Next Production]] |
| **Active Intelligence Feeds** | 7 Deep Tech Niches | [[Channel Intelligence & Trends]] |
| **AI Orchestrator** | Hermes Agent + Gemini Flash | [[Server Architecture]] |

---

## 📑 Core Knowledge Hubs

```dataview
TABLE file.mtime AS "Oxirgi o'zgarish", tags AS "Teglar"
FROM "01 - 30-Day Content Plan"
SORT file.name ASC
LIMIT 10
```

### 🎯 Tezkor Havolalar:
- [[30-Day Master Roadmap]] — To'liq 30 kunlik reja ro'yxati
- [[Channel Intelligence & Trends]] — Raqobatchilar va trend tahlili
- [[Hermes Telegram Bot Integration]] — Telegram bot nazorati va mini-app
- [[Server Architecture]] — Tizim servis va daemonlari holati

---
*Generated automatically by BeyondEra Autonomous Content Engine.*
"""
    dashboard_path = os.path.join(VAULT_PATH, "00 - Overview & Dashboards", "BeyondEra Master Dashboard.md")
    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(content)


def sync_30_day_content_plan():
    """Generates individual markdown notes for all 30 days with full metadata."""
    plan_file = os.path.join(PROJECT_ROOT, "assets/content_plan_30_days.json")
    if not os.path.exists(plan_file):
        print(f"⚠️ {plan_file} topilmadi.")
        return

    with open(plan_file, "r", encoding="utf-8") as f:
        days_data = json.load(f)

    # State check
    state_file = os.path.join(PROJECT_ROOT, "assets/30_day_state.json")
    last_completed = 0
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as sf:
            last_completed = json.load(sf).get("last_completed_day", 0)

    roadmap_rows = []

    for item in days_data:
        day_num = item.get("day", 1)
        title = item.get("title", f"Future Tech Day {day_num}")
        video_type = item.get("video_type", "shorts")
        niche = item.get("niche", "Artificial Intelligence & Future Tech")
        hook = item.get("hook_0_3s", "")
        script = item.get("full_voiceover_script", "")
        tags = item.get("tags", ["#Shorts", "#AI"])
        scenes = item.get("scenes", [])
        audio = item.get("audio_direction", {})
        uzbek_summary = item.get("uzbek_summary", "")

        is_done = day_num <= last_completed
        status = "completed_ready" if is_done else "pending_generation"

        # Sanitize filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-")).rstrip()
        filename = f"Day {day_num:02d} - {safe_title[:50]}.md"
        note_path = os.path.join(VAULT_PATH, "01 - 30-Day Content Plan", filename)

        # Build Scenes Section
        scenes_md = ""
        for sc in scenes:
            s_num = sc.get("scene_num", 1)
            timing = sc.get("timing", "0-5s")
            p = sc.get("flow_prompt", "")
            hud = sc.get("telemetry_hud", "")
            line = sc.get("spoken_line", "")
            scenes_md += f"""### Scene {s_num} ({timing})
- **Flow AI Prompt:** `{p}`
- **Telemetry HUD:** `{hud}`
- **Spoken Audio:** *"{line}"*

"""

        note_content = f"""---
day: {day_num}
title: "{title}"
video_type: "{video_type}"
niche: "{niche}"
status: "{status}"
duration_target: "{'30-60s' if video_type == 'shorts' else '8-12 min'}"
voice_model: "{audio.get('voice_model', 'en-US-ChristopherNeural')}"
tags: {json.dumps(tags)}
created_at: "{datetime.now().strftime('%Y-%m-%d')}"
---

# 🎬 Day {day_num:02d}: {title}

**Holat:** `{"✅ Tayyor (Rendered)" if is_done else "⏳ Navbatda (Pending)"}`  
**Format:** `{"⚡ YouTube Shorts (Vertical 9:16)" if video_type == "shorts" else "🎥 Long Documentary (Horizontal 16:9)"}`  
**Yo'nalish:** `[[{niche}]]`  
**Oldingi kun:** [[Day {max(1, day_num - 1):02d}]] | **Keyingi kun:** [[Day {min(30, day_num + 1):02d}]]

---

## ⚡ 0-3s Viral Retention Hook
> 🎯 **"{hook}"**

---

## 🎙️ To'liq Ovoz Ssenariysi (English Voiceover)
```text
{script}
```

---

## 🎥 Google Flow AI Visual Scenes & Prompts
{scenes_md}

---

## 🎵 Ovoz va Subtitr Direktsiyasi
- **Edge-TTS Voice:** `{audio.get('voice_model', 'en-US-ChristopherNeural')}` (Rate: `{audio.get('voice_rate', '+3%')}`, Volume: `{audio.get('voice_volume', '+20%')}`)
- **Fon Musiqasi:** `{audio.get('music_theme', 'ambient_flow_synth')}`
- **Subtitr Rangi:** `{audio.get('subtitle_color', '&H00FFFF')}` (Cyberpunk Cyan)

---

## 🇺🇿 Telegram Bot / O'zbekcha Xulosa
> {uzbek_summary}

---
*Bog'langan resurslar:* [[BeyondEra Master Dashboard]] | [[Channel Intelligence & Trends]]
"""
        with open(note_path, "w", encoding="utf-8") as f:
            f.write(note_content)

        roadmap_rows.append(
            f"| Day {day_num:02d} | [[{filename[:-3]}]] | `{video_type.upper()}` | `{'✅ Tayyor' if is_done else '⏳ Navbatda'}` |"
        )

    # Master Roadmap Note
    roadmap_path = os.path.join(VAULT_PATH, "00 - Overview & Dashboards", "30-Day Master Roadmap.md")
    with open(roadmap_path, "w", encoding="utf-8") as rf:
        rf.write(f"""---
title: "30-Day Master Content Roadmap"
aliases: ["Roadmap"]
tags: [roadmap, schedule, beyond_era]
---

# 📅 30-Day Master Content Roadmap

| Kun | Video Nomi & Eslatma | Format | Holat |
| :---: | :--- | :---: | :---: |
""" + "\n".join(roadmap_rows) + "\n\n[[BeyondEra Master Dashboard|⬅️ Asosiy Dashboard]]\n")


def sync_channel_intelligence():
    """Generates notes for Channel Intelligence and Competitor Insights."""
    cache_file = os.path.join(PROJECT_ROOT, "assets/intelligence_cache/daily_report_20260921.json")
    intel_data = {}
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            intel_data = json.load(f)

    note_content = f"""---
title: "Channel Intelligence & Trends"
aliases: ["Intelligence", "Market Research"]
tags: [intelligence, competitors, trends, beyond_era]
updated_at: "{datetime.now().strftime('%Y-%m-%d')}"
---

# 🧠 BeyondEra Tech — Channel Intelligence & Competitor Trends

Ushbu eslatma YouTube tahlili va trend skanerlaridan olingan statistik ma'lumotlarni o'z ichiga oladi.

## 🎯 Monitor Qilinayotgan 7 ta Asosiy Yo'nalish
1. **Humanoid Robotics** (`#Robotics #Optimus #Figure02`)
2. **Quantum Computing** (`#Quantum #Qubit`)
3. **Brain-Computer Interfaces** (`#Neuralink #BCI`)
4. **Clean Fusion Energy** (`#Fusion #Tokamak`)
5. **Space Megastructures & Propulsion** (`#SpaceTech #DysonSphere`)
6. **Cellular Nanotechnology & Longevity** (`#Nanobots #Biotech`)
7. **Artificial General Intelligence & Singularity** (`#AGI #Superintelligence`)

---

## 📈 Tahlil Qilingan Raqobatchi Trendlari
- **Eng yuqori retention siri:** Dastlabki 0-3 soniyada odatiy ko'rinishni buzuvchi g'ayritabiiy harakat yoki metrani ko'rsatish (*pattern-interrupt*).
- **Subtitr qoidasi:** 3-4 so'zdan iborat markaziy dinamik ASS subtitrlar, YouTube Shorts interfeysi tugmalarini to'sib qo'ymaydigan balandlikda.

---
[[BeyondEra Master Dashboard|⬅️ Asosiy Dashboard]]
"""
    intel_path = os.path.join(VAULT_PATH, "02 - Channel Intelligence", "Channel Intelligence & Trends.md")
    with open(intel_path, "w", encoding="utf-8") as f:
        f.write(note_content)


def sync_system_architecture():
    """Documents the active host server setup in the Obsidian vault."""
    arch_md = f"""---
title: "Server & Daemon Architecture"
tags: [infrastructure, systemd, docker, server]
updated_at: "{datetime.now().strftime('%Y-%m-%d')}"
---

# 🖥️ Host Server & Autonomous Daemons

Kali Linux noutbuki doimiy avtonom server rejimida ishlaydi.

## ⚙️ Faol Systemd Foydalanuvchi Servislari:
1. `youtube-telegram-bot.service` — Hermes Master Telegram bot (`scripts/hermes_master_bot.py`)
2. `hermes-gateway.service` — Hermes Agent Gateway xabarlar magistrali
3. `telegram-webapp-tunnel.service` — Cloudflare tunnel orqali Telegram Mini-App ulanishi
4. `youtube-integratsiya-scheduler.service` — Har kuni 19:00 da videolarni YouTube'ga chiqaruvchi scheduler

## 🐳 Faol Docker Konteynerlari:
- `youtube_integratsiya_backend` (Django REST API, port 8000)
- `youtube_integratsiya_frontend` (React Dark Studio, port 80)
- `youtube_integratsiya_nginx` (Reverse Proxy, port 80/443)
- `youtube_integratsiya_db` (PostgreSQL 16)
- `youtube_integratsiya_redis` (Redis 7)

---
[[BeyondEra Master Dashboard|⬅️ Asosiy Dashboard]]
"""
    arch_path = os.path.join(VAULT_PATH, "04 - Automation & Infrastructure", "Server Architecture.md")
    with open(arch_path, "w", encoding="utf-8") as f:
        f.write(arch_md)


def run_full_obsidian_sync() -> str:
    """Executes full sync and returns status report."""
    ensure_vault_directories()
    sync_dashboard()
    sync_30_day_content_plan()
    sync_channel_intelligence()
    sync_system_architecture()
    
    # Create symlink inside project root if not present
    symlink_path = os.path.join(PROJECT_ROOT, "obsidian_vault")
    if not os.path.exists(symlink_path) and not os.path.islink(symlink_path):
        try:
            os.symlink(VAULT_PATH, symlink_path)
        except Exception:
            pass

    return f"Obsidian Vault muvaffaqiyatli sinxronlashtirildi: {VAULT_PATH}"


if __name__ == "__main__":
    msg = run_full_obsidian_sync()
    print(msg)
