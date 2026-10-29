# Own controller board ("Option E") — design, BOM, pin map, firmware

Replacing the stock electronics so the robot draws whatever we want. Written for
someone who is comfortable with ESP boards: nothing here needs a PCB on day one.
This is the detailed version of **Option D + Option E** in
[firmware.md](firmware.md) — Option D is Variant A below (reuse the stock
ULN2003s), Option E is Variant B (own board).

Inputs from the unit itself: USB‑C is **charge‑only** (no firmware path),
booting plays a voice clip and then **homes the two arm motors to the middle and
the lift motor upwards** ([firmware.md §2.1](firmware.md#21-observed-boot-behaviour-owner-report)).
Battery and sound are **out of scope** for this build.

---

## 1. Can you drive the motors directly? Yes — after one 5-minute measurement

The motors are 3‑wire? 4‑wire? unipolar? bipolar? — that single answer picks the
driver, and you already have all three motors on headers.

> ⚠️ **On this unit the `电机n` headers are glued/locked and do not come out.**
> Nothing below requires unplugging anything — see §1.1. The table is what the
> readings mean once you have them.

| Measurement | Reading | Conclusion |
|---|---|---|
| 5 wires, one pin shows **half** the resistance to each of the other four | e.g. 25 Ω vs 50 Ω | **5‑wire unipolar** (28BYJ‑48 class). Common = the odd one out (usually red). |
| 4 wires, two **isolated pairs** of ~equal resistance, ∞ across pairs | e.g. 40 Ω + 40 Ω | **4‑wire bipolar**. Two independent coils. |
| 4 wires, all pairs conduct, one pin ≈ half resistance | — | 4‑wire unipolar with internal common → treat as unipolar, find the common on the PCB. |
| Any pair reads 0 Ω or ∞ on all pairs | — | damaged motor or bad probe contact — re-check. |

Write the result here: **motor type = ____________**, coil resistance = ______ Ω.

### 1.1 Glued headers: measure in-circuit at the ULN2003

The ULN2003 outputs are the motor wires: SOIC pins **10…16** are OUT7…OUT1, pin
**8** is GND, pin **9** is COM. They are big, on the opposite side of the package
from the inputs, and they map 1:1 to the header pins. **Probe there.**

Why this is electrically valid with the board unpowered:

* Between two outputs there is only *one* conducting path — the motor winding.
  The ULN2003's internal clamp diodes cannot bridge two outputs (every
  output→COM diode faces the same way, so one of the two is always
  reverse-biased).
* With `U5` unpowered, the Darlington outputs are off (high‑Z), so the only other
  paths are the internal base bleed resistors → hundreds of kΩ, i.e. invisible.

Recipe:

1. Identify each chip's 4 outputs per motor by finding which 4 output pins are
   wired to the 4 pins of a given `电机n` header (continuity, board unpowered).
2. Ohmmeter across the 6 pairs of those 4 pins:

| Pattern (per motor, 4 wires) | Verdict |
|---|---|
| **all 6 pairs** read a similar value, tens of Ω (e.g. 40–60 Ω) | **unipolar** — every phase end is tied to the common inside the motor |
| **2 pairs** finite and equal, **4 pairs** open/∞ | **bipolar** — two separate coils |
| all pairs open | wrong pin group, or a broken winding |

3. `V+`/COM cross‑check (optional, and only with a **diode‑test** meter):
   output → pin 9 reads either a winding resistance (tens of Ω → unipolar) or
   just ~0.6–0.7 V of diode drop / OL (→ bipolar). Don't read this with a plain
   ohmmeter — the clamp diode and the winding parallel each other.

**Bonus test without any unplugging — back‑EMF:** with the robot **off**, set the
meter to AC mV and turn one arm slowly by hand. The coil pair that generates
voltage is the one belonging to that arm's motor, and pairs with *no* response
belong to the other motors. This also confirms "two coils per motor" physically.

### 1.2 If you really must release the header

Work out *why* it is stuck before applying force:

| What you see | What it is | How to release |
|---|---|---|
| clear/white rubbery blob over the housing | **hot‑melt glue** (most common) | a drop of **IPA** on a cotton bud, wait 30–60 s, then peel with a plastic pick; or 5–10 s of hot air at ~70 °C |
| white/black rubbery, tenacious | **silicone** | IPA does nothing; cut along the seam with a #11 blade, then peel |
| hard yellow/brown | **epoxy / cyanoacrylate** | do not fight it — treat the connector as permanent |
| a small tab on the housing | **moulded latch** (JST‑style) | press the latch with a fine screwdriver *while* pulling |

Always rock the **housing** side to side and pull the housing — never pull the
wires, the crimps tear. Never use the PCB or an SMD part as a fulcrum.

If it still will not move, the clean escape is to **desolder the header from the
PCB** (it is through‑hole, 4 pins) and lift it out with the cable still attached —
or snip the 4 pins flush and pull the plastic shell off, leaving 4 loose wire
ends. Do not cut the wires mid‑harness: you would lose the 4‑pin plug.

### 1.3 What actually needs the cable loose?

| Task | Needs unplugging? |
|---|---|
| Motor type measurement (DMM) | **no** — at the ULN2003 outputs (§1.1) |
| Homing capture (logic analyser) | **no** — at the ULN2003 **inputs** |
| Variant A (ESP into stock drivers) | **no** — PCB side only |
| Bipolar conversion for a chopper driver | **no, if** the motors are 4‑wire (already bipolar). If 5‑wire: cut the common's **trace on the PCB** instead of unplugging, then feed the 4 phase wires to the chopper (wire ends are then soldered on the header's PCB pads) |
| Variant B carrier board | only if you want to reuse the stock harness — otherwise desolder the 3 headers and mount them on the new board |

