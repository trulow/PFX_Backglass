#!/usr/bin/env python3
"""
Pinball FX Backglass Generator
==============================

Takes the template at Template/1.Table.png and composites each PNG in src/
beneath it, writing finished backglass images to modified/.

The script asks at startup for two choices:

1.  Fit mode — how the source artwork fills the template's transparent area.
       Fit / Contain  : show the whole image (black bars on sides if needed)
       Stretch        : fill the area, distorting the image if needed
       Cover          : fill the area by cropping the top/bottom

2.  Output size — the final image resolution.
       1080p : 1920 x 1080  (matches the template's native resolution)
       4K    : 3840 x 2160  (template is upscaled 2x)

You can pass either choice as a CLI flag to skip the prompt:

    python3 make_backglass.py --fit --1080
    python3 make_backglass.py --stretch --4k
    python3 make_backglass.py --cover

Re-running is safe; existing files in modified/ are overwritten.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from PIL import Image

# --- paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "Template" / "1.Table.png"
SRC_DIR = ROOT / "src"
OUT_DIR = ROOT / "modified"

# --- configuration -----------------------------------------------------------
# Geometry is defined relative to the native 1920x1080 template, then scaled
# at runtime when the user requests 4K output.
NATIVE_CANVAS = (1920, 1080)        # template's native size
NATIVE_BOX = (0, 0, 1920, 878)      # left, top, right, bottom of artwork area
BACKGROUND_COLOR = (0, 0, 0, 255)   # behind any letterbox bars

# Map user-facing fit-mode names -> internal mode used by fit_image()
MODE_ALIASES = {
    "fit": "contain", "contain": "contain", "f": "contain", "1": "contain",
    "stretch": "stretch", "s": "stretch", "2": "stretch",
    "cover": "cover", "crop": "cover", "c": "cover", "3": "cover",
}

# Map user-facing size names -> (width, height)
SIZE_PRESETS = {
    "1080p": (1920, 1080),
    "1080":  (1920, 1080),
    "hd":    (1920, 1080),
    "1":     (1920, 1080),
    "4k":    (3840, 2160),
    "2160p": (3840, 2160),
    "2160":  (3840, 2160),
    "uhd":   (3840, 2160),
    "2":     (3840, 2160),
}


def prompt_fit_mode() -> str:
    """Ask the user how to fit the source artwork. Returns an internal mode name."""
    print("How should the source artwork fit the template?")
    print("  [1] Fit     — show the whole image (black bars on sides if needed)")
    print("  [2] Stretch — fill the area, distorting the image if needed")
    print("  [3] Cover   — fill the area by cropping the top/bottom slightly")
    while True:
        try:
            choice = input("Choice [1/2/3, default 1]: ").strip().lower()
        except EOFError:
            choice = ""
        if choice == "":
            return "contain"
        if choice in MODE_ALIASES:
            return MODE_ALIASES[choice]
        print(f"  Sorry, '{choice}' isn't a valid option. Try 1, 2, or 3.")


def prompt_output_size() -> tuple[int, int]:
    """Ask the user what final size they want. Returns (width, height)."""
    print("What output resolution do you want?")
    print("  [1] 1080p  — 1920 x 1080  (template's native size)")
    print("  [2] 4K     — 3840 x 2160  (upscaled 2x)")
    while True:
        try:
            choice = input("Choice [1/2, default 1]: ").strip().lower()
        except EOFError:
            choice = ""
        if choice == "":
            return SIZE_PRESETS["1080p"]
        if choice in SIZE_PRESETS:
            return SIZE_PRESETS[choice]
        print(f"  Sorry, '{choice}' isn't a valid option. Try 1 or 2.")


def parse_args(argv: list[str]) -> tuple[str | None, tuple[int, int] | None]:
    """Read CLI flags. Each value is None if the user should be prompted."""
    parser = argparse.ArgumentParser(
        description="Composite src/*.png with the backglass template into modified/.",
        add_help=True,
    )

    fit_group = parser.add_mutually_exclusive_group()
    fit_group.add_argument("--fit", "--contain", dest="mode", action="store_const",
                           const="contain", help="Fit the whole image (default).")
    fit_group.add_argument("--stretch", dest="mode", action="store_const",
                           const="stretch", help="Stretch to fill the area.")
    fit_group.add_argument("--cover", dest="mode", action="store_const",
                           const="cover", help="Cover the area by cropping.")

    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument("--1080", "--1080p", "--hd", dest="size",
                            action="store_const", const=SIZE_PRESETS["1080p"],
                            help="Output at 1920x1080 (default).")
    size_group.add_argument("--4k", "--2160p", "--uhd", dest="size",
                            action="store_const", const=SIZE_PRESETS["4k"],
                            help="Output at 3840x2160.")

    args = parser.parse_args(argv)
    return args.mode, args.size


def fit_image(img: Image.Image, box_w: int, box_h: int, mode: str) -> Image.Image:
    """Resize *img* to fit a box of (box_w, box_h) according to *mode*.

    Returns an RGBA image exactly box_w x box_h with letterbox padding when
    needed (contain) or with the source cropped to fit (cover).
    """
    img = img.convert("RGBA")
    src_w, src_h = img.size
    canvas = Image.new("RGBA", (box_w, box_h), BACKGROUND_COLOR)

    if mode == "stretch":
        return img.resize((box_w, box_h), Image.LANCZOS)

    src_ratio = src_w / src_h
    box_ratio = box_w / box_h

    if mode == "cover":
        # scale so the image fully covers the box, then center-crop
        if src_ratio > box_ratio:
            new_h = box_h
            new_w = int(round(src_ratio * new_h))
        else:
            new_w = box_w
            new_h = int(round(new_w / src_ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - box_w) // 2
        top = (new_h - box_h) // 2
        return resized.crop((left, top, left + box_w, top + box_h))

    # default: contain — fit whole image inside the box, letterbox the rest
    if src_ratio > box_ratio:
        new_w = box_w
        new_h = int(round(new_w / src_ratio))
    else:
        new_h = box_h
        new_w = int(round(src_ratio * new_h))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    offset = ((box_w - new_w) // 2, (box_h - new_h) // 2)
    canvas.paste(resized, offset)
    return canvas


def build_backglass(
    source_path: Path,
    template: Image.Image,
    mode: str,
    canvas_size: tuple[int, int],
    box: tuple[int, int, int, int],
) -> Image.Image:
    """Composite a single source PNG with the template at the requested size."""
    src = Image.open(source_path)
    box_l, box_t, box_r, box_b = box
    box_w, box_h = box_r - box_l, box_b - box_t

    fitted = fit_image(src, box_w, box_h, mode)

    canvas = Image.new("RGBA", canvas_size, BACKGROUND_COLOR)
    canvas.paste(fitted, (box_l, box_t))
    canvas.alpha_composite(template)  # template's footer overlays the bottom
    return canvas


def scale_box(box: tuple[int, int, int, int], scale_x: float, scale_y: float
              ) -> tuple[int, int, int, int]:
    l, t, r, b = box
    return (
        int(round(l * scale_x)),
        int(round(t * scale_y)),
        int(round(r * scale_x)),
        int(round(b * scale_y)),
    )


def main(argv: list[str] | None = None) -> None:
    if not TEMPLATE_PATH.exists():
        raise SystemExit(f"Template not found: {TEMPLATE_PATH}")

    mode, size = parse_args(sys.argv[1:] if argv is None else argv)
    if mode is None:
        mode = prompt_fit_mode()
    if size is None:
        size = prompt_output_size()

    print(f"Using fit mode: {mode}")
    print(f"Output size:    {size[0]}x{size[1]}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    if template.size != NATIVE_CANVAS:
        template = template.resize(NATIVE_CANVAS, Image.LANCZOS)
    if size != NATIVE_CANVAS:
        template = template.resize(size, Image.LANCZOS)

    scale_x = size[0] / NATIVE_CANVAS[0]
    scale_y = size[1] / NATIVE_CANVAS[1]
    box = scale_box(NATIVE_BOX, scale_x, scale_y)

    sources = sorted(p for p in SRC_DIR.glob("*.png") if p.is_file())
    if not sources:
        print(f"No PNGs found in {SRC_DIR}")
        return

    print(f"Processing {len(sources)} file(s) -> {OUT_DIR}")
    for src_path in sources:
        out_path = OUT_DIR / src_path.name
        try:
            result = build_backglass(src_path, template, mode, size, box)
            result.save(out_path, "PNG")
            print(f"  ok  {src_path.name}")
        except Exception as exc:
            print(f"  FAIL {src_path.name}: {exc}")


if __name__ == "__main__":
    main()
