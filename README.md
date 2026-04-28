# FX Backglass

Automated generator for Pinball FX backglass images. The script takes a
template (with a transparent artwork area and a Zen Studios + Pinball FX
footer) and composites your table artwork PNGs into it, producing finished
1920×1080 backglass images.

## Folder layout

```
FX Backglass/
├── Template/
│   └── 1.Table.png      # 1920x1080 PNG with a transparent top area and an opaque footer
├── src/                 # input artwork PNGs (any size)
├── modified/            # finished backglass images written here
├── make_backglass.py    # the script
└── README.md            # this file
```

The template's transparent area is `1920 × 878` (the top of the canvas).
The bottom `1920 × 202` carries the Zen Studios logo, the table title
window, and the Pinball FX logo.

## Requirements

- Python 3.8 or newer
- [Pillow](https://pypi.org/project/Pillow/)

Install Pillow with:

```
python3 -m pip install Pillow
```

On newer macOS Python installs you may see an "externally-managed-environment"
error. If that happens, use one of these instead:

```
python3 -m pip install --user Pillow
python3 -m pip install --break-system-packages Pillow
```

If `python3` itself isn't found, install Python from
[python.org](https://www.python.org/downloads/) or via Homebrew
(`brew install python`).

## Usage

Drop your source artwork PNGs into `src/`, then run:

```
python3 make_backglass.py
```

The script will ask two questions. First, how to fit each source image into
the template's transparent area:

```
How should the source artwork fit the template?
  [1] Fit     — show the whole image (black bars on sides if needed)
  [2] Stretch — fill the area, distorting the image if needed
  [3] Cover   — fill the area by cropping the top/bottom slightly
Choice [1/2/3, default 1]:
```

Then, what final resolution to render at:

```
What output resolution do you want?
  [1] 1080p  — 1920 x 1080  (template's native size)
  [2] 4K     — 3840 x 2160  (upscaled 2x)
Choice [1/2, default 1]:
```

Pressing Enter on either prompt accepts option `[1]`. Finished images are
written to `modified/` using the same filename as the source.

### Skipping the prompts

You can pass either choice as a flag to skip the matching prompt — useful
for batch runs or shell scripts. Flags can be combined:

```
python3 make_backglass.py --fit --1080
python3 make_backglass.py --stretch --4k
python3 make_backglass.py --cover           # still asks for size
python3 make_backglass.py --4k              # still asks for fit mode
```

Available flags:

- Fit mode: `--fit` (alias `--contain`), `--stretch`, `--cover`
- Output size: `--1080` (aliases `--1080p`, `--hd`), `--4k` (aliases
  `--2160p`, `--uhd`)

## Fit modes at a glance

- **Fit (contain)** — preserves the source aspect ratio. The whole source
  image is visible inside the transparent area; any leftover space on the
  sides is filled with black.
- **Stretch** — resizes the source to exactly match the transparent area.
  No cropping or bars, but the image is distorted slightly because the
  source is 16:9 while the area is roughly 2.19:1.
- **Cover** — preserves aspect ratio by filling the entire area, cropping
  whatever spills outside. A small slice off the top and bottom of the
  source is lost.

## How it works

1. Load `Template/1.Table.png` and ensure it's `1920 × 1080`. If 4K output
   was requested, upscale the template to `3840 × 2160` and scale the
   artwork-area coordinates by 2x.
2. For each PNG in `src/`:
   - Resize it to fit the artwork area using the chosen fit mode.
   - Paste it onto a fresh black canvas at the chosen output resolution.
   - Alpha-composite the template on top so the footer overlays the bottom.
   - Save the result to `modified/<filename>.png`.

Re-running the script overwrites any matching files in `modified/`. Source
files are never modified.

## Tweaking

If the template ever changes shape, edit the `NATIVE_BOX` and
`NATIVE_CANVAS` constants near the top of `make_backglass.py`. New fit
modes can be added by extending `MODE_ALIASES` and `fit_image()`. New
output sizes can be added by extending `SIZE_PRESETS`.
