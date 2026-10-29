"""Generate upscaled crops of the hardware photos so small markings are legible.

Usage:  python tools/make_crops.py
Output: docs/derived/*.jpg   (regenerated from the originals, safe to delete)

Boxes are fractions of the (possibly rotated) source image: (left, top, right,
bottom).  ``rot`` rotates the source counter-clockwise before cropping, which is
handy for the phone photos that were taken with the board on its side.
"""
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "derived"
MAX_SIDE = 1100

# The product/app photo only exists as AVIF; ffmpeg decodes it for us.
AVIF_SRC = ROOT / "H10fc1b163d32467e8d186d39c303fd60A.avif"
AVIF_JPG = OUT / "app-photo.jpg"

# (name, source, (l, t, r, b), zoom, rotation)
CROPS = [
    # ---------- main PCB, component side (high-res.jpg, 2496x2521) ----------
    ("pcb_flash_and_jl", "high-res.jpg", (0.05, 0.24, 0.38, 0.42), 1.6, 0),
    ("pcb_jl_pins", "high-res.jpg", (0.22, 0.26, 0.40, 0.40), 3.0, 0),
    ("pcb_uln_left", "high-res.jpg", (0.22, 0.14, 0.42, 0.27), 2.5, 0),
    ("pcb_qfn_u5", "high-res.jpg", (0.44, 0.24, 0.62, 0.38), 3.0, 0),
    ("pcb_right_chips", "high-res.jpg", (0.62, 0.26, 0.86, 0.42), 2.5, 0),
    ("pcb_power_left", "high-res.jpg", (0.23, 0.55, 0.45, 0.82), 1.8, 0),
    ("pcb_power_right", "high-res.jpg", (0.44, 0.53, 0.72, 0.83), 1.8, 0),
    ("pcb_fpc_and_text", "high-res.jpg", (0.08, 0.45, 0.55, 0.60), 1.0, 0),
    ("pcb_buttons_left", "high-res.jpg", (0.10, 0.00, 0.45, 0.15), 1.3, 0),
    ("pcb_buttons_right", "high-res.jpg", (0.50, 0.00, 0.90, 0.15), 1.2, 0),
    # ---------- installed board, connectors + wires ----------
    # 20261028_195308 is still stored with the board on its side -> rot 90 (CCW)
    # makes the Chinese labels readable.  20261028_195243 is already upright.
    ("connector_labels", "20261028_195308.jpg", (0.32, 0.22, 0.55, 0.95), 3.0, 0),
    ("board_in_shell", "20261028_195308.jpg", (0.00, 0.22, 1.00, 0.98), 1.0, 90),
    ("connector_row", "20261028_195243.jpg", (0.12, 0.00, 1.00, 0.44), 1.5, 0),
    ("usb_and_fpc", "20261028_195243.jpg", (0.42, 0.26, 1.00, 1.00), 1.6, 0),
    ("label_plate", "20261028_195128.jpg", (0.10, 0.18, 0.90, 0.72), 1.6, 0),
    # ---------- product photo (catalog render) ----------
    # (product_hero is what the README shows at the top - tight crop around the
    #  machine so it still reads at a small display width.)
    ("product_hero", str(AVIF_JPG), (0.26, 0.28, 0.90, 0.94), 1.0, 0),
    ("product_arms", str(AVIF_JPG), (0.10, 0.15, 0.95, 0.75), 1.2, 0),
    ("product_head", str(AVIF_JPG), (0.25, 0.20, 0.70, 0.50), 1.8, 0),
]


def prepare_avif() -> None:
    """Decode the AVIF product render once (Pillow has no AVIF decoder here)."""
    if AVIF_JPG.exists():
        return
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(AVIF_SRC), str(AVIF_JPG)],
            check=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            "ffmpeg is needed to decode the AVIF product photo; install it and "
            "make sure it is on PATH."
        ) from exc


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prepare_avif()
    for name, src, (l, t, r, b), zoom, rot in CROPS:
        path = Path(src)
        if not path.exists():
            print(f"skip (missing): {src}")
            continue
        im = Image.open(path).convert("RGB")
        if rot:
            im = im.rotate(rot, expand=True)
        w, h = im.size
        crop = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
        if zoom != 1.0:
            crop = crop.resize(
                (int(crop.width * zoom), int(crop.height * zoom)), Image.LANCZOS
            )
        if max(crop.size) > MAX_SIDE:
            crop.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
        dest = OUT / f"{name}.jpg"
        crop.save(dest, quality=88)
        print(f"{dest.relative_to(ROOT)}  {crop.size}")


if __name__ == "__main__":
    main()
