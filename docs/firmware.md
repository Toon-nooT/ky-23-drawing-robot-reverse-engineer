# Reprogramming / repurposing the KY-23 — feasibility and plan

Answers "how feasible is it to reprogram this thing, and what do I actually have to
do?" against the hardware described in [hardware.md](hardware.md).

> **Status: analysis only — nothing here was carried out, and the project is in
> the freezer.** No flash has been dumped and no firmware has been modified. The
> original goal was modest: change the built-in drawing for one of my own and make
> the robot faster. Everything below is graded against that goal, and the honest
> conclusion is that **changing the firmware is not straightforward** — no update
> path, no documented CPUs, no toolchain, and no replaceable drawing file — so the
> effort went far beyond a patch of an existing image. Treat these pages as a map
> of the work, not as a walkthrough that was followed.

> Confidence markers: **[fact]** = follows from the photos or from generic,
> widely-documented practice; **[likely]** = strong inference, not verified on
> this unit; **[unverified]** = must be checked before relying on it.

---

## 0. Short answer

**Reprogramming is feasible, but "reprogram" is at least four different projects
with wildly different difficulty.** The good news is that *both* processors on
this board execute from **external SPI NOR flash** (`KH25V8035` ×2), so you can
dump, patch and rewrite their firmware with a **€5 CH341A clip and no vendor
tool at all** — as long as the images are not encrypted or signed. **[fact/photo]**

| # | Goal | Feasible? | Effort | Risk | Notes |
|---|---|---|---|---|---|
| 0 | **Custom drawings via the app/BLE protocol** | **Unproven** — no radio confirmed yet | 1–2 evenings *if it exists* | None to the robot | Needs (a) a radio, (b) an app, (c) that the app carries paths. §3.1 settles it in ~20 min. |
| A | **Read / patch / rewrite the SPI flashes** | Yes | Low (an evening) | Low | CH341A + SOP-8 clip. Best first move either way. |
| B | **New firmware on the JieLi `AB25BP33704`** | Plausible, unproven | High (days–weeks) | Medium (boot brick, recoverable) | Needs the JieLi download path + an SDK for this exact part. Vendor SDK is proprietary. |
| C | **New firmware on `U5` (motion MCU)** | Probably not | Very high | High | Part is deliberately unmarked; many cheap MCUs are OTP or read-out protected. |
| D | **Sidestep the stock firmware: drive the ULN2003s from your own MCU** | **Yes, recommended** | Medium (1–3 weekends) | Low–medium | You get a robot that draws what you want, regardless of what's inside. |
| E | Replacement board (own drivers, own everything) | Yes | High | Low | Do this only if D hits a wall. |

**Recommended order: A (dump everything) → 0 (try the app path) → D (own
controller).** B/C only if the goal is specifically to *keep* the stock
firmware and modify it. In practice D gives 90 % of the fun for 20 % of the
work, and A is what makes B safe anyway.

## 1. Why the external flash matters so much

Both CPUs are "XIP from SPI flash" parts — the JieLi chip because `AB` + 24 pins
+ external flash matches Jieli's external-flash audio line **[likely]**, and
`U5` because there is a second 8 Mbit flash that must belong to it
**[likely]**. Consequences:

* Firmware can be **read and written passively**, without any vendor tool,
  bootloader handshake or "unlock" procedure. **[fact]**
* You keep a **restorable backup** — this is what makes experimenting safe. A
  chip that no longer boots is usually just a flash that needs the original
  image written back. **[fact]** (assuming nothing one-time-programmable is
  involved, e.g. OTP fuses — rare in this class of part but not impossible).
* A flash dump answers most architecture questions cheaply: which CPU owns which
  chip, what RTOS/SDK, whether the drawing data is a simple resource blob, and
  whether the image is encrypted (high entropy / no readable strings).

## 2. Do these three measurements first (they decide everything)

Total time ~1 evening, no soldering, no risk. Record the results in this file.

