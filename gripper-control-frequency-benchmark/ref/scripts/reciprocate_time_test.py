"""测量 Z-EFG-C65 最快往复运动耗时。

满行程 0 mm ↔ 65 mm，速度 100 mm/s，电流 0.5 A。
先到闭合位置，然后重复“张开再闭合”。每一程从发出位置指令开始计时，
到反馈位置进入目标 0.5 mm 且不再运动时停止。
往复耗时是同一周期内张开与闭合两段之和，最后给出最快的一次。
"""

from __future__ import annotations

import argparse
import csv
import time

from zefg_c65 import POSITION_MAX_MM, ZefgC65, ZefgC65Error

CLOSED_MM = 0.0
OPEN_MM = POSITION_MAX_MM
TOLERANCE_MM = 0.5


def wait_reached(gripper: ZefgC65, target_mm: float, timeout: float) -> None:
    deadline = time.perf_counter() + timeout
    status = gripper.read_status()
    while time.perf_counter() < deadline:
        status = gripper.read_status()
        if abs(status.position_mm - target_mm) <= TOLERANCE_MM and not status.moving:
            return
        time.sleep(0.01)
    raise ZefgC65Error(f"未能到达 {target_mm:.1f} mm: {status}")


def time_move(gripper: ZefgC65, target_mm: float, timeout: float) -> tuple[float, float]:
    """返回指令到到位的耗时，以及到位时的位置。"""
    started = time.perf_counter()
    gripper.set_position(target_mm)
    deadline = started + timeout
    settled_at: float | None = None
    status = gripper.read_status()
    while time.perf_counter() < deadline:
        status = gripper.read_status()
        arrived = abs(status.position_mm - target_mm) <= TOLERANCE_MM and not status.moving
        now = time.perf_counter()
        if arrived:
            if settled_at is None:
                settled_at = now
            else:
                return settled_at - started, status.position_mm
        else:
            settled_at = None
    raise ZefgC65Error(f"运动超时，目标 {target_mm:.1f} mm: {status}")


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 Z-EFG-C65 最快往复运动耗时")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--cycles", type=int, default=5, help="往复次数")
    parser.add_argument("--speed", type=float, default=100.0, help="mm/s，最大 100")
    parser.add_argument("--current", type=float, default=0.5, help="A，最大 0.5")
    parser.add_argument("--timeout", type=float, default=4.0, help="单程超时，秒")
    args = parser.parse_args()
    if args.cycles < 1:
        raise SystemExit("往复次数至少为 1")

    print(
        f"满行程 {CLOSED_MM:.0f} mm ↔ {OPEN_MM:.0f} mm，"
        f"速度 {args.speed:.0f} mm/s，电流 {args.current:.2f} A，"
        f"共 {args.cycles} 次往复"
    )

    rows: list[tuple[int, str, float, float]] = []
    with ZefgC65(args.port, timeout=0.2) as gripper:
        status = gripper.read_status()
        print(f"当前: {status}")
        if not status.initialized:
            print("尚未初始化，先找零")
            gripper.initialize()
            wait_reached(gripper, OPEN_MM, timeout=15.0)

        gripper.set_speed(args.speed)
        gripper.set_current(args.current)
        print("先移动到闭合位置")
        gripper.set_position(CLOSED_MM)
        wait_reached(gripper, CLOSED_MM, args.timeout)
        print(gripper.read_status())

        for cycle in range(1, args.cycles + 1):
            open_s, open_mm = time_move(gripper, OPEN_MM, args.timeout)
            close_s, close_mm = time_move(gripper, CLOSED_MM, args.timeout)
            round_s = open_s + close_s
            rows.append((cycle, "张开", open_s, open_mm))
            rows.append((cycle, "闭合", close_s, close_mm))
            print(
                f"第 {cycle} 次  张开 {open_s:.3f} s → {open_mm:.2f} mm，"
                f"闭合 {close_s:.3f} s → {close_mm:.2f} mm，"
                f"往复 {round_s:.3f} s"
            )

    round_times = []
    for cycle in range(1, args.cycles + 1):
        pair = [row[2] for row in rows if row[0] == cycle]
        round_times.append((cycle, pair[0], pair[1], pair[0] + pair[1]))
    fastest = min(round_times, key=lambda item: item[3])
    open_times = [item[1] for item in round_times]
    close_times = [item[2] for item in round_times]
    totals = [item[3] for item in round_times]

    print()
    print(
        f"最快往复: 第 {fastest[0]} 次，{fastest[3]:.3f} s"
        f"（张开 {fastest[1]:.3f} s，闭合 {fastest[2]:.3f} s）"
    )
    print(
        f"平均  张开 {sum(open_times) / len(open_times):.3f} s，"
        f"闭合 {sum(close_times) / len(close_times):.3f} s，"
        f"往复 {sum(totals) / len(totals):.3f} s"
    )
    print("手册给出的单向满行程最短时间是 0.7 s")

    result_path = "reciprocate_time_test_result.csv"
    with open(result_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["cycle", "direction", "seconds", "end_position_mm"])
        for cycle, direction, seconds, position in rows:
            writer.writerow([cycle, direction, f"{seconds:.3f}", f"{position:.3f}"])
        writer.writerow([])
        writer.writerow(["fastest_cycle", fastest[0]])
        writer.writerow(["fastest_open_s", f"{fastest[1]:.3f}"])
        writer.writerow(["fastest_close_s", f"{fastest[2]:.3f}"])
        writer.writerow(["fastest_round_trip_s", f"{fastest[3]:.3f}"])
    print(f"结果已写入 {result_path}")


if __name__ == "__main__":
    main()
