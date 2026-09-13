#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import chess
from brian2 import ms

from chessophila.choice import Side
from chessophila.neuro import NeuralChoiceTrace, ShiuChoiceBackend, ShiuSimulator
from chessophila.neuro.visual import load_visual_feature_map


def resulting_fen(uci: str) -> str:
    board = chess.Board()
    move = chess.Move.from_uci(uci)
    if move not in board.legal_moves:
        raise ValueError(f"illegal starting move: {uci}")
    board.push(move)
    return board.fen()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one real connectome chess A/B choice")
    parser.add_argument("--left", default="e2e4")
    parser.add_argument("--right", default="d2d4")
    parser.add_argument("--duration-ms", type=float, default=250.0)
    parser.add_argument("--seed", type=int, default=20260913)
    parser.add_argument(
        "--sim-root",
        type=Path,
        default=Path("vendor/drosophila_brain_model"),
    )
    args = parser.parse_args()

    mapping = load_visual_feature_map()
    left = mapping.encode_fen(resulting_fen(args.left), side=Side.LEFT)
    right = mapping.encode_fen(resulting_fen(args.right), side=Side.RIGHT)
    traces: list[NeuralChoiceTrace] = []
    backend = ShiuChoiceBackend(
        simulator=ShiuSimulator(args.sim_root, codegen_target="numpy"),
        readout=mapping.steering_readout(),
        parameter_overrides={"t_run": args.duration_ms * ms},
        on_trial=traces.append,
    )
    side = backend.choose(left=left, right=right, seed=args.seed)
    trace = traces[0]
    payload = {
        "left_move": args.left,
        "right_move": args.right,
        "seed": args.seed,
        "duration_ms": args.duration_ms,
        "stimulated_left": len(left.activated),
        "stimulated_right": len(right.activated),
        "dna02_left_spikes": trace.readout.left_spikes,
        "dna02_right_spikes": trace.readout.right_spikes,
        "choice": side.value if side is not None else None,
        "selected_move": (
            args.left if side is Side.LEFT else args.right if side is Side.RIGHT else None
        ),
        "active_neurons": len(trace.trial.spikes_by_flywire_id),
        "total_spikes": sum(len(v) for v in trace.trial.spikes_by_flywire_id.values()),
    }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
