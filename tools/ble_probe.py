"""BLE 玩具协议探测脚本（最小可用版）

只做四件事：扫描、列 GATT、写一帧、听通知。
不猜、不扫全库、不做任何自动化动作 —— 每一步都由你手动发起。

用法：
    python ble_probe.py scan
    python ble_probe.py gatt   <ADDR>
    python ble_probe.py write  <ADDR> 03 12 80 00 00
    python ble_probe.py listen <ADDR> 30

依赖：bleak
"""
from __future__ import annotations

import asyncio
import sys

from bleak import BleakClient, BleakScanner


async def scan() -> None:
    print('扫描 8 秒…')
    devices = await BleakScanner.discover(timeout=8.0)
    for d in devices:
        name = d.name or '(无名字)'
        print(f'{d.address}  {name}')


async def gatt(addr: str) -> None:
    async with BleakClient(addr) as c:
        print(f'已连接 {addr}')
        for svc in c.services:
            print(f'\n[service] {svc.uuid}')
            for ch in svc.characteristics:
                props = ','.join(ch.properties)
                print(f'  [char] {ch.uuid}  handle=0x{ch.handle:04x}  ({props})')
                for dsc in ch.descriptors:
                    print(f'      [desc] {dsc.uuid}')


async def write(addr: str, hexs: list[str]) -> None:
    payload = bytes(int(x, 16) for x in hexs)
    frame = payload + b'\x00' * (20 - len(payload))
    if len(frame) > 20:
        print('帧超过 20 字节，拒绝发送')
        return
    async with BleakClient(addr) as c:
        # 写 fe02 必须 response=True；不同设备写特征可能不同，先跑 gatt 确认
        target = None
        for svc in c.services:
            for ch in svc.characteristics:
                if 'write' in ch.properties and ch.handle == 0x000C:
                    target = ch
        if target is None:
            print('没找到 handle 0x000c，先跑 gatt 看你的设备写特征在哪')
            return
        await c.write_gatt_char(target, frame, response=True)
        print('已发送：' + ' '.join(f'{b:02x}' for b in frame))


async def listen(addr: str, secs: int) -> None:
    def cb(_h, data: bytearray) -> None:
        print('notify:', ' '.join(f'{b:02x}' for b in data))

    async with BleakClient(addr) as c:
        started = []
        for svc in c.services:
            for ch in svc.characteristics:
                if 'notify' in ch.properties:
                    await c.start_notify(ch, cb)
                    started.append(ch.uuid)
        print(f'已订阅 {len(started)} 个通知特征，听 {secs} 秒…')
        await asyncio.sleep(secs)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == 'scan':
        asyncio.run(scan())
    elif cmd == 'gatt' and len(sys.argv) == 3:
        asyncio.run(gatt(sys.argv[2]))
    elif cmd == 'write' and len(sys.argv) >= 4:
        asyncio.run(write(sys.argv[2], sys.argv[3:]))
    elif cmd == 'listen' and len(sys.argv) == 4:
        asyncio.run(listen(sys.argv[2], int(sys.argv[3])))
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
