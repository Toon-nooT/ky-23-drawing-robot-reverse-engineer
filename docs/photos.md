# Photos and derived crops

## Originals

| File | Pixels | Subject |
|---|---|---|
| `high-res.jpg` | 2496 × 2521 | **Primary evidence.** Component side of the main PCB, everything readable. |
| `20261028_195128.jpg` | 1071 × 803 | Close-up of the regulatory label on the shell (model, batch, power, battery, manufacturer, CE/FC/RoHS marks), with the installed board visible above it. |
| `20261028_195243.jpg` | 695 × 595 | Installed PCB from the connector side, upright: 4-pin motor headers with wire colours, USB-C, `LED1`/`红线`, `J16` FPC ribbon, `U11`. |
| `20261028_195308.jpg` | 803 × 1071 | PCB connector edge, stored **sideways**: Chinese labels `电池` / `电机3` / `电机2` / `电机1` / `喇叭`, black gear hub, blue cover. |
| `H10fc1b163d32467e8d186d39c303fd60A.avif` | 1920 × 1920 | Product render used for the mechanical analysis (Pillow cannot open AVIF, so it is decoded with ffmpeg). |

## Derived crops

Everything in `docs/derived/` is **generated** — delete the directory at any time
and rebuild it:

```powershell
python tools/make_crops.py
```

The script:

* decodes the AVIF product photo to `docs/derived/app-photo.jpg` via `ffmpeg`
  (must be on `PATH`),
* crops by *fractional* boxes `(left, top, right, bottom)` so it keeps working
  if a photo is replaced with a higher-resolution shot of the same subject,
* optionally rotates a photo first (the 20261028_195308.jpg shot is still stored
  with the board on its side), and
* caps output at 1100 px on the long edge and writes JPEG (~q88) so the files
  stay small enough to inspect.

To inspect a new detail, add one line to `CROPS` in `tools/make_crops.py`
instead of hand-cropping:

```python
("pcb_my_new_detail", "high-res.jpg", (0.30, 0.30, 0.45, 0.40), 3.0, 0),
#  name               source          l, t, r, b            zoom  rotation°
```

## Crop index

| Crop | Shows |
|---|---|
| `pcb_flash_and_jl` | `KH25V8035` SOP-8 + the `JL` JieLi chip with its full marking. |
| `pcb_jl_pins` | Tight shot of the `JL` chip — for counting pins. |
| `pcb_uln_left` | Left `ULN2003` (866350H) and the button row. |
| `pcb_qfn_u5` | The unmarked QFN (`U5`) and the `J15` test pads. |
| `pcb_right_chips` | `Q6` (SOP-8), `Q51` (`1AM`), `D7`/`D8`, `R22`/`R23`. |
| `pcb_power_left` | Second `KH25V8035` and `U3` (`4056A`) charger. |
| `pcb_power_right` | `FB1` 4R7 inductor, 220 µF/16 V cap, `U10` DC-DC. |
| `pcb_fpc_and_text` | `J16` FPC connector + the `ZFX_KY-23_L_V2.1_2026_0427` silk screen. |
| `pcb_buttons_left` / `pcb_buttons_right` | Tactile switches, `LED3`/`LED4`, `R36`/`R37`. |
| `connector_labels` | Chinese header labels on the PCB edge, zoomed (still vertical). |
| `connector_row` | Motor headers, silk pin numbers and wire colours. |
| `usb_and_fpc` | USB-C receptacle, `J16` FPC connector + ribbon, `LED1`, `红线`, `U11`. |
| `label_plate` | Regulatory label: model, batch, power, battery, manufacturer, compliance marks. |
| `board_in_shell` | The PCB as installed behind the shell, rotated upright (from the sideways `20261028_195308.jpg`). |
| `product_hero` | Tight crop of the whole machine — **the image shown at the top of the README**. |
| `product_arms` / `product_head` | Product render: linkage geometry and head details. |

## Privacy / metadata audit

Checked before publishing this repo (2026-10-29), because phone photos often
carry more than the picture:

| Item | Result |
|---|---|
| GPS coordinates | **none anywhere** — no `GPSInfo` data, no latitude/longitude tags or strings in any file |
| Files with *any* metadata | only `20261028_195308.jpg`, the untouched camera original |
| `20261028_195128.jpg`, `20261028_195243.jpg` | cropped/re-saved on 2026-10-29 and **completely stripped** — plain JFIF: no EXIF, no XMP, no ICC profile, no MPO |
| `high-res.jpg` | **no EXIF at all** (plain JFIF) |
| `H10fc1b…A.avif` | **no metadata**; only the AVIF brand tags |
| `docs/derived/*.jpg` | written by Pillow, **no metadata** |
| Camera make / model / serial | **not present** (no `Make`, `Model`, `BodySerialNumber`, `LensModel`) |
| Owner / artist / copyright | **not present** |
| Software tag | `Google` in `195308.jpg` only (Android camera pipeline), nothing identifying |
| `DateTimeOriginal` | `2026:10:28 19:53:08` in `195308.jpg` only — capture time, no timezone, no location |
| XMP | only `hdrgm:Version="1.0"` (HDR gain-map stub) in `195308.jpg`, no creator or location |
| ICC profile / embedded images | Samsung `DCI-P3` profile and an **MPO** wrapper with an HDR gain-map frame, `195308.jpg` only — camera pipeline, not personal |

Visually, the frames show the PCB, the shell, a keyboard/monitor/desk in the
background and fingers holding the board — no faces, no documents, no shipping
labels, nothing readable about where the photos were taken. The only address and
e-mail address in the repo are the **manufacturer's**, printed on the regulatory
label (see [hardware.md §1](hardware.md#1-identity-of-the-device)).

If you ever want the capture timestamps gone too, strip metadata without
re-encoding:

```powershell
ffmpeg -y -i in.jpg -c copy -map_metadata -1 out.jpg   # or: exiftool -all= in.jpg
```

