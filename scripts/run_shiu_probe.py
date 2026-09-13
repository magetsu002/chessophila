#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter

from brian2 import ms

from chessophila.neuro import ShiuSimulator, load_upstream_lock

SUGAR_GRNS_V783 = (
    720575940624963786, 720575940630233916, 720575940637568838,
    720575940638202345, 720575940617000768, 720575940630797113,
    720575940632889389, 720575940621754367, 720575940621502051,
    720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239,
    720575940629176663, 720575940611875570,
)
V630_SUGAR_GRN_NOT_IN_V783 = 720575940620900446
MN9 = 720575940660219265


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a real Shiu/FlyWire sugar-response probe")
    parser.add_argument("--root", type=Path, default=Path("vendor/drosophila_brain_model"))
    parser.add_argument("--duration-ms", type=float, default=1000.0)
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.duration_ms <= 0:
        raise SystemExit("--duration-ms must be positive")
    if args.top < 0:
        raise SystemExit("--top cannot be negative")

    lock = load_upstream_lock()
    simulator = ShiuSimulator(args.root)
    started = perf_counter()
    result = simulator.run_trial(
        activated=SUGAR_GRNS_V783,
        seed=args.seed,
        parameter_overrides={"t_run": args.duration_ms * ms},
    )
    elapsed = perf_counter() - started
    counts = {flywire_id: len(times) for flywire_id, times in result.spikes_by_flywire_id.items()}
    top = sorted(counts.items(), key=lambda item: item[1], reverse=True)[: args.top]

    summary = {
        "simulator_commit": lock.commit,
        "flywire_materialization": lock.flywire_materialization,
        "seed": args.seed,
        "duration_ms": args.duration_ms,
        "elapsed_s": round(elapsed, 3),
        "input_neurons": len(SUGAR_GRNS_V783),
        "active_neurons": sum(count > 0 for count in counts.values()),
        "total_spikes": sum(counts.values()),
        "sugar_spikes": sum(counts.get(flywire_id, 0) for flywire_id in SUGAR_GRNS_V783),
        "mn9_spikes": counts.get(MN9, 0),
        "v630_unmapped_sugar_grn": V630_SUGAR_GRN_NOT_IN_V783,
        "top_neurons": [{"flywire_id": key, "spikes": value} for key, value in top],
    }

    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        for key, value in summary.items():
            if key != "top_neurons":
                print(f"{key}: {value}")
        print("top_neurons:")
        for item in summary["top_neurons"]:
            print(f"  {item['flywire_id']}: {item['spikes']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
