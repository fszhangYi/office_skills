"""测量 Z-EFG-C65 的数据读取频率。

只发 Modbus 0x03 读寄存器，不写位置、不让夹爪运动。
主结果是连续读取 0x0040~0x0047 这一帧状态的频率，
内容和驱动里的 read_status() 相同：初始化、夹持状态、位置、速度、电流。
另外各测一次单寄存器和位置浮点，用来看帧长对读取频率的影响。
"""

from __future__ import annotations

import argparse
import csv
import time
from dataclasses import dataclass

from zefg_c65 import REG_GRIP_STATUS, REG_POSITION_FB, ZefgC65, ZefgC65Error


@dataclass
class ReadResult:
    name: str
    registers: int
    hz: float
    period_ms: float
    min_ms: float
    max_ms: float
    errors: int


def benchmark(name: str, registers: int, seconds: float, read_once) -> ReadResult:
    intervals: list[float] = []
    errors = 0
    previous = time.perf_counter()
    started = previous
    while time.perf_counter() - started < seconds:
        try:
            read_once()
        except ZefgC65Error:
            errors += 1
            previous = time.perf_counter()
            continue
        now = time.perf_counter()
        intervals.append(now - previous)
        previous = now
    elapsed = time.perf_counter() - started
    count = len(intervals)
    if count == 0:
        raise ZefgC65Error(f"{name} 没有成功读到数据")
    period = sum(intervals) / count
    return ReadResult(
        name=name,
        registers=registers,
        hz=count / elapsed,
        period_ms=period * 1000.0,
        min_ms=min(intervals) * 1000.0,
        max_ms=max(intervals) * 1000.0,
        errors=errors,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="测试 Z-EFG-C65 数据读取频率")
    parser.add_argument("--port", default="COM3")
    parser.add_argument("--seconds", type=float, default=3.0, help="每一项的测量时长")
    args = parser.parse_args()
    if args.seconds <= 0:
        raise SystemExit("测量时长必须大于 0")

    with ZefgC65(args.port, timeout=0.2) as gripper:
        print(f"当前: {gripper.read_status()}")
        cases = (
            ("状态帧 8 寄存器", 8, gripper.read_status),
            ("位置反馈 2 寄存器", 2, lambda: gripper.read_float(REG_POSITION_FB)),
            ("夹持状态 1 寄存器", 1, lambda: gripper.read_u16(REG_GRIP_STATUS)),
        )
        results = []
        for name, registers, read_once in cases:
            print(f"测量{name}...")
            result = benchmark(name, registers, args.seconds, read_once)
            results.append(result)
            print(
                f"{result.name}: {result.hz:.1f} Hz，"
                f"周期 {result.period_ms:.2f} ms，"
                f"最短 {result.min_ms:.2f} ms，最长 {result.max_ms:.2f} ms，"
                f"失败 {result.errors} 次"
            )

    status_hz = results[0].hz
    print()
    print(f"状态数据最高读取频率: {status_hz:.1f} Hz")

    result_path = "read_frequency_test_result.csv"
    with open(result_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["name", "registers", "hz", "period_ms", "min_ms", "max_ms", "errors"]
        )
        for result in results:
            writer.writerow(
                [
                    result.name,
                    result.registers,
                    f"{result.hz:.2f}",
                    f"{result.period_ms:.3f}",
                    f"{result.min_ms:.3f}",
                    f"{result.max_ms:.3f}",
                    result.errors,
                ]
            )
    print(f"结果已写入 {result_path}")


if __name__ == "__main__":
    main()
