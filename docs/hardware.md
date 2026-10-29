# Kids Drawing Robot "KY-23" — what the photos tell us

> Status: **first pass, photo evidence only.** The robot has not been powered,
> measured with instruments, or sniffed yet. Every claim below carries a
> confidence marker:
>
> * **[read]** — legible in the photos (label text, silkscreen, chip markings).
> * **[obs]** — observed on the physical unit by the owner (behaviour, not print).
> * **[likely]** — standard interpretation of what is legible; consistent with
>   the rest of the evidence, but not proven.
> * **[guess]** — hypothesis that still needs verification.
>
> Open questions are collected in [§8](#8-open-questions--next-experiments).

---

## 1. Identity of the device

From the regulatory label on the rear/side of the white shell
(`20261028_195128.jpg`) — all **[read]**:

| Field | Value |
|---|---|
| Product name | Kids Drawing Robot |
| Model | **KY-23** |
| Batch No. | 202607 |
| Production date | 2026.07 |
| Power | 5 W |
| Input | 5 V ⎓ 1 A |
| Battery | **1800 mAh** |
| Manufacturer | Kaisiwei Technology Co., Ltd |
| Location of manufacture | Shenzhen City, Guangdong Province, China |
| E-mail | 2628615819@qq.com |
| Marks | CE, FC (FCC), RoHS, WEEE (crossed-out bin), packaging recycling symbol, "CHOKING HAZARD — Small parts — not for children under 3 years" |

Immediate consequences:

* Single-cell Li-ion/LiPo of 1800 mAh → 3.0–4.2 V rail, charged from 5 V/1 A
  USB. **[likely]**
* 5 W while moving implies small geared steppers (~1–2 W each) rather than
  hobby servos. **[guess]**
* No serial number and no per-motor rating is printed anywhere. **[read —
  absent]**

## 2. Photo / image inventory

| File | Size | What it contains |
|---|---|---|
| `20261028_195128.jpg` | 1071×803 | Close-up of the regulatory label (model, batch, power, battery, manufacturer, CE/FC/RoHS) with the installed board above it. |
| `20261028_195243.jpg` | 695×595 | Installed PCB, connector side, upright: 4-pin motor headers + wire colours, USB-C, `LED1`/`红线`, `J16` FPC ribbon, `U11`. |
| `20261028_195308.jpg` | 803×1071 | Same PCB, stored sideways: Chinese labels `电池` / `电机3` / `电机2` / `电机1` / `喇叭`, gear hub, blue cover. |
| `high-res.jpg` | 2496×2521 | Best shot of the component side of the main PCB — almost every chip marking is readable. |
| `H10fc1b163d32467e8d186d39c303fd60A.avif` | 1920×1920 | Product render on a white background: cat head, two arms, pen assembly. Used for the mechanical analysis (§3). |

`docs/derived/*.jpg` are upscaled crops generated from the originals by
`tools/make_crops.py` — see [docs/photos.md](photos.md).

## 3. Mechanical layout (product render + teardown photos)

**[read] Enclosure:** a rounded, roughly cylindrical white body with a big cat
head. On top of the head there is one dark rounded-rectangle pad (reads as a
button or a covered port) plus two small dark dots (LEDs and/or a microphone
hole). Two dark "ears", big eyes and a printed smile on the face. The PCB sits
**vertically at the rear** of the body — visible in `20261028_195128.jpg`, where
the board is held behind the shell.

**[read] Arms:** two white, square-section links, one per side of the body.
Each starts at a **shoulder pivot on the side of the body**, and at that pivot
there is a **black knurled collar/clamp**. The two links run forward/down and
meet at a shared node near the front of the machine, where the **pen holder**
(white clamp with a vertical cylinder and a peg above it) is mounted. A black
toothed hub is visible inside the shell next to the PCB in
`20261028_195308.jpg` — a large **gear at the shoulder**, i.e. a geared joint.

**[likely] Kinematics:** 2-DOF **closed-chain (5-bar) parallel mechanism**:
both links are hinged to the body at fixed, separated pivots and are pinned to
each other at a common "elbow" node, with the pen hanging from that node. Two
independent shoulder angles then place the pen in X/Y (intersection of two
circles), and a **third actuator provides Z (pen up/down)**. This matches the
three motor headers on the PCB (`电机1/2/3`, §6). Alternatives not yet
excluded:

* "Skew-actuator" reading — the pen is rigidly attached to one link and the
  second link only sets the tool angle (unlikely: the pen bracket sits at the
  junction of both links). **[guess]**
* The third motor drives a **cam or lead screw** for pen pressure rather than a
  plain lift. **[guess]**

To settle the kinematics we need the joint types and four lengths:
pivot separation `d`, link lengths `L1`/`L2`, pen offset from the shared node,
and the Z travel (§8).

**[obs] Homing behaviour (2026‑10‑28).** Pressing the power
button: (1) the robot plays a **spoken welcome message**, (2) both arm motors
drive for a few seconds until the arms sit at the **middle** of their travel,
(3) the **pen-lift motor runs upwards**. That is a zero-point calibration /
homing routine. Since the board has no encoders, no limit switches and no current
sensing, the firmware must be driving blind into a mechanical stop or to a fixed
known pose — see [firmware.md §2.1](firmware.md#21-observed-boot-behaviour-owner-report).
Practical consequence for the model: **every axis' zero is defined relative to a
hard stop or a fixed step count, and the lift's zero is at the top.**

**[obs] USB-C is charge-only.** Plugged into a PC, no device appears — no
updater, no serial port, no field-update path. Firmware can therefore only be
reached through the flash chips or a UART header (`J15`).

## 4. Main PCB

### 4.1 Identification

**[read]** Silk screen in the middle of the board:

```
ZFX_KY-23_L_V2.1_2026_0427
```

→ house/project code `ZFX`, model `KY-23`, board flavour `L` (main logic),
layout revision **V2.1**, dated **2026-04-27**. Footprints on this board carry
their pin numbers on the silkscreen (e.g. `4`, `5` next to the power chips),
which is typical of a fast, low-cost ODM layout.

Green solder mask, wide power pours under the motor section, mounted vertically
inside the body with the headers along one long edge. **[read]**

### 4.2 Component list

Refdes is not printed for most parts; where the silkscreen names one, it is
listed.

| Refdes | Marking on part | Package | Interpretation | Conf. |
|---|---|---|---|---|
| — (×2) | `ULN2003` / `866350H` | SOIC-16W | 7-channel Darlington sink array — **the motor drivers**. Two of them = 14 outputs, enough for three 4-phase unipolar steppers with 2 spare channels. | **[read]** marking / **[likely]** use |
| — and — | `KH25V8035` / `5Q224300` / `L261016` | SOP-8 ×2 | **8 Mbit SPI NOR flash**, naming/pinout clone of Macronix `MX25V8035` (`25` + 8-pin SOP + `V` = low-voltage series). There are **two** of these on the board (one by the `JL` chip, one in the power section). A `U2` label sits near the first one, but the refdes-to-part mapping is not proven. | **[read]** marking / **[likely]** function |
| — | `JL` logo + **`AB25BP33704-55A0`** | **SOP/SSOP-24** (pin count confirmed by owner) | The `JL` mark is Zhuhai **Jieli** Technology. `AB` + 24 pins + a **separate external SPI flash** matches Jieli's `AB53xx`-style BT-audio line (external-flash parts, no on-chip code flash) rather than the `AC69xx` line, which usually has internal flash. Function: **BT/voice SoC** — speaker, LEDs, possibly the BLE link to the app. Reprogramming discussed in [firmware.md](firmware.md). | **[read]** marking+package / **[guess]** function |
| `U5` | blank / abraded — the laser marking looks deliberately removed | QFN, ~12 pins/side (~48) | Most likely the **motion controller**: drives the ULN2003 inputs, scans the buttons, talks to the Jieli chip. Unmarked parts in this spot are usually the MCU. | **[guess]** |
| `U3` | `4056A` / `5JD41C` | SOP-8 | **TP4056A-class 1-cell Li-ion linear charger** (1 A max, current set by `R2`), fed from USB-C 5 V. Matches "5 V ⎓ 1 A, 1800 mAh". | **[likely]** |
| `U10` | small, blurry (`KC?AH`) | SOT-23-6 | DC-DC converter next to `FB1` (4R7 = 4.7 µH) and a 220 µF/16 V electrolytic → generates the motor and/or logic rail. | **[guess]** |
| `Q6` | two lines, illegible (`?05W` / `6B?6?`) | SOP-8 | Dual MOSFET (load switch or small half-bridge) near the connector edge. | **[guess]** |
| `Q51` | `1AM` | SOT-23 | `1AM` = MMBT3904-type small-signal NPN; likely an LED or speaker-enable switch. | **[likely]** |
| `D7`, `D8` | `SA` | SOD-323 | Small diodes (clamps / ORing). | **[guess]** |
| `FB1` + `C19` | `4R7`, `220 16V VT` | inductor + SMD electrolytic | Output filter of the DC-DC. | **[read]** parts |
| `J16` | — | FPC/FFC, 0.5 mm pitch, ribbon labelled `AWM 20624 80°C 60V VW-1` | Ribbon to the **second assembly** (head / eyes / front board). Pin count still to confirm. | **[read]** |
| `J15` | pads `V+`, `U_1`, `U_2`, `NC`, plus `TP` and `TP1` | through-hole test pads | **Debug/programming** header — the obvious place for a logic analyser. | **[likely]** |
| `SW1..SW3` | — | 4-pin tactile switches | Three user buttons along the top edge (next to `LED3`/`LED4`, `R36`/`R37`). | **[read]** |
| `LED1..LED4` | — | LEDs (position marks only) | Status lighting; the head "eyes" are probably fed over the FPC instead. | **[likely]** |
| — | — | USB Type-C receptacle | 5 V charging input. Whether D+/D− are wired (does it enumerate?) is **unknown**. | **[read]** connector |
| `R2`, `R9`–`R12`, `R16`–`R24`, `R30`–`R37`, `C3`–`C23` | — | 0603/0805 | Charge-current set, LED series resistors, ULN input pull-downs, DC-DC feedback divider. | — |

### 4.3 Block diagram (working hypothesis)

```
 5 V USB-C ──► TP4056A charger (U3, R2 sets I_chg) ──► 1S Li-ion 1800 mAh
                      │                                    │
                      └──────────► VBAT ────────────────────┤
                                                           │
         DC-DC (U10 + FB1 4R7 + 220 µF) ──► V_MOTOR / 3V3 ──┤
                                                           │
 ┌─────────────────────────────────┐                       │
 │ U5  QFN, unmarked               │                       │
 │ main/motion controller          │                       │
 └──┬────────────┬─────────────┬───┘                       │
    │            │             └── SW1..SW3 + LED1..LED4    │
    │            └── SPI ── KH25V8035 #1 ──────────────────┐│
    │                                                      ││
    │   ┌───────────────────────────────┐                  ││
    └───┤ "JL" JieLi SoC (AB25BP…)      │◄─ KH25V8035 #2 ──┘│
        │ voice / audio / LED drive     │──────► 喇叭 speaker │
        └───────────────────────────────┘                     │
                  │                                           │
   ULN2003 #1 ──► 电机1 (4 wires)                             │
   ULN2003 #2 ──► 电机2 (4 wires) + 电机3 (4 wires, split)     │
                  │                                           │
   J16 FPC ──► head assembly (eyes / front panel?)            │
```

Only the charger, the two flashes, the ULN2003s, the headers and the speaker
label are read directly; the signal map is a hypothesis. How `电机3` is split
across the two ULN2003s is a 5-minute continuity check.

## 5. Power and battery

* **1800 mAh** 1S pack on a 2-wire red/black harness into the `电池` header
  **[read]**.
* `4056A` (TP4056A-class) charger → 1 A by default unless `R2` differs; the
  board is rated 5 V/1 A, so roughly 0.5–1 A charge current is expected
  **[likely]**.
* No fuel-gauge IC is visible → the firmware charges/protects externally and
  infers state of charge from an ADC **[guess]**.
* ULN2003 drops ~1 V (two V_BE), so a boost converter to ~5–6 V for the motor
  rail would make sense from a 3.7 V pack; `FB1`/220 µF is consistent with a
  boost (or with a 3.3 V buck) **[guess]**.

## 6. Connectors and wire colours

The Chinese labels are printed on the PCB edge (photo `20261028_195308.jpg`);
reading that photo top-down **[read]**:

| Silk label | Meaning | Housing | Wires seen |
|---|---|---|---|
| `电池` | Battery | 2-pos, JST-XH style (`J14`) | thick red + black |
| *(unlabelled, smaller)* | Auxiliary 2-pos — sensor, switch or limit | 2-pos | — |
| `电机3` | Motor 3 | 4-pos | coloured set (yellow/red/blue/black) |
| `电机2` | Motor 2 | 4-pos | coloured set |
| `电机1` | Motor 1 | 4-pos | coloured set |
| `喇叭` | Speaker | 2-pos | red/black |
| `J16` | FPC ribbon → head | 0.5 mm FPC | white flat cable |

**[read]** In `20261028_195243.jpg` four solder pins are visible under each
motor housing → the motor headers are 4-position.

**[obs]** On this unit the headers are **glued/locked in place** and cannot be
unplugged. That is not a blocker: every measurement we need can be taken on the
PCB side — resistance at the **ULN2003 output pins** (10…16) and logic captures
at its **input pins** (1…7). Workarounds and a glue-identification table are in
[controller.md §1.1–1.2](controller.md#11-glued-headers-measure-in-circuit-at-the-uln2003).

**[likely]** Three motors × 4 phases = 12 outputs, and two ULN2003 provide
exactly 14 sink channels. Unipolar stepper wiring (coil centre taps returned to
the motor rail) fits this arithmetic. Two things still have to be confirmed:

1. how the motors' fifth (common) wire is returned, and
2. the pin → wire-colour map of each motor, which the firmware must reproduce.

## 7. Useful negatives (what is *not* on the board)

* No hall sensors, no optical encoders, no end-stop switches are visible →
  the machine is **open loop**; positions must come from step counting plus a
  homing routine against a hard stop **[likely]**.
* No relay, no servo headers, no buzzer besides the `喇叭` speaker.

### 7.1 Is there a radio at all? (evidence so far)

Nothing photographed **proves** a radio. The case for and against:

| Observation | Reading |
|---|---|
| `JL` = JieLi. Jieli is a **Bluetooth-audio** house; essentially all of its toy SoCs in this class contain a 2.4 GHz BR/EDR + BLE radio. | **for** — conditional on the logo/type being right **[guess]** |
| `AB…` prefix + external SPI flash + 24-pin SOP = Jieli's *external-flash* line (their `AC69xx` parts normally have on-chip code flash). Those parts are BT parts. | **for** **[guess]** |
| The board is a **two-processor** design (voice chip + motion MCU talking over UART). A BLE link on the voice chip would have to forward drawing commands to the motion chip — a normal, cheap toy architecture. | **for** **[guess]** |
| A welcome voice clip plays with **no phone present** → the toy is fully standalone. | neutral |
| No **antenna** is visible on the *photographed* (component) side: no ~25 mm PCB meander, no ceramic chip antenna, no wire, no obvious RF keep-out. | **against** — but the **bottom side was never photographed** |
| No **26 MHz crystal** was spotted near the JieLi chip in the shots we have (a BT SoC needs one, ±20 ppm class). | **against** — same caveat, we never did a full-board sweep |
| The regulatory label carries only generic CE/FC/RoHS/WEEE marks — **no FCC ID and no CE-RED number**, which an intentional radiator would normally need. | weak **against** |
| UI = 3 buttons + 4 LEDs + speaker → a standalone toy, not necessarily an app-toy. | weak **against** |

Conclusion: **unproven, and the physical evidence currently leans slightly
"no radio"**, while the chip-family argument leans "radio". §8 item 10 gives the
20-minute procedure that settles it.

## 8. Open questions & next experiments

Ordered by value per unit of effort. 📷 = needs a photo/measurement,
🔌 = needs a meter / scope / logic analyser. For the firmware/serial-access side
of these questions, see [firmware.md](firmware.md).

1. **Motor wiring** 🔌 — resistance/continuity between the 4 pins of each
   `电机n` header. A unipolar stepper shows one common pin, two independent
   coils show ~equal pair resistances (bipolar). Record the colours per pin.
2. **Motor identity** 📷 — photo of the motor label (gearbox ratio, step
   angle). 28BYJ-style geared steppers are the usual suspect: 4-phase, 64:1,
   5.625°/step. Confirm 4 vs 5 wires on the motor itself.
3. **Arm geometry** 📷 — measure shoulder-pivot separation `d`, link lengths
   `L1`/`L2`, pen offset from the shared node, Z travel, and the reachable
   drawing area. Required before the inverse kinematics can be written.
4. **`U5` marking** 📷 — re-shoot with a torch held almost parallel to the
   board; the QFN looks intentionally blanked.
5. ~~**`JL` chip** pin count~~ — resolved: `AB25BP33704-55A0`, 24-pin SOP. The
   open item is now its pinout and boot/download behaviour, see
   [firmware.md](firmware.md).
6. **`J16` FPC** 🔌📷 — count contacts; trace whether it feeds the eyes, a
   second MCU or just LEDs.
7. **`J15` debug pads** 🔌 — logic analyser on `U_1`/`U_2` while booting; UART
   at 115200 baud is the most likely outcome, and the pad set also looks like a
   programming header.
8. ~~**USB-C**~~ — answered: **charge-only**, no USB device appears.
9. **Boot behaviour** 📷 — power on, record LED patterns and button functions;
   correlate with (7).
10. **Radio** 📷 — settle it in this order (each step is decisive on its own):
    1. **Photograph the bottom side** of the PCB and the area around the `JL`
       chip. Look for a ~25 mm PCB meander antenna, a 3×1.6 mm ceramic chip
       antenna, or a short wire, plus its **RF matching network** (2–3 tiny
       passives on one pin) and an antenna keep-out with no copper pour.
    2. **Look for a 26 MHz crystal** (4-pad SMD, ~3.2×2.5 mm) next to the `JL`
       chip. No crystal anywhere → the part is not a radio SoC.
    3. **BLE scan**: nRF Connect / LightBlue for 60 s while the robot is on and
       while long-pressing each button. Note name + MAC OUI.
    4. **Check the paperwork**: FCC ID or CE-RED number on the label, box or
       manual. Either one → radio confirmed, and the ID can be looked up in the
       public database (frequency, modulation, sometimes internal photos!).
11. **Inside the mechanics** 📷 — with the shell open: both shoulder gearboxes,
    the pen-lift actuator, and whether motor 3 is a stepper or a cam/DC motor.
12. **Power rails** 🔌 — pack voltage, charge current, and the `U10` output
    voltage to pin down the motor supply.

## 9. Reading tips for the next photo session

* Chip markings: hold the phone ~10 cm away, light the package at a **grazing
  angle** with the flashlight, and use a **2×/3× tele lens** rather than digital
  zoom — laser etching loses contrast under wide-angle zoom.
* Fill ~70 % of the frame with the board and shoot perpendicular; perspective
  destroys the small packages.
* Take a second frame with the light from the opposite side: etchings are often
  readable in only one direction.
* A USB microscope (or a phone macro clip-on) on `U5` and the `JL` chip would
  settle both unknowns in one shot.

