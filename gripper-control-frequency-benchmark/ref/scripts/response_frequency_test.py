"""测量 Z-EFG-C65 的同步控制频率。

分两项：

1. 通信回路频率：连续“写位置 + 读反馈”每秒能完成多少次。
   这项写的是同一个位置，手指不动，测的是总线往返上限。
2. 位置跟踪频率：在中位附近做小幅度方波，升高频率，
   直到反馈峰峰值掉到指令峰峰值的 70.7%（-3 dB）以下。
   这项才是夹爪机械响应能跟上的最高频率。

默认行程 32±4 mm，速度 100 mm/s，电流 0.5 A，避免撞到 0 mm 和 65 mm。
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass

from zefg_c65 import ZefgC65, ZefgC65Error

FREQUENCIES_HZ = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 15.0)
MINUS_3_DB = 0.707


@dataclass
class SweepPoint:
    frequency_hz: float
    command_hz: float
    peak_to_peak_mm: float
    ratio: float
    errors: int


def wait_reached(gripper: ZefgC65, target_mm: float, timeout: float = 8.0) -> None:
    deadline = time.perf_counter() + timeout
    status = gripper.read_status()
    while time.perf_counter() < deadline:
        status = gripper.read_status()
        if abs(status.position_mm - target_mm) <= 1.0 and not status.moving:
            print(f"到位: {status}")
            return
        time.sleep(0.02)
    raise ZefgC65Error(f"未能到达 {target_mm:.1f} mm: {status}")


def benchmark_sync_hz(gripper: ZefgC65, position_mm: float, seconds: float) -> tuple[float, int]:
    """同一位置反复写读，统计同步回路频率。"""
    count = 0
    errors = 0
    started = time.perf_counter()
    while time.perf_counter() - started < seconds:
        try:
            gripper.set_position(position_mm)
            gripper.read_status()
            count += 1
        except ZefgC65Error:
            errors += 1
    elapsed = time.perf_counter() - started
    return count / elapsed, errors


def run_square_wave(
    gripper: ZefgC65,
    center_mm: float,
    amplitude_mm: float,
    frequency_hz: float,
) -> SweepPoint:
    duration = max(2.0, 3.0 / frequency_hz)
    samples: list[tuple[float, float]] = []
    errors = 0
    started = time.perf_counter()
    while True:
        now = time.perf_counter() - started
        if now >= duration:
            break
        high = int(now * frequency_hz * 2.0) % 2 == 0
        target = center_mm + amplitude_mm if high else center_mm - amplitude_mm
        try:
            gripper.set_position(target)
            status = gripper.read_status()
        except ZefgC65Error:
            errors += 1
            continue
        samples.append((now, status.position_mm))
    if len(samples) < 4:
        raise ZefgC65Error(f"{frequency_hz} Hz 有效样本不足")

    period = 1.0 / frequency_hz
    usable = [position for timestamp, position in samples if timestamp >= period]
    if len(usable) < 4:
        usable = [position for _, position in samples]
    peak_to_peak = max(usable) - min(usable)
    ratio = peak_to_peak / (2.0 * amplitude_mm)
    command_hz = len(samples) / duration
    return SweepPoint(frequency_hz, command_hz, peak_to_peak, ratio, errors)


def crossing(points: list[SweepPoint], level: float) -> float | None:
    """在跌破 level 的相邻两点之间线性插值。"""
    for earlier, later in zip(points, points[1:]):
        if earlier.ratio >= level > later.ratio:
            span = earlier.ratio - later.ratio
            if span <= 0:
                return later.frequency_hz
            fraction = (earlier.ratio - level) / span
            return earlier.frequency_hz + (later.frequency_hz - earlier.frequency_hz) * fraction
    if points and points[-1].ratio >= level:
        return None
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 Z-EFG-C65 同步控制频率")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--center", type=float, default=32.0, help="方波中心，mm")
    parser.add_argument("--amplitude", type=float, default=4.0, help="单侧幅度，mm")
    parser.add_argument("--speed", type=float, default=100.0, help="mm/s，最大 100")
    parser.add_argument("--current", type=float, default=0.5, help="A，最大 0.5")
    args = parser.parse_args()

    low = args.center - args.amplitude
    high = args.center + args.amplitude
    if low < 0 or high > 65:
        raise SystemExit(f"方波范围 {low:.1f}~{high:.1f} mm 超出 0~65 mm")

    kinematic_hz = args.speed / (4.0 * args.amplitude)
    print(
        f"方波 {args.center:.1f}±{args.amplitude:.1f} mm，"
        f"速度 {args.speed:.0f} mm/s，电流 {args.current:.2f} A"
    )
    print(
        f"忽略加减速时，走完这个方波的运动学上限约为 {kinematic_hz:.2f} Hz"
    )

    with ZefgC65(args.port, timeout=0.2) as gripper:
        status = gripper.read_status()
        print(f"当前: {status}")
        if not status.initialized:
            print("尚未初始化，先找零")
            gripper.initialize()
            wait_reached(gripper, 65.0, timeout=15.0)

        gripper.set_speed(args.speed)
        gripper.set_current(args.current)
        print(f"移动到中心 {args.center:.1f} mm")
        gripper.set_position(args.center)
        wait_reached(gripper, args.center)

        print("测量写位置+读反馈的同步回路频率...")
        sync_hz, sync_errors = benchmark_sync_hz(gripper, args.center, 2.0)
        print(f"同步回路: {sync_hz:.1f} Hz，失败 {sync_errors} 次")

        points: list[SweepPoint] = []
        for frequency in FREQUENCIES_HZ:
            if frequency > sync_hz:
                print(f"{frequency:.1f} Hz 高于通信回路，停止扫频")
                break
            point = run_square_wave(gripper, args.center, args.amplitude, frequency)
            points.append(point)
            print(
                f"{point.frequency_hz:5.1f} Hz  "
                f"指令回路 {point.command_hz:5.1f} Hz  "
                f"反馈峰峰 {point.peak_to_peak_mm:5.2f} mm  "
                f"跟踪比 {point.ratio:5.1%}  "
                f"失败 {point.errors}"
            )
            if point.ratio < 0.25:
                print("跟踪比已低于 25%，停止扫频")
                break

        gripper.set_position(args.center)

    cutoff = crossing(points, MINUS_3_DB)
    half = crossing(points, 0.5)
    print()
    print(f"同步回路最高发送频率: {sync_hz:.1f} Hz")
    if cutoff is None and points and points[-1].ratio >= MINUS_3_DB:
        print(f"-3 dB 跟踪频率: 高于已测最高 {points[-1].frequency_hz:.1f} Hz")
    elif cutoff is None:
        print("-3 dB 跟踪频率: 最低测试频率下已经低于 70.7%")
    else:
        print(f"-3 dB 跟踪频率: {cutoff:.2f} Hz")
    if half is not None:
        print(f"跟踪比降到 50% 的频率: {half:.2f} Hz")

    result_path = "frequency_test_result.csv"
    with open(result_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["frequency_hz", "command_hz", "peak_to_peak_mm", "ratio", "errors"]
        )
        for point in points:
            writer.writerow(
                [
                    f"{point.frequency_hz:.2f}",
                    f"{point.command_hz:.2f}",
                    f"{point.peak_to_peak_mm:.3f}",
                    f"{point.ratio:.4f}",
                    point.errors,
                ]
            )
        writer.writerow([])
        writer.writerow(["sync_loop_hz", f"{sync_hz:.2f}"])
        writer.writerow(["minus_3db_hz", "" if cutoff is None else f"{cutoff:.2f}"])
    print(f"扫频结果已写入 {result_path}")


if __name__ == "__main__":
    main()
