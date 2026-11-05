# Xingzhi (COC) BLE toy — control protocol notes

Field notes on the control frames of a Chinese Bluetooth sex toy (product name 「星织」 / Xingzhi).
**Every conclusion below was verified by packet capture plus live replay.** Anything unverified is marked as such.

Why this exists: when we needed a reference for this class of device, there was none. So here it is, to save the next person a few nights.

> **Scope**: control only ("how to make it move"). No personal data, no device serial numbers, no pairing records.
>
> **Status**: unofficial, unaffiliated with the vendor, contains no vendor source code, installers or firmware.
>
> **Experimental**: confirm the device state before replaying frames, and keep a physical way to stop it.

---

## TL;DR

```
Write channel   fe02 (handle 0x000c), fixed 20-byte frames
Frame layout    [channel][0x12][arg][0x00][extra][ ... zero-padded to 20 bytes ]
Channels        0x01 vibration mode / 0x02 suction mode / 0x03 vibration intensity
Read direction  fe01, ff14 never return data -> no readable sensors on this device
```

Full frame table: [`protocol/frames.md`](protocol/frames.md) (Chinese).

---

## How it was verified

1. Enabled Bluetooth HCI snoop logging in Android developer options, then reproduced every action in the vendor app
2. Pulled `btsnoop_hci.log` with `adb bugreport`
3. `tshark -r btsnoop_hci.log -Y "btatt.opcode == 0x52"` to extract all Write Commands
4. Grouped by handle → the traffic was all on `0x000c` (characteristic `fe02`), **not** `ff15` as initially guessed
5. Replayed frames one by one with Python + `bleak` and observed the mechanical response

**The mistake worth repeating**: we first wrote to `ff15` because it looked like the obvious write characteristic. Fifteen raw commands, zero response — that characteristic does not participate in control. **Don't trust "which characteristic looks writable"; read the capture.**

---

## Evidence levels

| Claim | Level | Basis |
|---|---|---|
| Write channel is `fe02` / handle `0x000c` | **verified** | all 625 captured writes land there; replay works |
| `03 12 XX` = intensity, linear | **verified** | `20/80/FF` increases; `00` stops immediately |
| `01 12 NN` = vibration mode (0–4) | **verified** | rhythm changes with NN |
| `02 12 NN` = suction mode (0–5) | **weak** | device was still vacuum-sealed, mechanically constrained |
| Device reports pressure / force | **no** | `fe01`/`ff14` never notify; only a 10 s `64 00 00` heartbeat |
| `ff15` also controls it | **no** | 15 raw commands + 7-byte frames, zero response |

---

## Minimal tooling

```bash
pip install -r tools/requirements.txt
python tools/ble_probe.py scan
python tools/ble_probe.py gatt  <ADDR>
python tools/ble_probe.py write <ADDR> 03 12 80 00 00
python tools/ble_probe.py listen <ADDR> 30
```

Writing to `fe02` requires a Write Request (`response=True` in bleak); Write Command is ignored.

---

## License

MIT.
