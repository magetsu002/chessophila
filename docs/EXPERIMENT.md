# Experiment contract

Chessophila is an experiment, not a chess-themed animation. The repository keeps the chess environment, neural decision system, reward/plasticity model, and viewer separate so each claim can be tested independently.

## Validation criterion

A pinned connectome simulation must make a reproducible left/right decision between two legal chess continuations, with the complete physical presentation and neural readout recorded.

Passing this criterion does **not** mean that the fly understands chess or has learned an opening. Those are stronger claims that require separate learning experiments and controls.

## Decision interface

A legal chess position is converted into candidate resulting positions. A trial presents two candidates as left/right sensory stimuli. The neural backend may return a physical choice (`left` or `right`) or no decisive response. A non-response is logged and may trigger another bounded bout; it is never coerced into a chess move. The backend does not receive SAN/UCI notation, opening names, engine rankings, or the identity of the rewarded move.

Because biological output is noisy, one pairwise decision targets an odd number of decisive bouts. Left/right placement is randomized independently for every bout. Multi-move chess positions can be reduced through a randomized knockout bracket; experiments must measure and report bracket/order effects rather than assuming pairwise preferences are transitive.

## Required trial record

Every real neural bout must eventually persist at least:

- experiment/version identifier
- simulator commit and connectome dataset identifier/checksum
- plasticity/checkpoint identifier
- RNG seed
- source FEN
- left and right resulting positions
- left/right stimulus mapping
- raw neural readout needed to reproduce the decoded side
- decoded physical side or explicit non-response
- selected chess candidate, if any
- reward/punishment delivered after the decision
- timing information

## Controls required before chess-learning claims

At minimum:

1. neutral A/B baseline to quantify fixed turning bias
2. randomized left/right presentation
3. reversed stimulus mapping
4. frozen-plasticity control
5. no-reward or shuffled-reward control
6. held-out positions not used during training
7. deterministic replay from saved seeds/checkpoints where the simulator permits it

A result that fails these controls is reported as a failure or artifact, not learning.

## Engine boundary

Stockfish may be used as an **external evaluator/critic** during selected curriculum experiments. It must never make the fly's choice. Exact engine scores should not be fed as a hidden policy signal; reward shaping must be explicit, bounded, versioned, and reported.

## Visualization boundary

The 3D viewer consumes recorded/live telemetry. It never fabricates neural choices. Any stylized brain rendering must distinguish measured activity from purely decorative visual effects.
