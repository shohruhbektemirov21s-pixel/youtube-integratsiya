#!/usr/bin/env python3
"""
BeyondEra Tech - Professional FFmpeg Render Engine.
Autonomous Multi-Scene Dynamic Compositor:
1. Multi-scene dynamic visual assembly (cuts between diverse clips & procedural HUDs every 5-8s).
2. Gemini-driven Creative Direction (theme, color palette, voice model, music profile, subtitle colors).
3. Expressive Edge-TTS voiceover synthesis with rate/pitch tuning.
4. Ambient sound design with diverse audio tracks (cyber_pulse, quantum_suspense, ambient_flow_synth, epic_uplifting).
5. Burned-in Subtitles (.ass with mobile-safe positioning).
6. Branding Overlays & Color Grading with theme-matched accents.
7. Post-render QA verification via video_qa.py.
"""

import os
import sys
import glob
import json
import time
import math
import random
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
VIDEO_LIB_DIR = os.path.join(PROJECT_ROOT, "assets/video_library")


def _render_scene_frame_v1(scene_type: str, title: str, subtitle: str, index: int, w: int, h: int, prim_hex: str = "0x00f0ff") -> Image.Image:
    """Generates high-contrast, cyberpunk/future-tech visual scenes for dynamic animation fallback. (Legacy v1, superseded by render_scene_tech_visual)"""
    base = Image.new("RGBA", (w, h), (7, 11, 20, 255))
    draw = ImageDraw.Draw(base)

    # Convert hex to RGB
    try:
        clean_hex = prim_hex.replace("0x", "").replace("#", "")
        r_c = int(clean_hex[0:2], 16)
        g_c = int(clean_hex[2:4], 16)
        b_c = int(clean_hex[4:6], 16)
        prim = (r_c, g_c, b_c, 180)
    except Exception:
        prim = (0, 240, 255, 180)

    sec = (147, 51, 234, 160)

    # Dynamic ambient glow
    cy = int(h * (0.35 + (index % 3) * 0.08))
    for r in range(w, 0, -35):
        a = int(35 * (1 - r / w))
        draw.ellipse([w//2 - r, cy - r, w//2 + r, cy + r], fill=(prim[0], prim[1], prim[2], a))

    # Cyber grid horizon
    horizon_y = int(h * (0.58 if h > w else 0.65))
    vp_x = w // 2
    for x in range(-w, w * 2, 80):
        draw.line([(vp_x, horizon_y), (x, h)], fill=(prim[0], prim[1], prim[2], 45), width=2)
    for i in range(1, 14):
        y = int(horizon_y + (h - horizon_y) * (i / 13.0) ** 2)
        draw.line([(0, y), (w, y)], fill=(prim[0], prim[1], prim[2], 50 + i * 4), width=2)

    # Central HUD Circles & Nodes
    hud_r = int(w * 0.22)
    draw.ellipse([w//2 - hud_r, cy - hud_r, w//2 + hud_r, cy + hud_r], outline=prim, width=3)
    draw.ellipse([w//2 - hud_r - 25, cy - hud_r - 25, w//2 + hud_r + 25, cy + hud_r + 25], outline=sec, width=1)

    random.seed(200 + index)
    nodes = [(random.randint(80, w - 80), random.randint(int(h * 0.20), int(h * 0.55))) for _ in range(14)]
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            d = math.hypot(nodes[i][0] - nodes[j][0], nodes[i][1] - nodes[j][1])
            if d < 250:
                draw.line([nodes[i], nodes[j]], fill=(prim[0], prim[1], prim[2], int(70 * (1 - d / 250))), width=2)
    for nx, ny in nodes:
        draw.ellipse([nx - 6, ny - 6, nx + 6, ny + 6], fill=(255, 255, 255, 255), outline=prim, width=2)

    try:
        font_sub = ImageFont.truetype(FONT_BOLD, 42 if h > w else 36)
        font_mono = ImageFont.truetype(FONT_MONO, 24 if h > w else 20)
    except Exception:
        font_sub = font_mono = None

    telemetry = [
        f"SYS.PROTOCOL // BEYONDERA-AI // SCENE {index+1:02d}",
        f"NEURAL INFERENCE: 0.82ms | COHERENCE: 99.98%",
        f"STATUS: MULTI-SCENE DYNAMIC KINETIC SYNTHESIS"
    ]
    ty = int(h * 0.68)
    for line in telemetry:
        draw.text((80, ty), line, fill=(prim[0], prim[1], prim[2], 180), font=font_mono)
        ty += 30

    draw.rectangle([50, int(h * 0.78), w - 50, int(h * 0.89)], fill=(7, 11, 20, 215), outline=prim, width=2)
    draw.text((w//2, int(h * 0.82)), title.upper(), fill=(255, 255, 255, 255), font=font_sub, anchor="mm")
    draw.text((w//2, int(h * 0.865)), subtitle, fill=prim, font=font_mono, anchor="mm")

    return base.convert("RGB")


def render_scene_tech_visual(
    scene_prompt: str,
    title: str,
    subtitle: str,
    telemetry: str,
    index: int,
    w: int,
    h: int,
    prim_hex: str = "0x00f0ff",
    accent_hex: str = "0xff0055"
) -> Image.Image:
    """
    Generates high-fidelity futuristic technological imagery customized to the specific
    scene prompt (Humanoid Robots, Quantum Processors, Neural Chips, Tokamak Fusion, Space Megastructures).
    """
    base = Image.new("RGBA", (w, h), (5, 9, 18, 255))
    draw = ImageDraw.Draw(base)

    # Convert hex colors
    try:
        c1 = prim_hex.replace("0x", "").replace("#", "")
        prim = (int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16), 220)
    except Exception:
        prim = (0, 240, 255, 220)

    try:
        c2 = accent_hex.replace("0x", "").replace("#", "")
        accent = (int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16), 200)
    except Exception:
        accent = (255, 0, 85, 200)

    p_lower = (scene_prompt + " " + title + " " + subtitle).lower()

    # Determine Domain Theme
    if any(k in p_lower for k in ["quantum", "qubit", "cryo", "laser", "photon"]):
        domain_tag = "QUANTUM CORE // QUBIT SYNTHESIS"
        theme_type = "quantum"
    elif any(k in p_lower for k in ["robot", "humanoid", "actuator", "dexterity", "bipedal"]):
        domain_tag = "BEYONDERA // KINETIC ROBOTICS"
        theme_type = "robot"
    elif any(k in p_lower for k in ["neural", "brain", "synapse", "cortex", "telepathy"]):
        domain_tag = "NEURAL FABRIC // BIO-DIGITAL LINK"
        theme_type = "neural"
    elif any(k in p_lower for k in ["fusion", "plasma", "energy", "tokamak", "stellarator"]):
        domain_tag = "CLEAN FUSION // MAGNETIC CONFINEMENT"
        theme_type = "fusion"
    elif any(k in p_lower for k in ["space", "orbit", "starship", "lunar", "mars", "dyson"]):
        domain_tag = "AEROSPACE // ORBITAL INFRASTRUCTURE"
        theme_type = "space"
    else:
        domain_tag = "FRONTIER AI // AUTONOMOUS MATRIX"
        theme_type = "cyber"

    # Ambient volumetric glows
    center_y = int(h * 0.40)
    for r in range(int(w * 0.9), 0, -40):
        alpha = int(45 * (1 - r / (w * 0.9)))
        draw.ellipse(
            [w // 2 - r, center_y - r, w // 2 + r, center_y + r],
            fill=(prim[0], prim[1], prim[2], alpha)
        )

    # Secondary Accent Glow
    sec_y = int(h * 0.28)
    for r in range(int(w * 0.45), 0, -35):
        alpha = int(30 * (1 - r / (w * 0.45)))
        draw.ellipse(
            [w // 2 - r, sec_y - r, w // 2 + r, sec_y + r],
            fill=(accent[0], accent[1], accent[2], alpha)
        )

    # Cyber Perspective Grid
    horizon_y = int(h * (0.62 if h > w else 0.68))
    vp_x = w // 2
    for x in range(-w, w * 2, 70):
        draw.line([(vp_x, horizon_y), (x, h)], fill=(prim[0], prim[1], prim[2], 40), width=1)
    for i in range(1, 16):
        y_pos = int(horizon_y + (h - horizon_y) * (i / 15.0) ** 2.2)
        draw.line([(0, y_pos), (w, y_pos)], fill=(prim[0], prim[1], prim[2], int(40 + i * 5)), width=2)

    # Domain-Specific Procedural Schematics
    random.seed(1000 + index * 37)
    if theme_type == "quantum":
        # Concentric Interference Rings & Qubit Matrix
        for r_step in range(40, int(w * 0.38), 35):
            draw.ellipse(
                [w // 2 - r_step, center_y - r_step, w // 2 + r_step, center_y + r_step],
                outline=(prim[0], prim[1], prim[2], 120), width=2
            )
        # Qubit lattice
        q_cols, q_rows = 5, 5
        x_gap = int(w * 0.45) // q_cols
        y_gap = int(w * 0.45) // q_rows
        start_x = w // 2 - (q_cols * x_gap) // 2
        start_y = center_y - (q_rows * y_gap) // 2
        for ix in range(q_cols + 1):
            for iy in range(q_rows + 1):
                qx, qy = start_x + ix * x_gap, start_y + iy * y_gap
                draw.line([(qx, qy - 12), (qx, qy + 12)], fill=accent, width=2)
                draw.line([(qx - 12, qy), (qx + 12, qy)], fill=accent, width=2)
                draw.ellipse([qx - 4, qy - 4, qx + 4, qy + 4], fill=(255, 255, 255, 240))

    elif theme_type == "robot":
        # Kinematic Wireframe & HUD Angle Arcs
        draw.ellipse([w // 2 - 180, center_y - 180, w // 2 + 180, center_y + 180], outline=prim, width=3)
        draw.arc([w // 2 - 240, center_y - 240, w // 2 + 240, center_y + 240], start=30, end=210, fill=accent, width=4)
        # Kinematic arm lines
        draw.line([(w // 2 - 140, center_y + 90), (w // 2, center_y - 80)], fill=(255, 255, 255, 220), width=4)
        draw.line([(w // 2, center_y - 80), (w // 2 + 120, center_y + 60)], fill=prim, width=4)
        draw.ellipse([w // 2 - 140 - 10, center_y + 90 - 10, w // 2 - 140 + 10, center_y + 90 + 10], fill=accent)
        draw.ellipse([w // 2 - 10, center_y - 80 - 10, w // 2 + 10, center_y - 80 + 10], fill=(255, 255, 255, 255))
        draw.ellipse([w // 2 + 120 - 10, center_y + 60 - 10, w // 2 + 120 + 10, center_y + 60 + 10], fill=accent)

    elif theme_type == "neural":
        # Synaptic Neural Network Constellation
        syn_nodes = [(random.randint(int(w * 0.15), int(w * 0.85)), random.randint(int(h * 0.20), int(h * 0.55))) for _ in range(18)]
        for i in range(len(syn_nodes)):
            for j in range(i + 1, len(syn_nodes)):
                dist = math.hypot(syn_nodes[i][0] - syn_nodes[j][0], syn_nodes[i][1] - syn_nodes[j][1])
                if dist < 220:
                    alpha = int(140 * (1 - dist / 220))
                    draw.line([syn_nodes[i], syn_nodes[j]], fill=(prim[0], prim[1], prim[2], alpha), width=2)
        for sx, sy in syn_nodes:
            draw.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], fill=(255, 255, 255, 240), outline=accent, width=2)

    elif theme_type == "fusion":
        # Toroidal Tokamak Magnetic Fields
        for r_x in range(int(w * 0.35), 40, -40):
            r_y = int(r_x * 0.55)
            draw.ellipse(
                [w // 2 - r_x, center_y - r_y, w // 2 + r_x, center_y + r_y],
                outline=(prim[0], prim[1], prim[2], 160), width=3
            )
        draw.ellipse(
            [w // 2 - 70, center_y - 70, w // 2 + 70, center_y + 70],
            fill=(accent[0], accent[1], accent[2], 180), outline=(255, 255, 255, 255), width=3
        )

    else:
        # High Tech HUD & Radar Target
        radar_r = int(w * 0.26)
        draw.ellipse([w // 2 - radar_r, center_y - radar_r, w // 2 + radar_r, center_y + radar_r], outline=prim, width=3)
        draw.ellipse([w // 2 - radar_r - 30, center_y - radar_r - 30, w // 2 + radar_r + 30, center_y + radar_r + 30], outline=accent, width=1)
        draw.line([(w // 2 - radar_r - 50, center_y), (w // 2 + radar_r + 50, center_y)], fill=prim, width=2)
        draw.line([(w // 2, center_y - radar_r - 50), (w // 2, center_y + radar_r + 50)], fill=prim, width=2)

    # Fonts setup
    try:
        font_header = ImageFont.truetype(FONT_BOLD, 46 if h > w else 38)
        font_sub = ImageFont.truetype(FONT_BOLD, 36 if h > w else 30)
        font_mono = ImageFont.truetype(FONT_MONO, 24 if h > w else 20)
        font_small = ImageFont.truetype(FONT_MONO, 18 if h > w else 16)
    except Exception:
        font_header = font_sub = font_mono = font_small = None

    # Top Telemetry Header
    draw.rectangle([40, 50, w - 40, 110], fill=(7, 12, 24, 220), outline=prim, width=2)
    draw.text((60, 70), f"⚡ {domain_tag}", fill=prim, font=font_mono)
    draw.text((w - 70, 70), f"SEC.ID // 0x{index+1:02X}", fill=accent, font=font_mono, anchor="ra")

    # Corner Technical Reticles
    c_len = 30
    for cx, cy in [(40, 140), (w - 40, 140), (40, h - 140), (w - 40, h - 140)]:
        dx = c_len if cx == 40 else -c_len
        dy = c_len if cy < h // 2 else -c_len
        draw.line([(cx, cy), (cx + dx, cy)], fill=prim, width=3)
        draw.line([(cx, cy), (cx, cy + dy)], fill=prim, width=3)

    # Telemetry Badges
    clean_telem = "".join(c for c in telemetry if c.isalnum() or c in " .-_/:|")[:50]
    telem_lines = [
        f"PROTOCOL: BEYONDERA-RESEARCH // ACT-{index+1:02d}",
        f"TELEMETRY: {clean_telem or 'OPTIMAL COHERENCE // 99.9%'}",
        f"PROMPT FOCUS: {scene_prompt[:45].strip()}..."
    ]
    t_y = int(h * 0.66)
    for line in telem_lines:
        draw.rectangle([50, t_y - 6, w - 50, t_y + 26], fill=(4, 8, 16, 200))
        draw.text((70, t_y), line, fill=prim, font=font_small)
        t_y += 36

    # Bottom Title Card Box
    box_top = int(h * 0.78)
    box_bottom = int(h * 0.90)
    draw.rectangle([40, box_top, w - 40, box_bottom], fill=(7, 12, 24, 235), outline=accent, width=2)
    clean_t = title.replace("Act ", "PHASE ").upper()[:36]
    draw.text((w // 2, box_top + 35), clean_t, fill=(255, 255, 255, 255), font=font_header, anchor="mm")
    clean_sub = subtitle[:48] if subtitle else "Frontier Future Technologies Breakthrough"
    draw.text((w // 2, box_top + 80), clean_sub, fill=prim, font=font_mono, anchor="mm")

    # Brand Watermark in corner
    draw.text((w // 2, h - 45), "BEYONDERA TECH // NEXT-GEN RESEARCH LABS", fill=(120, 150, 180, 160), font=font_small, anchor="mm")

    return base.convert("RGB")


def render_scene_frame(scene_type: str, title: str, subtitle: str, index: int, w: int, h: int, prim_hex: str = "0x00f0ff") -> Image.Image:
    """Fallback compatibility wrapper."""
    return render_scene_tech_visual("", title, subtitle, "", index, w, h, prim_hex=prim_hex)


def select_best_clip_for_prompt(prompt_text: str, valid_clips: List[str], scene_idx: int) -> str:
    """
    Intelligently maps a scene prompt to the most fitting video clip in library.
    """
    if not valid_clips:
        return ""
    p = prompt_text.lower()
    
    # Keyword to clip preference
    preferred = None
    if any(w in p for w in ["quantum", "qubit", "photon", "laser", "chip"]):
        preferred = "flow_clip_2.mp4"
    elif any(w in p for w in ["neural", "brain", "synapse", "telepathy", "cortex"]):
        preferred = "flow_clip_3.mp4"
    elif any(w in p for w in ["matrix", "radar", "hud", "telemetry", "algorithm", "data"]):
        preferred = "flow_clip_4.mp4"
    elif any(w in p for w in ["space", "orbit", "starship", "lunar", "satellite", "star"]):
        preferred = "flow_clip_5.mp4"
    elif any(w in p for w in ["robot", "humanoid", "hand", "mechanic", "factory"]):
        preferred = "flow_clip_1.mp4"

    if preferred:
        for c in valid_clips:
            if os.path.basename(c) == preferred:
                return c

    # Otherwise staggered distribution across valid clips
    return valid_clips[scene_idx % len(valid_clips)]


def create_multi_scene_dynamic_track(
    content_plan: Dict[str, Any],
    total_dur: float,
    work_dir: str,
    all_clips: Optional[List[str]] = None,
    is_shorts: bool = True
) -> str:
    """
    Builds a high-retention HYBRID multi-scene visual track that creatively blends:
    1. Multi-prompt customized video cuts (varied start offsets, distinct thematic clips).
    2. Multi-prompt futuristic tech image scenes with Ken Burns kinetic motion (zoom, pan, scan).
    Alternates between dynamic video footage and detailed tech imagery so the video
    is never monotonous and maintains >65% viewer retention.
    """
    w = 1080 if is_shorts else 1920
    h = 1920 if is_shorts else 1080

    creative = content_plan.get("creative_direction", {})
    prim_hex = creative.get("primary_hex", "0x00f0ff")
    accent_hex = creative.get("accent_hex", "0xff0055")

    scenes = content_plan.get("scenes") or []
    scene_prompts = content_plan.get("scene_prompts") or []

    if len(scenes) < 3:
        scenes = [
            {"title": "Act 1 The Hook", "voiceover": "Frontier intelligence calibration", "telemetry": "SIGNAL.LOCK: 99.98%", "prompt": "Humanoid robot assembling quantum chip"},
            {"title": "Act 2 The Mechanism", "voiceover": "Sub-millimeter dexterity", "telemetry": "ACTUATION: 480 deg/s", "prompt": "Macro shot of micro actuators and neural wiring"},
            {"title": "Act 3 The Discovery", "voiceover": "Zero-latency computation", "telemetry": "COHERENCE: OPTIMAL", "prompt": "Quantum core cryogenic chamber with laser pulses"},
            {"title": "Act 4 The Inflection", "voiceover": "Physical AI milestone", "telemetry": "BANDWIDTH: 10.4 TB/s", "prompt": "Cleanroom gigafactory with autonomous robotics"},
            {"title": "Act 5 Beyond Horizon", "voiceover": "BeyondEra Tech", "telemetry": "HORIZON: 2026.Q4", "prompt": "Futuristic orbital research station"}
        ]

    # Discover all video assets in library
    if not all_clips:
        all_clips = sorted(glob.glob(os.path.join(VIDEO_LIB_DIR, "flow_clip_*.mp4")))
    valid_clips = [c for c in all_clips if os.path.exists(c) and os.path.getsize(c) > 100 * 1024]

    num_scenes = len(scenes)
    scene_dur = total_dur / float(num_scenes)

    clip_parts = []
    font_mono = FONT_MONO if os.path.exists(FONT_MONO) else "Sans"

    print("=" * 65)
    print(f"🎬 [CREATIVE HYBRID ASSEMBLY] Jami {num_scenes} ta sahna montaj qilinmoqda...")
    print(f"💡 Multi-Prompt rejimi: Video va Rasmlar uyg'unligi (Har bir sahna: {scene_dur:.1f}s)")
    print("=" * 65)

    for idx, sc in enumerate(scenes):
        stitle = sc.get("title", f"Act {idx+1}")
        stelemetry = sc.get("telemetry") or f"SYS.PERF: 99.{90 + (idx * 2) % 10}%"
        # Extract specific prompt for this scene
        sc_prompt = sc.get("prompt") or (scene_prompts[idx] if idx < len(scene_prompts) else "") or content_plan.get("topic", "")
        svoiceover = sc.get("voiceover") or ""

        scene_output = os.path.join(work_dir, f"scene_cut_{idx}.mp4")
        clean_telem = "".join(c for c in stelemetry if c.isalnum() or c in " .-_")[:35]
        scene_badge = f"SCENE {idx+1:02d} // {clean_telem}"

        # Creative Strategy:
        # Alternating scenes: Even scenes (0, 2, 4) use Dynamic Video Clips with scene-matched prompt
        # Odd scenes (1, 3, 5) use Futuristic Scientific Tech Image with Ken Burns animation
        use_video_clip = (idx % 2 == 0) and bool(valid_clips)

        rendered_success = False

        if use_video_clip:
            source_clip = select_best_clip_for_prompt(sc_prompt, valid_clips, idx)
            start_offset = (idx * 1.8) % 4.5
            print(f"  📽 [SCENE {idx+1}/{num_scenes}] Video Klip: {os.path.basename(source_clip)} (Offset: {start_offset:.1f}s) | Prompt: \"{sc_prompt[:40]}...\"")

            vf_filter = (
                f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}, "
                f"eq=contrast=1.08:brightness=0.01:saturation=1.15, "
                f"drawtext=fontfile='{font_mono}':text='{scene_badge}':fontcolor={prim_hex}:fontsize=24:x=(w-text_w)/2:y=280:box=1:boxcolor=0x070b14@0.80:boxborderw=8"
            )

            cmd_scene = [
                "ffmpeg", "-y",
                "-ss", str(start_offset),
                "-stream_loop", "-1",
                "-i", source_clip,
                "-vf", vf_filter,
                "-t", f"{scene_dur:.2f}",
                "-c:v", "libx264", "-preset", "faster", "-crf", "18", "-pix_fmt", "yuv420p",
                scene_output
            ]
            try:
                subprocess.run(cmd_scene, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=25, check=True)
                clip_parts.append(scene_output)
                rendered_success = True
            except Exception as e:
                print(f"  ⚠️ Video klipda xatolik: {e}, rasm animatsiyasiga o'tilmoqda...")

        if not rendered_success:
            # Render High-Tech Scientific Frame tailored to this scene's prompt
            print(f"  🖼 [SCENE {idx+1}/{num_scenes}] Texnologik Rasm + Ken Burns Harakat | Prompt: \"{sc_prompt[:40]}...\"")
            frame_img = os.path.join(work_dir, f"scene_tech_frame_{idx}.jpg")
            im = render_scene_tech_visual(
                scene_prompt=sc_prompt,
                title=stitle,
                subtitle=svoiceover[:45] or sc_prompt[:45],
                telemetry=stelemetry,
                index=idx,
                w=w,
                h=h,
                prim_hex=prim_hex,
                accent_hex=accent_hex
            )
            im.save(frame_img, "JPEG", quality=95)

            size_str = f"{w}x{h}"
            # Creative Ken Burns dynamics
            if idx % 3 == 1:
                # Dynamic slow zoom-in
                motion_filter = f"zoompan=z='min(zoom+0.0018,1.18)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(scene_dur*30)}:s={size_str}:fps=30"
            elif idx % 3 == 2:
                # Dynamic horizontal pan with slight zoom
                motion_filter = f"zoompan=z='1.12':x='(it/{scene_dur})*(iw-iw/zoom)':y='ih/2-(ih/zoom/2)':d={int(scene_dur*30)}:s={size_str}:fps=30"
            else:
                # Dynamic zoom-out revealing the complete architecture
                motion_filter = f"zoompan=z='if(lte(zoom,1.0),1.18,max(1.0,zoom-0.0018))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(scene_dur*30)}:s={size_str}:fps=30"

            cmd_proc = [
                "ffmpeg", "-y", "-loop", "1", "-i", frame_img,
                "-vf", motion_filter,
                "-t", f"{scene_dur:.2f}",
                "-c:v", "libx264", "-preset", "faster", "-pix_fmt", "yuv420p",
                scene_output
            ]
            subprocess.run(cmd_proc, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            clip_parts.append(scene_output)

    # Concatenate all dynamic scene cuts
    concat_txt = os.path.join(work_dir, "scene_concat.txt")
    with open(concat_txt, "w") as f:
        for c in clip_parts:
            f.write(f"file '{c}'\n")

    multi_scene_video = os.path.join(work_dir, "multi_scene_track.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_txt,
        "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p",
        "-r", "30", "-an",
        multi_scene_video
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    print(f"✅ [MULTI-SCENE ASSEMBLY] {len(clip_parts)} ta turli xil video va rasm sahnalari muvaffaqiyatli ulandi!")
    return multi_scene_video


def generate_video_thumbnail(content_plan: Dict[str, Any], output_path: str) -> str:
    """
    Generates a high-contrast, clickable YouTube thumbnail for the episode.
    Follows mobile-first composition rules: clean negative space, bold typography, glowing accents.
    """
    is_shorts = (content_plan.get("video_type") == "shorts")
    w = 1080 if is_shorts else 1280
    h = 1920 if is_shorts else 720

    creative = content_plan.get("creative_direction", {})
    prim_hex = creative.get("primary_hex", "0x00f0ff")
    accent_hex = creative.get("accent_hex", "0xff0055")

    # Render base cyber scene
    title = content_plan.get("title", "BEYONDERA TECH")
    subtitle = content_plan.get("hook", "Frontier AI Breakthrough")[:45]
    thumb = render_scene_frame("thumb", title[:30], subtitle, 0, w, h, prim_hex=prim_hex)

    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    thumb.save(output_path, "JPEG", quality=95)
    print(f"🖼 [THUMBNAIL] Yangi video muqovasi tayyorlandi: {output_path}")
    return output_path


def assemble_final_video(
    content_plan: Dict[str, Any],
    raw_video_path: Optional[str] = None,
    all_clips: Optional[List[str]] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Assembles final high-production MP4 combining multi-scene visual track,
    dynamically voiced narration, ambient music profile, and styled burned-in subtitles.
    Runs complete QA before returning.
    """
    from scripts.audio_subtitles_engine import synthesize_voiceover, generate_styled_ass_subtitles, resolve_ambient_music
    from scripts.video_qa import run_full_qa

    gen_id = content_plan.get("generation_id") or f"gen_{int(time.time())}"
    work_dir = os.path.join(PROJECT_ROOT, f"workspace/working/{gen_id}")
    os.makedirs(work_dir, exist_ok=True)

    is_shorts = (content_plan.get("video_type") == "shorts")
    w = 1080 if is_shorts else 1920
    h = 1920 if is_shorts else 1080

    if not output_path:
        output_path = os.path.join(work_dir, f"rendered_{'shorts' if is_shorts else 'long'}.mp4")


    creative = content_plan.get("creative_direction", {})
    voice_name = creative.get("voice_name", "en-US-ChristopherNeural")
    voice_rate = creative.get("voice_rate", "+3%")
    music_profile = creative.get("music_profile", "ambient_flow_synth")
    subtitle_color = creative.get("subtitle_color", "&H00FFFF")
    prim_hex = creative.get("primary_hex", "0x38bdf8")

    # 1. Synthesize Voiceover with dynamic voice & pacing
    script_text = content_plan.get("voiceover_text") or content_plan.get("script") or "BeyondEra Tech frontier intelligence."
    voice_path = os.path.join(work_dir, "voice.mp3")
    v_path, voice_dur = synthesize_voiceover(script_text, voice=voice_name, rate=voice_rate, output_path=voice_path)

    # 2. Duration calibration
    if is_shorts:
        total_dur = max(30.0, min(58.0, voice_dur + 2.5))
    else:
        total_dur = max(60.0, min(120.0, voice_dur + 5.0))

    # 3. Subtitles with dynamic theme colors
    ass_path = os.path.join(work_dir, "subtitles.ass")
    generate_styled_ass_subtitles(
        script_text,
        voice_dur,
        ass_path,
        is_shorts=is_shorts,
        custom_primary=subtitle_color
    )

    # 4. Multi-Scene Visual Assembly (cuts between multiple diverse clips)
    visual_track = create_multi_scene_dynamic_track(
        content_plan=content_plan,
        total_dur=total_dur,
        work_dir=work_dir,
        all_clips=all_clips,
        is_shorts=is_shorts
    )

    # 5. Composite Final Video with Subtitles + Audio Mixing
    raw_title = content_plan.get("title", "BeyondEra Tech").replace(":", " - ")
    clean_title = "".join(c for c in raw_title if c.isalnum() or c in " -_").strip()
    if len(clean_title) > 38:
        clean_title = clean_title[:35] + "..."

    font_choice = FONT_BOLD if os.path.exists(FONT_BOLD) else "Sans"
    ass_escaped = ass_path.replace(":", "\\:").replace("'", "\\'")
    actual_ambient_music = resolve_ambient_music(music_profile)

    if is_shorts:
        vf_chain = (
            f"subtitles='{ass_escaped}', "
            f"drawtext=fontfile='{font_choice}':text='BEYONDERA TECH':fontcolor={prim_hex}:fontsize=36:x=(w-text_w)/2:y=130:box=1:boxcolor=0x070b14@0.90:boxborderw=16, "
            f"drawtext=fontfile='{font_choice}':text='{clean_title}':fontcolor=white:fontsize=38:x=(w-text_w)/2:y=205:box=1:boxcolor=0x000000@0.80:boxborderw=14"
        )
    else:
        vf_chain = (
            f"subtitles='{ass_escaped}', "
            f"drawtext=fontfile='{font_choice}':text='BEYONDERA TECH - SPECIAL INVESTIGATION':fontcolor={prim_hex}:fontsize=32:x=70:y=70:box=1:boxcolor=0x070b14@0.90:boxborderw=14, "
            f"drawtext=fontfile='{font_choice}':text='{clean_title}':fontcolor=white:fontsize=42:x=70:y=130:box=1:boxcolor=0x000000@0.80:boxborderw=14"
        )

    cmd_final = [
        "ffmpeg", "-y",
        "-i", visual_track,
        "-i", voice_path,
        "-stream_loop", "-1", "-i", actual_ambient_music,
        "-filter_complex",
        f"[0:v]{vf_chain}[vout]; "
        f"[1:a]volume=1.0[voice]; [2:a]volume=0.16[bg]; "
        f"[voice][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]",
        "-map", "[vout]", "-map", "[aout]",
        "-t", str(total_dur),
        "-c:v", "libx264", "-preset", "faster", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]
    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # 6. Run Post-Render QA Check
    qa_result = run_full_qa(
        output_path,
        expected_type="shorts" if is_shorts else "long",
        min_duration=28.0 if is_shorts else 50.0,
        max_duration=62.0 if is_shorts else 600.0,
        require_audio=True
    )

    return {
        "output_path": output_path,
        "total_duration": total_dur,
        "qa": qa_result,
        "is_shorts": is_shorts,
        "creative_direction": creative
    }


if __name__ == "__main__":
    from scripts.content_plan_engine import generate_content_plan
    plan = generate_content_plan(video_type="shorts")
    res = assemble_final_video(plan)
    print("Render Result:")
    print(json.dumps(res, indent=2, ensure_ascii=False))
