import math
import os
import shutil
import subprocess
from typing import List, Optional
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

from app.models.schema import VideoAspect
from app.utils import utils


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Loads Vietnamese-compatible BeVietnamPro-Bold font or fallback."""
    font_file = os.path.join(utils.font_dir(), "BeVietnamPro-Bold.ttf")
    if os.path.isfile(font_file):
        try:
            return ImageFont.truetype(font_file, size)
        except Exception:
            pass

    # System fallbacks
    for cand in (
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.isfile(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _ease_out_cubic(x: float) -> float:
    return 1.0 - math.pow(1.0 - max(0.0, min(1.0, x)), 3.0)


def _ease_out_back(x: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1.0
    x_clamped = max(0.0, min(1.0, x))
    return 1.0 + c3 * math.pow(x_clamped - 1.0, 3.0) + c1 * math.pow(x_clamped - 1.0, 2.0)


def render_cinematic_motion_clip(
    output_path: str,
    title: str,
    subtitle: str = "",
    template: str = "architecture_flow",
    duration: float = 4.0,
    fps: int = 30,
    is_portrait: bool = False,
    scene_idx: int = 0,
) -> bool:
    """
    Renders a true frame-by-frame cinematic motion graphics animation video.
    Each frame contains dynamic moving elements: data packet pulses, real terminal typing,
    racing metric bars, counter ticking, and particle grid motion.
    """
    width = 1080 if is_portrait else 1920
    height = 1920 if is_portrait else 1080
    total_frames = max(1, int(duration * fps))

    ffmpeg_bin = utils.get_ffmpeg_binary()
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{width}x{height}",
        "-pix_fmt",
        "rgb24",
        "-r",
        str(fps),
        "-i",
        "-",
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]

    try:
        pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except Exception as e:
        logger.error(f"failed to spawn ffmpeg for motion clip: {e}")
        return False

    # Theme palette based on scene index or template
    palettes = [
        {"accent": (56, 189, 248), "accent_hex": "#38bdf8", "bg_dark": (10, 15, 30), "badge": "ARCHITECTURE FLOW"},
        {"accent": (168, 85, 247), "accent_hex": "#a855f7", "bg_dark": (18, 10, 32), "badge": "CODE & RUNTIME"},
        {"accent": (16, 185, 129), "accent_hex": "#10b981", "bg_dark": (6, 28, 20), "badge": "BENCHMARK & PERF"},
        {"accent": (245, 158, 11), "accent_hex": "#f59e0b", "bg_dark": (28, 18, 4), "badge": "VERSUS COMPARISON"},
        {"accent": (236, 72, 153), "accent_hex": "#ec4899", "bg_dark": (26, 8, 20), "badge": "CORE ECOSYSTEM"},
    ]
    cur_palette = palettes[scene_idx % len(palettes)]
    accent = cur_palette["accent"]

    # Typography
    font_badge = _get_font(20 if not is_portrait else 18)
    font_title = _get_font(46 if not is_portrait else 38)
    font_sub = _get_font(24 if not is_portrait else 20)
    font_card_head = _get_font(28 if not is_portrait else 22)
    font_mono = _get_font(24 if not is_portrait else 18)
    font_mono_small = _get_font(18 if not is_portrait else 15)

    clean_title = title.strip()
    if len(clean_title) > 42:
        clean_title = clean_title[:40] + "..."

    # Code script for terminal template
    code_lines = [
        f"// Initializing {clean_title}",
        "import { Engine, Runtime } from '@studioflow/core';",
        f"const pipeline = new Engine({{ target: '{clean_title[:20]}' }});",
        "await pipeline.benchmark({ fps: 60, latency: '1.2ms' });",
        "console.log('🚀 60 FPS Native Acceleration Ready');",
    ]
    full_code = "\n".join(code_lines)

    for frame_idx in range(total_frames):
        t = frame_idx / fps
        progress = t / duration

        # 1. Base canvas & Background
        img = Image.new("RGB", (width, height), cur_palette["bg_dark"])
        draw = ImageDraw.Draw(img)

        # 2. Moving Cyber Grid (drift with time t)
        grid_spacing = 70 if not is_portrait else 50
        offset_y = int(t * 35) % grid_spacing
        offset_x = int(t * 20) % grid_spacing
        grid_col = (25, 35, 55)

        for y in range(offset_y, height, grid_spacing):
            draw.line([(0, y), (width, y)], fill=grid_col, width=1)
        for x in range(offset_x, width, grid_spacing):
            draw.line([(x, 0), (x, height)], fill=grid_col, width=1)

        # 3. Ambient Floating Particles
        for p_idx in range(12):
            px = int((width * 0.1 + (p_idx * 153 + t * 40)) % (width * 0.9))
            py = int((height * 0.15 + (p_idx * 211 + math.sin(t + p_idx) * 30)) % (height * 0.8))
            p_size = 2 + (p_idx % 3)
            draw.ellipse([px - p_size, py - p_size, px + p_size, py + p_size], fill=accent)

        # 4. Header: Badge & Scene Title
        header_y = 60 if not is_portrait else 90
        badge_w = 260
        draw.rounded_rectangle(
            [width // 2 - badge_w // 2, header_y, width // 2 + badge_w // 2, header_y + 40],
            radius=20,
            fill=(15, 23, 42),
            outline=accent,
            width=2,
        )
        draw.text((width // 2, header_y + 20), cur_palette["badge"], fill=accent, font=font_badge, anchor="mm")

        # Title with smooth reveal & underline
        title_y = header_y + 70
        draw.text((width // 2, title_y), clean_title, fill=(255, 255, 255), font=font_title, anchor="mm")

        # Accent line expanding beneath title
        line_len = int(min(width - 200, 600) * _ease_out_cubic(min(1.0, progress * 2.0)))
        draw.line(
            [(width // 2 - line_len // 2, title_y + 35), (width // 2 + line_len // 2, title_y + 35)],
            fill=accent,
            width=3,
        )

        # 5. Template-Specific Dynamic Cinematic Motion
        card_y0 = title_y + 60
        card_y1 = height - (70 if not is_portrait else 120)
        card_x0 = 120 if not is_portrait else 50
        card_x1 = width - (120 if not is_portrait else 50)

        chosen_template = template
        if chosen_template == "architecture_flow" or (template == "auto" and scene_idx % 4 == 0):
            # ARCHITECTURE FLOW WITH STREAMING DATA PACKETS
            mid_y = (card_y0 + card_y1) // 2

            nodes = [
                {"label": "Client Layer", "icon": "📱", "color": (56, 189, 248)},
                {"label": clean_title[:18] or "Core Engine", "icon": "⚡", "color": (244, 114, 182)},
                {"label": "Native Runtime", "icon": "⚙️", "color": (16, 185, 129)},
            ]
            num_nodes = len(nodes)
            node_w = 220 if not is_portrait else 180
            node_h = 130 if not is_portrait else 100
            spacing = (card_x1 - card_x0 - num_nodes * node_w) // (num_nodes + 1)

            # Draw connecting circuit bus lines
            draw.line([(card_x0 + spacing + node_w // 2, mid_y), (card_x1 - spacing - node_w // 2, mid_y)], fill=(51, 65, 85), width=6)

            # Animated glowing data packets traveling along the circuit line
            for pkt_idx in range(4):
                pkt_offset = (progress * 1.5 + pkt_idx * 0.25) % 1.0
                pkt_x = int((card_x0 + spacing + node_w // 2) + (card_x1 - card_x0 - 2 * spacing - node_w) * pkt_offset)
                pkt_color = (250, 204, 21) if pkt_idx % 2 == 0 else accent
                # Trail
                draw.line([(pkt_x - 30, mid_y), (pkt_x, mid_y)], fill=pkt_color, width=4)
                # Head
                draw.ellipse([pkt_x - 10, mid_y - 10, pkt_x + 10, mid_y + 10], fill=pkt_color)

            # Draw Nodes
            for n_idx, node in enumerate(nodes):
                nx = card_x0 + spacing * (n_idx + 1) + node_w * n_idx
                ny = mid_y - node_h // 2
                is_active = (n_idx == 1)

                # Pulsing ripple ring for active node
                if is_active:
                    pulse_r = int(10 + math.sin(t * 6) * 6)
                    draw.rounded_rectangle(
                        [nx - pulse_r, ny - pulse_r, nx + node_w + pulse_r, ny + node_h + pulse_r],
                        radius=20,
                        outline=node["color"],
                        width=2,
                    )

                draw.rounded_rectangle([nx, ny, nx + node_w, ny + node_h], radius=16, fill=(15, 23, 42), outline=node["color"], width=3)
                draw.text((nx + node_w // 2, ny + 35), node["icon"], font=font_card_head, anchor="mm")
                draw.text((nx + node_w // 2, ny + node_h - 30), node["label"], fill=(255, 255, 255), font=font_mono_small, anchor="mm")

            # Telemetry readout at bottom of card
            status_text = f"STREAM: 60.0 FPS • THROUGHPUT: {int(850 + math.sin(t * 4) * 50)} MB/s • LATENCY: 1.1ms"
            draw.text((width // 2, card_y1 - 40), status_text, fill=(52, 211, 153), font=font_mono_small, anchor="mm")

        elif chosen_template == "code_terminal" or (template == "auto" and scene_idx % 4 == 1):
            # TERMINAL STREAMING CODE WITH TYPING ANIMATION
            term_pad = 20
            draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y1], radius=18, fill=(3, 7, 18), outline=(51, 65, 85), width=2)

            # Title bar
            bar_h = 44
            draw.rounded_rectangle([card_x0, card_y0, card_x1, card_y0 + bar_h], radius=18, fill=(15, 23, 42))
            draw.rectangle([card_x0, card_y0 + 20, card_x1, card_y0 + bar_h], fill=(15, 23, 42))
            # Traffic lights
            draw.ellipse([card_x0 + 18, card_y0 + 15, card_x0 + 32, card_y0 + 29], fill=(239, 68, 68))
            draw.ellipse([card_x0 + 40, card_y0 + 15, card_x0 + 54, card_y0 + 29], fill=(245, 158, 11))
            draw.ellipse([card_x0 + 62, card_y0 + 15, card_x0 + 76, card_y0 + 29], fill=(16, 185, 129))
            draw.text((card_x0 + 95, card_y0 + 22), "terminal — studioflow/runtime (zsh)", fill=(148, 163, 184), font=font_mono_small, anchor="lm")

            # Real typing progress
            type_progress = min(1.0, progress * 1.35)
            char_count = int(len(full_code) * type_progress)
            typed_text = full_code[:char_count]

            # Render code lines with syntax coloring
            lines = typed_text.split("\n")
            cur_y = card_y0 + bar_h + 24
            line_spacing = 42 if not is_portrait else 34

            for l_i, line in enumerate(lines):
                c = (226, 232, 240)
                if line.startswith("//"):
                    c = (100, 116, 139)
                elif line.startswith("import") or line.startswith("const") or line.startswith("await"):
                    c = (244, 114, 182)
                elif "console.log" in line:
                    c = (52, 211, 153)

                draw.text((card_x0 + 30, cur_y), line, fill=c, font=font_mono)

                # Blinking cursor on the active line
                if l_i == len(lines) - 1 and (int(t * 3.5) % 2 == 0):
                    bbox = draw.textbbox((card_x0 + 30, cur_y), line, font=font_mono)
                    cx = bbox[2] + 4
                    draw.rectangle([cx, cur_y + 2, cx + 10, cur_y + line_spacing - 10], fill=accent)

                cur_y += line_spacing

            # Streaming terminal output when typing is done
            if progress > 0.65:
                draw.line([(card_x0, card_y1 - 60), (card_x1, card_y1 - 60)], fill=(30, 41, 59), width=1)
                draw.text(
                    (card_x0 + 30, card_y1 - 32),
                    "✔ Compiled successfully in 142ms • Ready for production",
                    fill=(52, 211, 153),
                    font=font_mono_small,
                    anchor="lm",
                )

        elif chosen_template == "benchmark_metrics" or (template == "auto" and scene_idx % 4 == 2):
            # BENCHMARK WITH RACING BARS AND COUNTING NUMBERS
            metrics = [
                {"label": "Frame Rate Stability", "target": 60.0, "unit": "FPS", "color": (56, 189, 248)},
                {"label": "Memory Footprint", "target": 38.4, "unit": "MB", "color": (16, 185, 129)},
                {"label": "Execution Overhead", "target": 1.2, "unit": "ms", "color": (245, 158, 11)},
            ]

            card_h = (card_y1 - card_y0 - 40) // 3
            for m_i, m in enumerate(metrics):
                my0 = card_y0 + m_i * (card_h + 15)
                my1 = my0 + card_h
                draw.rounded_rectangle([card_x0, my0, card_x1, my1], radius=16, fill=(15, 23, 42), outline=(30, 41, 59), width=1)

                # Racing progress value
                val_progress = _ease_out_cubic(min(1.0, progress * 1.4))
                cur_val = m["target"] * val_progress

                # Label & live counter
                draw.text((card_x0 + 25, my0 + 25), m["label"], fill=(148, 163, 184), font=font_sub)
                val_str = f"{cur_val:.1f} {m['unit']}"
                draw.text((card_x1 - 25, my0 + 25), val_str, fill=m["color"], font=font_card_head, anchor="ra")

                # Racing progress bar
                bar_x0 = card_x0 + 25
                bar_x1 = card_x1 - 25
                bar_y0 = my1 - 25
                bar_h_px = 10
                draw.rounded_rectangle([bar_x0, bar_y0, bar_x1, bar_y0 + bar_h_px], radius=5, fill=(30, 41, 59))

                fill_w = int((bar_x1 - bar_x0) * val_progress * 0.95)
                if fill_w > 5:
                    draw.rounded_rectangle([bar_x0, bar_y0, bar_x0 + fill_w, bar_y0 + bar_h_px], radius=5, fill=m["color"])
                    # Glowing laser head on the bar
                    draw.ellipse([bar_x0 + fill_w - 6, bar_y0 - 2, bar_x0 + fill_w + 6, bar_y0 + bar_h_px + 2], fill=(255, 255, 255))

        else:
            # VERSUS BATTLE / COMPARISON CARDS
            parts = clean_title.split(" vs " if " vs " in clean_title.lower() else " và ")
            side_a = parts[0].strip() if len(parts) > 0 else "Platform A"
            side_b = parts[1].strip() if len(parts) > 1 else "Platform B"

            mid_x = width // 2
            card_w = (width - 340) // 2 if not is_portrait else width - 100

            # Slide-in animation for left & right cards
            slide_in = _ease_out_back(min(1.0, progress * 1.5))
            offset_slide = int((1.0 - slide_in) * 200)

            # Left Card (Blue)
            left_x0 = card_x0 - offset_slide
            left_x1 = mid_x - 60 - offset_slide
            draw.rounded_rectangle([left_x0, card_y0, left_x1, card_y1], radius=20, fill=(15, 23, 42), outline=(56, 189, 248), width=2)
            draw.text((left_x0 + 30, card_y0 + 35), side_a, fill=(56, 189, 248), font=font_card_head)
            draw.text((left_x0 + 30, card_y0 + 85), "✓ Unified JavaScript Ecosystem\n✓ High Dev Ergonomics\n✓ Fast Prototyping", fill=(148, 163, 184), font=font_sub)

            # Right Card (Purple)
            right_x0 = mid_x + 60 + offset_slide
            right_x1 = card_x1 + offset_slide
            draw.rounded_rectangle([right_x0, card_y0, right_x1, card_y1], radius=20, fill=(15, 23, 42), outline=(168, 85, 247), width=2)
            draw.text((right_x0 + 30, card_y0 + 35), side_b, fill=(168, 85, 247), font=font_card_head)
            draw.text((right_x0 + 30, card_y0 + 85), "✓ Skia / Impeller Rendering\n✓ Native 60-120 FPS Speed\n✓ Robust Type Safety", fill=(148, 163, 184), font=font_sub)

            # Center VS Shockwave Badge
            vs_scale = _ease_out_back(min(1.0, max(0.0, (progress - 0.2) * 2.0)))
            vs_r = int(45 * vs_scale)
            if vs_r > 5:
                # Shockwave ring
                ring_r = max(6, int(vs_r + math.sin(t * 5) * 8))
                draw.ellipse([mid_x - ring_r, (card_y0 + card_y1) // 2 - ring_r, mid_x + ring_r, (card_y0 + card_y1) // 2 + ring_r], outline=(239, 68, 68), width=2)
                # Badge
                draw.ellipse([mid_x - vs_r, (card_y0 + card_y1) // 2 - vs_r, mid_x + vs_r, (card_y0 + card_y1) // 2 + vs_r], fill=(239, 68, 68))
                draw.text((mid_x, (card_y0 + card_y1) // 2), "VS", fill=(255, 255, 255), font=font_card_head, anchor="mm")

        # 6. Pipe raw RGB24 frame directly to FFmpeg
        pipe.stdin.write(img.tobytes())

    try:
        pipe.stdin.close()
        pipe.wait(timeout=10)
    except Exception as e:
        logger.error(f"error finalizing ffmpeg video pipe: {e}")
        return False

    return os.path.isfile(output_path) and os.path.getsize(output_path) > 1000


def generate_html_motion_videos(
    task_id: str,
    search_terms: List[str],
    video_aspect: VideoAspect = VideoAspect.portrait,
    audio_duration: float = 0.0,
    max_clip_duration: int = 5,
    html_motion_template: Optional[str] = "architecture_flow",
    html_motion_code: Optional[str] = None,
) -> List[str]:
    """
    Renders pure dynamic cinematic tech animation videos ("dạng video phim")
    with 60/30 FPS frame-by-frame data streams, live terminal typing, and racing metrics.
    """
    task_dir = utils.task_dir(task_id)
    os.makedirs(task_dir, exist_ok=True)

    is_portrait = video_aspect in (VideoAspect.portrait, VideoAspect.square)
    template = html_motion_template or "architecture_flow"

    terms = [t for t in search_terms if t.strip()]
    if not terms:
        terms = ["Tech Architecture", "Code Implementation", "Benchmark Comparison", "Modern Pipeline"]

    needed_clips = max(len(terms), int(audio_duration // max_clip_duration) + 1)
    while len(terms) < needed_clips:
        terms.extend(terms[: needed_clips - len(terms)])

    logger.info(
        f"rendering {len(terms)} cinematic motion film clips for task {task_id} "
        f"(duration={audio_duration}s, aspect={video_aspect}, template={template})"
    )

    rendered_video_clips: List[str] = []

    for idx, term in enumerate(terms):
        clip_path = os.path.join(task_dir, f"html_motion_clip_{idx + 1}.mp4")

        # Vary templates per scene so the whole video feels like an engaging multi-scene film!
        scene_template = template
        if template in ("auto", "architecture_flow") and len(terms) > 1:
            scene_templates = ["architecture_flow", "code_terminal", "benchmark_metrics", "versus_battle"]
            scene_template = scene_templates[idx % len(scene_templates)]

        success = render_cinematic_motion_clip(
            output_path=clip_path,
            title=term,
            subtitle=f"Scene {idx + 1} • High Performance Vector Animation",
            template=scene_template,
            duration=float(max_clip_duration),
            fps=30,
            is_portrait=is_portrait,
            scene_idx=idx,
        )

        if success and os.path.isfile(clip_path):
            rendered_video_clips.append(clip_path)
            logger.info(f"generated cinematic motion video clip {idx + 1}: {clip_path}")
        else:
            logger.warning(f"failed to generate motion video clip for scene {idx + 1}")

    # Persist material sources to script.json
    try:
        from app.services import task_artifacts
        material_sources = [
            {
                "provider": "html_animation",
                "local_file": os.path.basename(clip),
                "duration": max_clip_duration,
                "search_term": terms[min(i, len(terms) - 1)],
            }
            for i, clip in enumerate(rendered_video_clips)
        ]
        task_artifacts.patch_script_data(task_id, material_sources=material_sources)
    except Exception as e:
        logger.warning(f"failed to patch material_sources for html motion: {e}")

    return rendered_video_clips