**Why it matters**

* **Unipolar (5‑wire)** → the stock ULN2003s are the correct driver. You can keep
  the stock board as a driver stage (Variant A), or build your own sink driver.
* **Bipolar (4‑wire)** → ULN2003 cannot drive it (it is sink‑only, there is no
  high side). You need a real H‑bridge/chopper (Variant B).

**Either way there is a useful trick:** a 5‑wire unipolar motor can be driven as
a **bipolar** motor by using only the two *end* wires of each coil and ignoring
the centre tap. That doubles the torque and lets you use a modern chopper driver
(`A4988`, `DRV8825`, `TMC2209`), which is what makes a drawing robot quiet and
smooth. On a 28BYJ‑48 the pairs are (blue ↔ yellow) and (pink ↔ orange), red =
common; confirm with your own measurements, never trust the colour table.

Typical 28BYJ‑48 numbers to expect (**verify**): 5 V, 4‑phase, 64:1 gearbox,
**2048 full steps per output revolution** (5.625°/step), ~50 Ω per phase.

## 2. Keep or cut the stock board?

| | Variant A — reuse the stock ULN2003s | Variant B — own carrier board |
|---|---|---|
| New hardware | ESP dev kit + 12 wires | ESP + 3 drivers + power section |
| Cost | ~€10 | ~€25–40 |
| Work | cut/lift 12 traces (`U5` → ULN2003), solder 12 wires | build a board or use 3 stepper modules |
| Motor type | **unipolar only** | bipolar (or unipolar) |
| Torque / noise | as stock (whiny, buzzes) | much better, near silent with TMC2209 |
| Homing | open loop into hard stops, or add switches | sensorless (`StallGuard`) or switches |
| Reversible | yes, if you lift pins instead of cutting traces | the stock board stays intact as a spare |

Recommendation: **Variant B with 28BYJ‑48 rewired as bipolar + TMC2209**. If you
want a working robot this weekend, Variant A gets you there in an hour.

## 3. Variant A — ESP into the stock ULN2003 inputs (fastest)

The ULN2003s are already wired to the motors, the `V+` pad on `J15` is the motor
rail and the ULN2003 common (pin 9) sits on that rail too. The only thing to
remove is `U5`'s control.

1. Find the 12 input traces (`U5` pin → ULN2003 pin 1…7). Record them.
2. **Lift the 12 `U5` pins** (or cut the traces) so the ESP is the only driver.
   Leave the two ULN2003s and their outputs untouched.
3. Wire the ULN2003 input pads to 12 ESP GPIOs, plus a common GND.
4. Power: **do not** use the robot's battery/charger unless you want to. Feed the
   ULN2003 common (`V+`) from a **5 V / 2 A** bench or USB supply, ESP on its own
   USB, grounds tied together.
5. Sanity: 10 kΩ pulldowns on the 12 inputs keep the motors off while the ESP
   boots.

Darlington reality check: ~1.0–1.3 V drop per channel, 500 mA max per channel, so
at 5 V a 50 Ω phase sees ~75 mA — exactly how the stock robot runs.

## 4. Variant B — own carrier board

### 4.1 Block diagram

```
 5–12 V DC jack / USB-PD ──► reverse-polarity P-FET ──► VM rail ─┬── 3× TMC2209 VM
                                  │                              │   100 µF + 100 nF each
                                  └── buck (MP1584 / MP2315) ──► 3V3 ──► ESP32-S3
                                                                        │
 ESP32-S3 ── STEP/DIR ×3 ──────────────────────────────────────────────┘
          ── EN (shared, active low)
          ── UART (single wire, 1 kΩ per driver) ──► TMC2209 config / StallGuard
          ── 3× endstop inputs (optional, cheap)
          ── button, status LEDs, USB to the host
```

### 4.2 BOM

