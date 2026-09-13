#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brian2 import ms

from chessophila.chess import ChessPosition
from chessophila.choice import InsufficientDecisionsError, PairwiseProtocol
from chessophila.neuro import (
    NeuralChoiceTrace,
    ShiuChoiceBackend,
    ShiuSimulator,
    load_upstream_lock,
)
from chessophila.neuro.visual import VisualChessChoiceBackend, load_visual_feature_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Run randomized real-connectome chess A/B bouts")
    parser.add_argument("--a", default="e2e4")
    parser.add_argument("--b", default="d2d4")
    parser.add_argument("--best-of", type=int, default=3)
    parser.add_argument("--duration-ms", type=float, default=100.0)
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument("--sim-root", type=Path, default=Path("vendor/drosophila_brain_model"))
    args = parser.parse_args()

    candidates = {candidate.uci: candidate for candidate in ChessPosition().candidates()}
    if args.a not in candidates or args.b not in candidates:
        raise SystemExit("--a and --b must be legal moves from the starting position")

    mapping = load_visual_feature_map()
    traces: list[NeuralChoiceTrace] = []
    neural = ShiuChoiceBackend(
        simulator=ShiuSimulator(args.sim_root, codegen_target="numpy"),
        readout=mapping.steering_readout(),
        parameter_overrides={"t_run": args.duration_ms * ms},
        on_trial=traces.append,
    )
    backend = VisualChessChoiceBackend(neural, mapping)
    protocol = PairwiseProtocol(
        backend=backend,
        best_of=args.best_of,
        seed=args.seed,
        max_bouts=args.best_of * 3,
    )
    try:
        decision = protocol.decide(candidates[args.a], candidates[args.b])
    except InsufficientDecisionsError as exc:
        print(json.dumps({"winner": None, "error": str(exc)}, indent=2))
        return 2

    lock = load_upstream_lock()
    bouts = []
    for bout, trace in zip(decision.bouts, traces, strict=True):
        bouts.append({
            "left": bout.left.uci,
            "right": bout.right.uci,
            "left_fen": bout.left.resulting_fen,
            "right_fen": bout.right.resulting_fen,
            "dna02_left_spikes": trace.readout.left_spikes,
            "dna02_right_spikes": trace.readout.right_spikes,
            "selected_side": bout.selected_side.value if bout.selected_side else None,
            "selected_move": bout.selected.uci if bout.selected else None,
            "seed": bout.seed,
            "active_neurons": len(trace.trial.spikes_by_flywire_id),
            "total_spikes": sum(len(v) for v in trace.trial.spikes_by_flywire_id.values()),
        })
    payload = {
        "schema_version": 1,
        "source": "real-connectome",
        "simulator": {
            "name": lock.name,
            "commit": lock.commit,
            "flywire_materialization": lock.flywire_materialization,
            "codegen": "numpy",
        },
        "experiment": {
            "a": args.a,
            "b": args.b,
            "best_of": args.best_of,
            "duration_ms": args.duration_ms,
            "seed": args.seed,
        },
        "winner": decision.winner.uci,
        "bouts": bouts,
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
