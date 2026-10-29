# Drawing robot reverse engineering — "Kids Drawing Robot" KY-23

<p align="center">
  <img src="docs/derived/product_hero.jpg" alt="KY-23 kids' drawing robot: white cat-faced body, two arms joined at a common node holding a pen" width="340">
</p>

Notes and tooling for reverse engineering a cheap kids' drawing robot
(manufacturer *Kaisiwei Technology Co., Ltd*, Shenzhen). The starting material
is a set of photos of the opened machine plus a product render; no firmware,
schematic or documentation came with it.

> ## Status: analysis only — project parked ("in the freezer")
>
> Everything in this repository is **analysis**: photos, component
> identification, hypotheses and plans. **No firmware was dumped, patched or
> reflashed, and nothing here has been verified on the hardware.**
>
> The original goal was modest — swap the built-in drawing for one of my own and
> make the robot draw faster — but changing the firmware turned out **not to be
> straightforward at all**:
>
> * there is **no firmware-update path** (USB-C is charge-only, no bootloader,
>   no vendor tool);
> * both firmwares live in **external SPI flash next to undocumented CPUs** — a
>   proprietary JieLi SoC and an unmarked, possibly read-out-protected QFN — so
>   there is no toolchain to build against;
> * the drawings are not a file you can simply replace; whatever format they use
>   is baked into an image nobody has dumped yet;
> * "make it faster" means redoing the motion control (step generation, homing,
>   kinematics), i.e. writing a new firmware rather than editing the old one.
>
> So this stays at the analysis stage and goes **in the freezer**. If you want to
> pick it up, [docs/firmware.md](docs/firmware.md) explains what makes it hard and
> what the realistic routes are — **option D (drive the existing ULN2003s from
> your own MCU)** is the one with a sane effort/reward ratio.

```
.
├── high-res.jpg                 # main PCB, component side (primary evidence)
├── 20261028_1951*.jpg           # label close-up, connector side, Chinese silk
├── H10fc1b...A.avif             # product render (cat head, two arms, pen)
├── docs/
│   ├── hardware.md              # everything we know so far, with confidence levels
│   ├── firmware.md              # how (and whether) to reprogram it - options, steps, risks
│   ├── controller.md            # own controller: motor choices, BOM, pin map, firmware
│   ├── photos.md                # photo inventory + crop tool + metadata audit
│   └── derived/                 # generated crops (not source data)
├── data/components.csv          # machine-readable component/connector list
└── tools/make_crops.py          # regenerates docs/derived/*.jpg
```

## TL;DR of the findings

Full details, evidence and open questions: **[docs/hardware.md](docs/hardware.md)**.

* **Device:** model `KY-23`, batch `202607`, built 2026.07, 5 V ⎓ 1 A input,
  5 W, **1800 mAh** single-cell battery, CE/FCC/RoHS.
* **Main board:** `ZFX_KY-23_L_V2.1_2026_0427`, vertical inside the body,
  USB-C for charging.
* **Guts:** TP4056A-class charger, a DC-DC stage (`FB1` 4.7 µH + 220 µF/16 V),
  two `KH25V8035` 8 Mbit SPI flashes, one **JieLi** (`JL`) audio/voice SoC, one
  unmarked QFN (`U5`, the likely motion MCU), **two ULN2003** Darlington arrays
  as motor drivers, 3 tactile switches, 4 LEDs, an FPC ribbon to the head and
  debug pads marked `V+ / U_1 / U_2 / NC`.
* **Motors:** headers labelled `电机1`, `电机2`, `电机3` (4-pin each) plus
  `电池` (battery) and `喇叭` (speaker). 12 motor phases run off 14 ULN2003
  channels → three **4-phase unipolar steppers** is the leading hypothesis.
* **Mechanism:** two shoulder-mounted arms pinned together at a common front
  node with the pen hanging off it → a 2-DOF closed-chain (**5-bar**) parallel
  machine, with the third motor for pen up/down.
* **Observed boot:** speaks a welcome message, homes both arms to the middle,
  raises the pen. USB-C is **charge-only** (no firmware path).

## Reprogramming verdict (theory — never attempted)

Short version — see **[docs/firmware.md](docs/firmware.md)** for the full plan:

* Both CPUs run from **external SPI flash** (`KH25V8035` ×2), so both firmwares
  can be dumped, patched and reflashed with a **~€5 CH341A + SOP-8 clip**, no
  vendor tool, no bootloader unlock. That is the safe first move and the backup
  you need for everything else.
* The JieLi `AB25BP33704-55A0` (24-pin SOP) is a **plausible but unproven**
  firmware-modification target: it needs its pinout/download mode and an SDK
  (proprietary) that may not be publicly available for this exact part.
* The unmarked QFN `U5` is a **poor** target: no datasheet, likely OTP or
  read-out protected.
* **USB-C is charge-only**, so there is no firmware update path at all — flash
  chips or the `J15` UART pads only.
* The pragmatic route to "a robot that draws my drawings" is to **bypass the
  stock firmware**: cut/lift the 12 `U5` → ULN2003 lines and drive the existing
  darlington arrays from an ESP32/RP2040 with our own motion firmware — or build
  a small carrier board with 3 stepper drivers. Both are specified in
  **[docs/controller.md](docs/controller.md)**.

## Regenerating the crops

```powershell
python tools/make_crops.py     # needs Pillow + ffmpeg on PATH
```

See [docs/photos.md](docs/photos.md) for what each crop shows and how to add
new ones.

## What to do next (if this ever leaves the freezer)

None of this has been done — it is the list the project would resume with. The
highest-value next steps (details in §8 of `docs/hardware.md`):

1. 🔌 Meter the `电机n` headers (4 wires each) to identify unipolar vs bipolar
   steppers, and note the wire colours.
2. 🔌 Buzz out `U5` → ULN2003 inputs: this both proves the architecture and
   yields the 12-channel motor pin map needed to repurpose the board.
3. 📷 Measure the linkage: pivot spacing, link lengths, pen offset, Z travel.
4. 🔌 Logic-analyser on the `J15` pads (`V+ / U_1 / U_2 / NC`) during boot,
   and check whether USB-C enumerates.
5. 💾 Dump both `KH25V8035` flashes with a CH341A clip and analyse the images
   (`binwalk`, `strings`) — see [docs/firmware.md](docs/firmware.md) §4.