| Qty | Part | Why | Note |
|---|---|---|---|
| 1 | **ESP32‑S3‑WROOM‑1** dev kit (or classic ESP32‑DevKitC) | plenty of GPIO, native USB | avoid strapping pins 0/3/45/46 and the USB pins 19/20 for motor signals |
| 3 | **TMC2209** stepper module (`TMC2226` is the same chip) | silent, 256 µstep, **StallGuard4** sensorless homing, 4.75–29 V, 1.4 A RMS | preferred; works down to a **5 V** rail |
| — | *alternative:* 3× `A4988` | cheapest | **needs ≥ 8 V** VM → rules out a 5 V rail |
| 3 | 100 µF electrolytic + 100 nF | decoupling per driver | electrolytic on VM, ceramic near VIO |
| 1 | MP1584 / MP2315 buck module | 5–12 V → 3.3 V for logic | or power the logic from the dev kit's USB |
| 3 | microswitch / optical endstop (optional) | deterministic homing without StallGuard | at arm‑A stop, arm‑B stop, pen‑lift top |
| 3 | JST‑XH 4‑pin plug + wires | reuse the stock motor harness | repin for bipolar if you rewire the motors |
| 1 | fuse + P‑MOSFET or Schottky | supply protection | optional, cheap |
| — | DC jack / screw terminal | main power in | 5 V ≥ 2 A (unipolar) or 12 V ≥ 1.5 A (chopper) |

**Voltage choice**

* Motors kept **unipolar** (stock wiring): **5 V**, 2 A — matches the stock setup.
* Motors rewired **bipolar** with TMC2209: **12 V** VM, current limit ~0.3 A RMS
  per phase. The chopper regulates current, so extra VM buys speed, not heat.
  5 V VM also runs, just sluggishly.

### 4.3 Pin map (ESP32‑S3)

| Signal | GPIO | Notes |
|---|---|---|
| M1 STEP / DIR | 4 / 5 | arm motor 1 |
| M2 STEP / DIR | 6 / 7 | arm motor 2 |
| M3 STEP / DIR | 15 / 16 | pen‑lift motor |
| `EN` (all drivers) | 17 | active low, pull‑up so drivers stay off during boot |
| TMC UART TX | 18 | via 1 kΩ into each driver's `PDN_UART` |
| TMC UART RX | 8 | direct (single‑wire half duplex) |
| Endstop A / B / lift | 9 / 10 / 11 | `INPUT_PULLUP`, switches to GND |
| Button | 12 | `INPUT_PULLUP` |
| Status LED | 13 | optional |

Adjust freely — just stay off the strapping and USB pins. On a **classic ESP32**
GPIO 6–11 are the internal flash: do not use this map verbatim there.

### 4.4 If you manufacture a PCB

* 4 layers if you can (signal / GND / 3V3 / VM); 2 layers is fine at these
  currents.
* Motor traces ≥ 0.5 mm, VM pour on top, keep the buck's switching node tiny and
  away from the STEP lines.
* Star ground: driver VM returns and logic GND meet at the input connector.
* Put the 12 motor outputs on 2.54 mm headers that match the stock harness.
* Bring out 3V3 / 5V / GND / UART on a spare header — debugging gets much easier.

## 5. Firmware plan

| Layer | Choice | Notes |
|---|---|---|
| Framework | Arduino‑ESP32 or ESP‑IDF | both fine; Arduino is quicker to start |
| Step generation | **FastAccelStepper** (ESP32 back end) | acceleration + 3 axes from one timer/RMT pool |
| Driver config | TMCStepper (TMC2209 over UART) | run/hold current, microsteps, StallGuard threshold |
| Homing | `G28`-style: StallGuard or endstop, then back off and re‑approach slowly | run it on every boot, exactly like the stock robot |
| Kinematics | 5‑bar IK (needs the measured geometry) | → `docs/kinematics.md` |
| Protocol | line based over USB‑serial: `G28`, `G0 X… Y…`, `M3`/`M5` pen down/up, `M114` | trivial to drive from Python |
| Host | SVG → polylines (`vpype`, `svg2gcode` or `svgpathtools`) → stream commands | keep the robot deterministic, the host smart |

**Calibration constants to find once the arms are measured**

* `steps_per_deg` = 2048 / 360 × microstep factor — verify by commanding 90° and
  counting.
* `d` = shoulder-pivot separation, `L1`/`L2` = link lengths, pen offset from the
  shared node, plus the sign/zero convention of each axis.
* One **scale factor** per axis from "draw a 100 mm line, measure it, adjust"
  absorbs gearbox and geometry errors.

## 6. Milestones

1. **One motor spins both ways** on the bench (200 steps out, 200 back) → proves
   the wiring map and the current setting.
2. **All three motors jog**; the arms sweep their full range without stalling and
   the lift goes up and down.
3. **Homing works** repeatedly (same pose every boot).
4. **A 100 mm straight line**, measured and calibrated.
5. **A square, then a circle** — first closed shape drawn by the new stack.
6. **SVG pipeline** draws a real picture.

## 7. Gotchas

* `EN` floating during boot → coils energised → motors get hot and the arms
  twitch. Pull it to the "disabled" level with a resistor.
* Never move the arms by hand while the drivers are enabled — you will lose
  steps and the position is gone until the next home.
* `A4988` on a 5 V rail simply does not run; that is why TMC2209 is the default
  here.
* Keep the stock board in a drawer: its ULN2003s, the `KH25V8035` flashes, the
  harnesses and the labelled connector pinouts are all reusable, and it is the
  only reference if the mechanics need re‑checking.
* The stock behaviour is a good UX reference: it homes *before* it speaks or
  draws, i.e. never trust a position after power‑on without homing.