1. **Continuity: `U5` GPIO → ULN2003 inputs.**
   The ULN2003's input pins 1–7 are on the side facing the QFN. Buzz them out to
   the QFN pins. This gives (a) proof that `U5` is the motion controller and
   (b) the **12-bit motor pin map** you need for Option D. If instead the
   ULN2003 inputs trace to the JieLi chip, the architecture in
   [hardware.md §4.3](hardware.md#43-block-diagram-working-hypothesis) is wrong
   and everything downstream changes.
2. **ULN2003 common (pin 9) → which rail?**
   It tells you the motor supply: raw `VBAT` (~3.7 V) or a boosted rail. Also
   measure battery voltage and the `U10` output while running.
3. ~~**USB-C enumeration.**~~ — **answered: the port is charge-only** (no USB
   device appears on a PC). There is no USB upgrader, no CDC port, no field
   update path. Consequences:
   * Option B has to go through the **flash image** (CH341A) or a UART download
     mode on a debug header — never through USB.
   * The `J15` pads (`V+ / U_1 / U_2 / NC`) are now the *only* plausible
     in-system serial/debug doorway.

### 2.1 Observed boot behaviour (owner report)

Powering on with the button gives, in order:

1. a **voice welcome message** (so the JieLi chip, its flash and the speaker all
   work — the `JL` chip really is the voice/UI processor **[likely]**, and it
   fires before or independently of the motion controller);
2. **both arms drive to the middle** for a few seconds;
3. the **pen-lift motor drives upwards** (pen raised).

**This is a homing / zero-point calibration routine**, not a random wiggle
**[likely]**. Because the board has no encoders, no limit switches and (from the
photos) no current sensing, the firmware can only do one of two things:

* drive a fixed number of steps into a **mechanical hard stop** (the gearbox
  stalls, the motor just doesn't move any more — harmless with a Darlington
  driver), or
* drive a fixed number of steps to a **known geometric pose** that is defined by
  the linkage itself (e.g. both arms at the middle of their range).

Either way, the sequence tells you a lot:

* **Step rate / acceleration** can be measured from the audio or by ear/film
  (a phone at 240 fps is enough to count steps on a marked arm).
* **Direction convention** for each motor and the **magnitude of the travel**
  (time × step rate) → the axis zero reference the stock firmware uses.
* **Phase order & step mode** (wave / full / half step) come out of the logic
  analyser capture described in §2.2.

### 2.2 Capture the homing sequence (the best-value experiment)

Put a logic analyser on **the 12 ULN2003 input pins** (two 8-channel analysers, or
one 16-channel) and record a power-on:

```
sigrok-cli -d fx2lafw --config samplerate=1m --samples=20m \
           -C D0,D1,...D11 -o homing.sr
pulseview homing.sr        # then measure: period, duty, phase order, delays
```

From that single capture you get the **step pattern, the step frequency, the
acceleration profile, the channel→motor→wire mapping and the homing duration**
— i.e. the parts of the stock firmware you actually want to copy. This is
"reprogramming by observation" and it needs no firmware work at all. It is also
the correctness reference for the new controller ([controller.md](controller.md)).

Baseline for later comparisons: voice on boot, arms to middle, lift up, then
idle. Record whether the LEDs blink and what the 3 buttons do.

## 3. Option 0 — don't reprogram, drive the app side

If the robot has a companion app, the app almost certainly sends *drawings* to
the stock firmware. Talking that protocol yourself means you never touch the
firmware, keep the electronics intact, and still get arbitrary drawings.

### 3.1 First prove there is a radio (cheap, decides the whole branch)

Nothing in the photos proves one — see
[hardware.md §7.1](hardware.md#71-is-there-a-radio-at-all-evidence-so-far). The
chip family argues "probably", the physical evidence leans "maybe not". Check in
this order, stop as soon as one is decisive:

1. **Bottom of the PCB + around the `JL` chip:** PCB meander antenna (~25 mm),
   ceramic chip antenna (3×1.6 mm), or wire → **radio yes**. Look for the matching
   network (2–3 tiny passives off one pin) and an antenna keep-out.
2. **26 MHz crystal** near the `JL` chip → **radio yes**; no crystal anywhere →
   **radio no**, and this branch is dead.
3. **BLE scan** (nRF Connect / LightBlue, 60 s, buttons pressed) → a device means
   **radio yes**.
4. **FCC ID / CE-RED number** on label, box or manual → **radio yes**, and the ID
   leads to a public filing (frequency, modulation, often internal photos).

If the answer is "no radio", jump straight to Option D/E
([controller.md](controller.md)).

### 3.2 If there is a radio

1. Find the app (packaging/manual/QR code; search `KY-23` plus the brand in the
   app stores).
2. Decompile the APK (`jadx-gui`), grep for `BluetoothGatt`, UUIDs, `write`
   characteristics, and any `svg`/`path`/`coord` strings.
3. Capture live traffic: Android "Developer options → Enable Bluetooth HCI snoop
   log", or an nRF52 dongle with Wireshark, while drawing a simple shape in the
   app. Diff two recordings (a line vs a circle) to decode the format.
4. **Listen on the inter-chip UART** (`J15` pads `U_1`/`U_2`) *while the app draws*.
   The motion MCU `U5` has no radio, so any drawing data must reach it over that
   UART — this makes `J15` a man-in-the-middle point that exposes the real
   drawing protocol even if BLE is encrypted or proprietary.
5. Replay with your own tool (`bleak` in Python, or an ESP32 pretending to be the
   app). If the payload is raw coordinates, you can send your own paths.

This is the cheapest path to a usable result **if** the stock firmware accepts raw
paths. It fails if the app only sends canned "draw a cat" commands, or if there is
no radio at all.

## 4. Option A — dump / patch / reflash the SPI flashes

### 4.1 Shopping list

| Item | Why | Approx. price |
|---|---|---|
| CH341A programmer (with a **3.3 V** option; avoid 5 V-only clones) | SPI flash access | €5 |
| SOP-8 test clip (Pomona 5250 or clone), or hot air to lift the chip | in-circuit read/write | €3 |
| 1.8 V adapter *only if* the datasheet says so | safety | €4 |
| 8-channel logic analyser (clone, `sigrok`-compatible) | SPI/UART sniffing | €8 |

`KH25V8035` is an `MX25V8035`-compatible 8 Mbit (1 MB) SPI NOR part. Check the
`V`-series voltage window before applying power — **never** feed 5 V to it.
**[unverified — check the specific datasheet]**

### 4.2 Procedure

```bash
# 1. two independent reads of each chip (reseat the clip between reads)
flashrom -p ch341a_spi -r flash_A_1.bin
flashrom -p ch341a_spi -r flash_A_2.bin
sha256sum flash_A_1.bin flash_A_2.bin        # must match -> trustworthy dump

# 2. first look at what is inside
binwalk -E flash_A_1.bin                     # entropy: flat/high = compressed or encrypted
binwalk -Me flash_A_1.bin                    # embedded headers, audio, fonts
strings -n 6 -el flash_A_1.bin | head -50    # UTF-16LE, the usual home of Chinese strings
strings -n 6 flash_A_1.bin | grep -iE 'jie|ab53|ver|sdk|audio|mp3'

# 3. write it back UNCHANGED first and confirm the robot still boots
flashrom -p ch341a_spi -w flash_A_1.bin -v

# 4. only then start patching
flashrom -p ch341a_spi -w patched.bin -v
```

If `flashrom` cannot identify the part, use `SNANDer`, `AsProgrammer` or
`minipro` with the `MX25V8035` (or a generic 8 Mbit 25-series) profile.
In-circuit writing works because the SoC is unpowered; if a chip refuses to
erase, lift its `HOLD#`/`WP#` pins or desolder it.

### 4.3 What the dumps answer

* **Ownership:** the flash whose reads appear on the SPI bus at boot while `U5`'s
  GPIOs stay quiet belongs to the JieLi chip — confirm with a logic analyser on
  the four SPI lines.
* **Protection level:** readable strings and a normal-looking code blob = plain
  image; noise everywhere = encrypted/signed, and Options B/C become research
  projects rather than tasks.
* **Easy wins:** voice prompts, and often the drawing samples, live in resource
  blobs. Replacing a WAV in the flash is frequently the cheapest modification
  that works — if no CRC rejects it.

## 5. Option B — new firmware for the JieLi `AB25BP33704-55A0`

**Known** **[fact]**: Jieli (Zhuhai) dominates the sub-€1 toy audio/BT SoC
market; their parts boot a mask-ROM loader that can enter a download mode over
UART (and sometimes USB), and on the "AB" flash-less parts the application image
lives in external SPI flash.

**Unknown** **[unverified]**: the pinout of this 24-pin variant, which pins carry
UART0/download, whether the boot ROM validates a header/CRC, and whether Jieli
publishes an SDK for this sub-family. Expect a few hours on Chinese-language
sources (LCSC/立创商城, 芯查查, 云汉芯城, JieLi developer forums) before investing
further.

**Steps if you go ahead**

1. **Get or derive the pinout.** Either find a datasheet for `AB25BP33704` (LCSC
   part search is the fastest route) or derive it: with the robot running, probe
   every pin — the speaker (PWM/DAC pair), the SPI flash pins (CS/CLK/DI/DO),
   `VDD`/`GND`, and any 1–2 pins carrying UART traffic are identifiable from
   waveforms alone.
2. **Probe `J15`** (`V+`, `U_1`, `U_2`, `NC`) at boot. `U_1`/`U_2` read like
   **UART1/UART2** and `NC` like the **download/strap pin**; then repeat while
   holding `NC` to GND during power-up and see whether output stops (the ROM is
   waiting for a host).
3. **Sniff the SPI bus** at boot. If the SoC reads a header block and then
   streams code, the image is XIP + header → any patch must keep the header/CRC
   consistent, or you switch to the flash-emulator trick below.
4. **Get the tools.** Officially: JieLi's download/upgrade utility plus their
   (Keil-based, NDA) SDK. Unofficial copies circulate widely but are
   **proprietary and licence-encumbered** — asking Kaisiwei or JieLi for a dev
   kit is the clean route if anything you build is going to be published.
5. **Build the smallest possible change first** — an LED blink or a beep from a
   hello-world image. Only then touch drawing behaviour.
6. **Keep the original dump and the CH341A clip on the bench.** A bricked chip is
   a 3-minute restore unless boot-ROM OTP fuses were hit.

**Trick worth knowing:** rather than reflashing for every experiment, put a small
MCU (RP2040/Pi Pico) between the SoC and its flash, hold the SoC in reset,
preload a RAM buffer with your patched image and let the SoC XIP-read from the
emulator. Iteration drops from minutes to seconds and the real flash is never
touched.

## 6. Option C — new firmware for `U5`

Realistically **not worth it** unless `U5` turns out to be a familiar, documented
part (see [hardware.md §8](hardware.md#8-open-questions--next-experiments)).

* The marking is deliberately wiped → no datasheet → no toolchain, no register
  map, no pinout.
* Cheap Chinese QFN MCUs in this class are frequently **OTP** or come with
  read-out protection; some are 8051 cores with non-standard ISP protocols.
* Even if you identify it, you would be rewriting the entire motion stack (step
  generation, homing, IK, path planning) from scratch — which is exactly
  Option D, but with a worse toolchain.

Decision rule: if a photo with grazing light reveals a recognisable,
`flashrom`/ISP-supported part (e.g. GD32, STM32 clone, WCH CH32, Padauk, Holtek),
Option C becomes a normal firmware project. Otherwise skip it.

## 7. Option D — keep the mechanics, drive the ULN2003s yourself (recommended)

> Full design, BOM, pin map and firmware plan: **[controller.md](controller.md)**
> (Variant A there = this section, Variant B = Option E).

You do not need to understand *any* stock firmware to make this robot draw your
drawings. Everything the motors need is already on the board: **two ULN2003s,
12 channels, one per motor phase**, and the `V+`/GND pads on `J15` to power your
controller from the existing battery.

### 7.1 Hardware

1. **Map the 12 channels** (Phase 0 measurement #1): for each `电机n` pin, find
   the ULN2003 channel, then the `U5` pin that drives it. Write it into a table
   in `data/` — this is the single most valuable artifact of the whole project.
2. **Cut `U5` out of the loop.** Two options:
   * *Quick:* cut the 12 traces between `U5` and the ULN2003 inputs, then wire the
     ULN2003 input pads to your MCU. The ULN2003s still do the current switching;
     `U5` simply never toggles them again.
   * *Reversible:* don't cut anything — lift the 12 `U5` pins (or the 7 input
     pins of each ULN2003) and tack wires onto the ULN2003 input pads. Slightly
     more fiddly, fully undoable.
3. **Drop in a controller.** ESP32-S3/C6 or an RP2040: 12 GPIOs for motor
   phases, 1 for the speaker (optional), 2–3 for the buttons, 1–2 for an
   end-stop/LED. Powered from `V+` + a buck/boost to 3.3 V.
4. *Optional upgrade:* replace the ULN2003s with `A4988`/`DRV8825` chopper
   drivers (needs the motors to be re-wired per coil — only valid if Phase 0
   shows two independent coils). More torque, quieter, microstepping.

Sanity check before cutting anything: the ULN2003 inputs are high-impedance
Darlington bases; a 10 kΩ pulldown keeps the motors off while `U5` is
disconnected but still present.

### 7.2 Firmware you have to write

| Piece | Notes |
|---|---|
| 4-phase step sequencer | wave / half-step / full-step tables, ~1–2 kHz step rate, one timer per motor or a scheduler |
| Homing | drive each axis into its mechanical stop at low speed, then back off a fixed number of steps. No encoders → this is mandatory after every power-up. |
| Inverse kinematics | solve the 5-bar from `d`, `L1`, `L2`, pen offset (`docs/kinematics.md`, to be written once the lengths are measured) |
| Path format | simplest useful protocol: `MOVE x y` / `PEN up|down` lines over USB-serial |
| Front end (host) | convert SVG → polylines (`vpype`, `svg2gcode`, or a 30-line `svgpathtools` script), then stream to the robot |

Start with: pen up, jog each motor 200 steps, pen down. If the pen traces two
independent straight lines, the wiring map is right and everything else is
mathematics.

## 8. Option E — a new controller board

Only if Option D is blocked (e.g. the ULN2003s turn out to be wired in a way you
cannot sever), **or** if you simply want a quiet, modern machine (TMC2209 +
bipolar motors). You then keep the motors, gears, arms, pen holder and shell, and
replace PCB + firmware. Effort is dominated by the mechanics of mounting and by
re-making the motor harness — order 1–2 weekends plus PCB turnaround, and none of
it is needed to get moving.

Concrete BOM (ESP32‑S3 + 3× TMC2209 + power section), pin map, PCB notes and
firmware stack: **[controller.md](controller.md)** Variant B.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Bricking a SoC | Always have a verified double-read dump + CH341A clip before the first write. Write back the untouched image once and confirm it still boots. |
| Damaging pads/traces while cutting | Work under magnification, cut mid-trace rather than at the pad, and verify with continuity before/after. |
| Li-ion safety | Never leave the pack charging unattended during bench work; don't short `V+`; if the pack is a bare cell + protection board, keep the protection board. |
| 5 V on a 1.8 V part | Check the `KH25V8035` datasheet and use a level adapter if needed. |
| Wrong chip on the SPI clip | Verify pin-1 orientation twice; a rotated SOP-8 clip can destroy the part. |
| Licensing / legal | JieLi's SDK and download tool are proprietary. Building on leaked copies is legally murky; for anything public, ask the vendor, or choose Options 0/D which need nothing proprietary. |
| Wasted effort | The three measurements in §2 cost one evening and can invalidate whole branches — do them first. |

## 10. Decision tree

```
Start
 └─ Dump both flashes with CH341A (§4)        ← always, cheap, safe, informative
     ├─ Image readable (strings / code visible)?
     │    ├─ Yes ─► Is the app/BLE protocol enough? (§3) ── Yes ─► DONE (no mods)
     │    │                         └─ No ─► patch a resource blob (§4.3) and test
     │    │                                     └─ still not enough ─► Option B (full SDK)
     │    └─ No (encrypted/signed) ─► Option B is a research project
     └─ Want a drawing robot you control, not a firmware mod? ─► Option D
```

## 11. Record your measurements here

Fill this in as you go; it keeps the repo the single source of truth.

| Check | Result | Date |
|---|---|---|
| `U5` → ULN2003 input pin map (12 lines) | | |
| ULN2003 pin 9 (COM) rail voltage | | |
| Battery voltage / `U10` output | | |
| USB-C enumerates? (VID:PID) | | |
| `J15` `U_1`/`U_2` traffic at boot (baud, bytes) | | |
| Flash A dump sha256 (2 matching reads) | | |
| Flash B dump sha256 (2 matching reads) | | |
| Flash dumps: readable strings? encrypted? | | |
| `J16` FPC pin count | | |
| Linkage `d` / `L1` / `L2` / pen offset | | |

