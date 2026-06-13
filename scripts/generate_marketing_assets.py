#!/usr/bin/env python3
"""Generate marketing screenshots and demo video for remote-run-llm."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "marketing"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#0f1117"
PANEL = "#161b22"
BORDER = "#30363d"
GREEN = "#3fb950"
CYAN = "#79c0ff"
YELLOW = "#d29922"
MAGENTA = "#d2a8ff"
ORANGE = "#ffa657"
TEXT = "#e6edf3"
MUTED = "#8b949e"
RED = "#f85149"

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def draw_window(
    title: str,
    lines: list[tuple[str, str]],
    *,
    width: int = 1400,
    subtitle: str | None = None,
) -> Image.Image:
    font = load_font(22)
    title_font = load_font(26)
    pad = 28
    line_height = 34
    header_h = 72 if subtitle else 56
    height = header_h + pad * 2 + line_height * len(lines) + 20

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # Window chrome
    draw.rounded_rectangle(
        (24, 24, width - 24, height - 24),
        radius=16,
        fill=PANEL,
        outline=BORDER,
        width=2,
    )
    draw.ellipse((44, 40, 58, 54), fill=RED)
    draw.ellipse((68, 40, 82, 54), fill=YELLOW)
    draw.ellipse((92, 40, 106, 54), fill=GREEN)
    draw.text((130, 36), title, font=title_font, fill=TEXT)
    if subtitle:
        draw.text((130, 66), subtitle, font=font, fill=MUTED)

    # Content area
    y = 24 + header_h + pad
    for text, color in lines:
        draw.text((48, y), text, font=font, fill=color)
        y += line_height

    return img


def save_demo_run() -> Path:
    lines = [
        ("$ pip install remote-run-llm", CYAN),
        ("Successfully installed remote-run-llm-0.1.1", GREEN),
        ("", TEXT),
        ("$ python restart_nginx.py", CYAN),
        ("", TEXT),
        ("from remote_run import run", MAGENTA),
        ('result = run("203.0.113.10", "sudo systemctl restart nginx",', TEXT),
        ('              user="ubuntu", key="~/.ssh/id_ed25519")', TEXT),
        ("print(result.stdout)", TEXT),
        ("", TEXT),
        ("● Connected to 203.0.113.10", GREEN),
        ("● Command finished (exit 0)", GREEN),
        ("", TEXT),
        ("nginx restarted successfully", TEXT),
    ]
    img = draw_window(
        "remote-run-llm — run a remote command",
        lines,
        subtitle="One function. No Paramiko boilerplate.",
    )
    path = OUT / "demo-run-command.png"
    img.save(path, quality=95)
    return path


def save_demo_upload() -> Path:
    lines = [
        ("$ python deploy.py", CYAN),
        ("", TEXT),
        ("from remote_run import upload", MAGENTA),
        ('upload("203.0.113.10", "dist/app.zip", "/var/www/app.zip",', TEXT),
        ('       user="deploy", key="~/.ssh/id_ed25519")', TEXT),
        ("", TEXT),
        ("● Connected to 203.0.113.10", GREEN),
        ("● Uploaded dist/app.zip → /var/www/app.zip (2.4 MB)", GREEN),
        ("", TEXT),
        ("Deploy complete.", TEXT),
    ]
    img = draw_window(
        "remote-run-llm — upload a file",
        lines,
        subtitle="SFTP without open_sftp() ceremony.",
    )
    path = OUT / "demo-upload-file.png"
    img.save(path, quality=95)
    return path


def save_demo_comparison() -> Path:
    width = 1600
    height = 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)
    title_font = load_font(30)
    font = load_font(18)
    small = load_font(17)

    draw.text(
        (width // 2 - 280, 30), "Paramiko vs remote-run-llm", font=title_font, fill=TEXT
    )

    panels = [
        (
            40,
            "Raw Paramiko (what LLMs generate)",
            RED,
            [
                "import paramiko",
                "client = paramiko.SSHClient()",
                "client.set_missing_host_key_policy(paramiko.AutoAddPolicy())",
                "client.connect('203.0.113.10', username='ubuntu',",
                "    key_filename='~/.ssh/id_rsa')  # wrong key type?",
                "stdin, stdout, stderr = client.exec_command('df -h')",
                "out = stdout.read()  # bytes, not str",
                "exit_code = stdout.channel.recv_exit_status()",
                "client.close()  # easy to forget",
                "",
                "✗ host keys  ✗ key types  ✗ bytes  ✗ exit code",
            ],
        ),
        (
            820,
            "remote-run-llm (what you actually wanted)",
            GREEN,
            [
                "from remote_run import run",
                "",
                'result = run("203.0.113.10", "df -h",',
                '              user="ubuntu", key="~/.ssh/id_ed25519")',
                "",
                "print(result.stdout)   # decoded string",
                "print(result.exit_code)",
                "if result.failed:",
                "    raise SystemExit(result.stderr)",
                "",
                "✓ auto host keys  ✓ key detect  ✓ strings  ✓ exit code",
            ],
        ),
    ]

    for x, heading, accent, code_lines in panels:
        draw.rounded_rectangle(
            (x, 90, x + 740, 860), radius=16, fill=PANEL, outline=BORDER, width=2
        )
        draw.text((x + 24, 110), heading, font=font, fill=accent)
        y = 160
        for line in code_lines:
            color = MUTED if line.startswith("✗") or line.startswith("✓") else TEXT
            if line.startswith("from") or line.startswith("import"):
                color = MAGENTA
            if "result" in line and "=" in line:
                color = CYAN
            draw.text((x + 24, y), line, font=small, fill=color)
            y += 30

    path = OUT / "demo-paramiko-comparison.png"
    img.save(path, quality=95)
    return path


def save_hero_banner() -> Path:
    width, height = 1600, 900
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # Gradient-ish bands
    for i in range(height):
        t = i / height
        r = int(15 + 10 * math.sin(t * math.pi))
        g = int(17 + 8 * t)
        b = int(23 + 20 * (1 - t))
        draw.line([(0, i), (width, i)], fill=(r, g, b))

    title_font = load_font(54)
    subtitle_font = load_font(28)
    tag_font = load_font(24)

    draw.rounded_rectangle(
        (80, 120, width - 80, height - 120),
        radius=24,
        fill=PANEL,
        outline=BORDER,
        width=2,
    )
    draw.text((130, 180), "remote-run-llm", font=title_font, fill=TEXT)
    draw.text(
        (130, 260),
        "SSH from Python in one line — no Paramiko boilerplate",
        font=subtitle_font,
        fill=MUTED,
    )

    code_font = load_font(26)
    code_lines = [
        ("pip install remote-run-llm", CYAN),
        ("from remote_run import run, upload, download", MAGENTA),
        ('run("203.0.113.10", "sudo systemctl restart nginx", user="ubuntu")', TEXT),
    ]
    y = 360
    for line, color in code_lines:
        draw.text((130, y), line, font=code_font, fill=color)
        y += 48

    tags = [
        "run()",
        "upload()",
        "download()",
        "run_many()",
        "LLM-friendly",
        "typed API",
    ]
    x = 130
    y = 560
    for tag in tags:
        tw = draw.textlength(tag, font=tag_font)
        draw.rounded_rectangle(
            (x - 8, y - 6, x + tw + 8, y + 34), radius=12, outline=BORDER, fill=BG
        )
        draw.text(
            (x, y), tag, font=tag_font, fill=ORANGE if tag.endswith("()") else GREEN
        )
        x += tw + 28

    path = OUT / "hero-banner.png"
    img.save(path, quality=95)
    return path


def build_video(frames: list[Path], output: Path, *, duration_per: float = 4.0) -> None:
    """Stitch PNG frames into an MP4 with crossfade-like holds using ffmpeg."""
    list_file = OUT / "frames.txt"
    with list_file.open("w") as fh:
        for frame in frames:
            fh.write(f"file '{frame}'\n")
            fh.write(f"duration {duration_per}\n")
        fh.write(f"file '{frames[-1]}'\n")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-vf",
            "scale=1600:900:force_original_aspect_ratio=decrease,pad=1600:900:(ow-iw)/2:(oh-ih)/2:color=0x0f1117",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
        capture_output=True,
    )


def main() -> None:
    frames = [
        save_hero_banner(),
        save_demo_run(),
        save_demo_upload(),
        save_demo_comparison(),
    ]
    video_path = OUT / "remote-run-llm-demo.mp4"
    build_video(frames, video_path)
    print("Generated:")
    for path in [*frames, video_path]:
        print(f"  {path}")


if __name__ == "__main__":
    main()
