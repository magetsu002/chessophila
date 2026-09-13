# Chessophila

**Can a biologically grounded fruit-fly connectome learn useful chess preferences?**

Chessophila is an experimental harness for connecting a reproducible Drosophila neural
simulation to chess decisions while keeping the scientific boundary explicit. The fly
will not receive opening names or a hidden chess policy. Chess supplies legal candidate
states; the neural system supplies physical choices; reward and plasticity are separate,
versioned experimental components.

## Current milestone: M0 — choice harness

The first implementation establishes the interface that a real connectome backend must
satisfy:

```text
chess position
    -> legal resulting positions
    -> randomized left/right A/B bouts
    -> neural physical choice
    -> pairwise decision
    -> optional multi-candidate knockout
    -> complete bout log
```

M0 intentionally does **not** ship a fake "fly brain". The backend protocol exists so the
published simulator can be integrated without letting chess logic leak into the neural
choice layer.

See [`docs/EXPERIMENT.md`](docs/EXPERIMENT.md) for the falsifiable experiment contract and
required controls.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
```

## Near-term milestones

- **M0:** deterministic chess candidate generation and bias-resistant A/B choice protocol
- **M1:** pin and reproduce a published connectome simulation baseline
- **M2:** map controlled sensory input and descending/motor readout to the A/B protocol
- **M3:** validate one bounded plasticity/reward experiment before claiming chess learning
- **M4:** curriculum from simple value discrimination to complete legal chess positions
- **M5:** live/replay 3D laboratory viewer driven only by real telemetry

## Scientific honesty

A connectome-derived simulation is not a perfect digital animal. Neural dynamics,
sensory encoding, readout, plasticity, and embodiment each introduce assumptions. The
repository will version those assumptions and keep negative results.
