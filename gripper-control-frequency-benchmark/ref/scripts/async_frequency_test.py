"""测量 Z-EFG-C65 的异步控制频率。

同步测试里，每一拍都是“写位置 + 读反馈”，下一条指令要等反馈回来。
异步测试把两件事拆开：

1. 指令线程只写位置，不等待运动结束，也不等待状态反馈。
2. 采样线程按固定频率单独读反馈，不挡在指令回路里。

RS485 是半双工，读和写仍共用同一条总线，所以采样会占用少量带宽。
指令频率看写位置本身能发多快；跟踪频率仍用反馈峰峰值相对指令的 -3 dB。
行程、速度、电流和同步测试一致，结果写到另一个文件，不覆盖同步数据。
"""

from __future__ import annotations

import argparse
import csv
import threading
import time

from response_frequency_test import (
    FREQUENCIES_HZ,
    MINUS_3_DB,
    SweepPoint,
    crossing,
    wait_reached,
)
from zefg_c65 import ZefgC65, ZefgC65Error


def benchmark_write_hz(gripper: ZefgC65, position_mm: float, seconds: float) -> tuple[float, int]:
    """只写位置、不读反馈，统计异步指令频率。"""
    count = 0
    errors = 0
    started = time.perf_counter()
    while time.perf_counter() - started < seconds:
        try:
            gripper.set_position(position_mm)
            count += 1
        except ZefgC65Error:
            errors += 1
    elapsed = time.perf_counter() - started
    return count / elapsed, errors


def run_async_square_wave(
    gripper: ZefgC65,
    center_mm: float,
    amplitude_mm: float,
    frequency_hz: float,
    sample_hz: float,
) -> SweepPoint:
    duration = max(2.0, 3.0 / frequency_hz)
    stop = threading.Event()
    bus = threading.Lock()
    samples: list[tuple[float, float]] = []
    write_count = 0
    errors = 0
    counter_lock = threading.Lock()
    started = time.perf_counter()

    def write_commands() -> None:
        nonlocal write_count, errors
        while not stop.is_set():
            now = time.perf_counter() - started
            high = int(now * frequency_hz * 2.0) % 2 == 0
            target = center_mm + amplitude_mm if high else center_mm - amplitude_mm
            try:
                with bus:
                    gripper.set_position(target)
            except ZefgC65Error:
                with counter_lock:
                    errors += 1
                continue
            with counter_lock:
                write_count += 1

    def read_feedback() -> None:
        period = 1.0 / sample_hz
        next_tick = time.perf_counter()
        while not stop.is_set():
            try:
                with bus:
                    status = gripper.read_status()
            except ZefgC65Error:
                with counter_lock:
                    errors += 1
            else:
                samples.append((time.perf_counter() - started, status.position_mm))
            next_tick += period
            delay = next_tick - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
            else:
                next_tick = time.perf_counter()

    writer = threading.Thread(target=write_commands, name="gripper-command")
    reader = threading.Thread(target=read_feedback, name="gripper-feedback")
    writer.start()
    reader.start()
    time.sleep(duration)
    stop.set()
    writer.join()
    reader.join()

    if len(samples) < 4:
        raise ZefgC65Error(f"{frequency_hz} Hz 有效样本不足")

    period = 1.0 / frequency_hz
    usable = [position for timestamp, position in samples if timestamp >= period]
    if len(usable) < 4:
        usable = [position for _, position in samples]
    peak_to_peak = max(usable) - min(usable)
    ratio = peak_to_peak / (2.0 * amplitude_mm)
    command_hz = write_count / duration
    return SweepPoint(frequency_hz, command_hz, peak_to_peak, ratio, errors)


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 Z-EFG-C65 异步控制频率")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--center", type=float, default=32.0, help="方波中心，mm")
    parser.add_argument("--amplitude", type=float, default=4.0, help="单侧幅度，mm")
    parser.add_argument("--speed", type=float, default=100.0, help="mm/s，最大 100")
    parser.add_argument("--current", type=float, default=0.5, help="A，最大 0.5")
    parser.add_argument("--sample-hz", type=float, default=25.0, help="反馈采样频率")
    args = parser.parse_args()

    low = args.center - args.amplitude
    high = args.center + args.amplitude
    if low < 0 or high > 65:
        raise SystemExit(f"方波范围 {low:.1f}~{high:.1f} mm 超出 0~65 mm")
    if args.sample_hz <= 0:
        raise SystemExit("反馈采样频率必须大于 0")

    kinematic_hz = args.speed / (4.0 * args.amplitude)
    print(
        f"异步方波 {args.center:.1f}±{args.amplitude:.1f} mm，"
        f"速度 {args.speed:.0f} mm/s，电流 {args.current:.2f} A，"
        f"反馈采样 {args.sample_hz:.0f} Hz"
    )
    print(f"忽略加减速时，走完这个方波的运动学上限约为 {kinematic_hz:.2f} Hz")

    points: list[SweepPoint] = []
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

        print("测量只写位置的异步指令频率...")
        write_hz, write_errors = benchmark_write_hz(gripper, args.center, 2.0)
        print(f"异步指令: {write_hz:.1f} Hz，失败 {write_errors} 次")

        for frequency in FREQUENCIES_HZ:
            if frequency > write_hz:
                print(f"{frequency:.1f} Hz 高于异步指令频率，停止扫频")
                break
            point = run_async_square_wave(
                gripper,
                args.center,
                args.amplitude,
                frequency,
                args.sample_hz,
            )
            points.append(point)
            print(
                f"{point.frequency_hz:5.1f} Hz  "
                f"指令发送 {point.command_hz:5.1f} Hz  "
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
    print(f"异步指令最高发送频率: {write_hz:.1f} Hz")
    if cutoff is None and points and points[-1].ratio >= MINUS_3_DB:
        print(f"-3 dB 跟踪频率: 高于已测最高 {points[-1].frequency_hz:.1f} Hz")
    elif cutoff is None:
        print("-3 dB 跟踪频率: 最低测试频率下已经低于 70.7%")
    else:
        print(f"-3 dB 跟踪频率: {cutoff:.2f} Hz")
    if half is not None:
        print(f"跟踪比降到 50% 的频率: {half:.2f} Hz")

    result_path = "async_frequency_test_result.csv"
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
        writer.writerow(["async_write_hz", f"{write_hz:.2f}"])
        writer.writerow(["sample_hz", f"{args.sample_hz:.2f}"])
        writer.writerow(["minus_3db_hz", "" if cutoff is None else f"{cutoff:.2f}"])
    print(f"扫频结果已写入 {result_path}")


if __name__ == "__main__":
    main()
