from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
from typing import Protocol, Sequence, TypeVar

T = TypeVar("T")


class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class ChoiceBackend(Protocol[T]):
    """Backend that converts one left/right presentation into one physical choice.

    A future fly-connectome backend implements this protocol. The protocol deliberately
    knows nothing about chess, Stockfish, or opening names.
    """

    def choose(self, *, left: T, right: T, seed: int) -> Side:
        ...


@dataclass(frozen=True, slots=True)
class Bout[T]:
    left: T
    right: T
    selected_side: Side
    selected: T
    seed: int


@dataclass(frozen=True, slots=True)
class Decision[T]:
    winner: T
    bouts: tuple[Bout[T], ...]


@dataclass(slots=True)
class PairwiseProtocol[T]:
    """Resolve a noisy A/B preference with randomized left/right placement.

    `best_of` is intentionally odd, which prevents tied pairwise votes. Orientation is
    randomized independently for every bout to stop a fixed turning bias from becoming
    a chess preference.
    """

    backend: ChoiceBackend[T]
    best_of: int = 5
    seed: int = 0

    def __post_init__(self) -> None:
        if self.best_of < 1 or self.best_of % 2 == 0:
            raise ValueError("best_of must be a positive odd integer")

    def decide(self, a: T, b: T) -> Decision[T]:
        if a == b:
            raise ValueError("pairwise candidates must be distinct")

        rng = random.Random(self.seed)
        wins = {a: 0, b: 0}
        bouts: list[Bout[T]] = []

        for _ in range(self.best_of):
            if rng.getrandbits(1):
                left, right = a, b
            else:
                left, right = b, a

            bout_seed = rng.getrandbits(63)
            side = self.backend.choose(left=left, right=right, seed=bout_seed)
            if side is Side.LEFT:
                selected = left
            elif side is Side.RIGHT:
                selected = right
            else:
                raise ValueError(f"backend returned invalid side: {side!r}")

            wins[selected] += 1
            bouts.append(
                Bout(
                    left=left,
                    right=right,
                    selected_side=side,
                    selected=selected,
                    seed=bout_seed,
                )
            )

        winner = a if wins[a] > wins[b] else b
        return Decision(winner=winner, bouts=tuple(bouts))


@dataclass(slots=True)
class KnockoutProtocol[T]:
    """Select one candidate using repeated, randomized pairwise decisions.

    This is a transport protocol, not a claim that biological preferences are transitive.
    Every bout is returned so experiments can quantify bracket/order effects later.
    """

    backend: ChoiceBackend[T]
    best_of: int = 5
    seed: int = 0

    def decide(self, candidates: Sequence[T]) -> Decision[T]:
        if not candidates:
            raise ValueError("at least one candidate is required")
        if len(set(candidates)) != len(candidates):
            raise ValueError("candidates must be unique")
        if len(candidates) == 1:
            return Decision(winner=candidates[0], bouts=())

        rng = random.Random(self.seed)
        round_candidates = list(candidates)
        rng.shuffle(round_candidates)
        bouts: list[Bout[T]] = []

        while len(round_candidates) > 1:
            next_round: list[T] = []
            iterator = iter(round_candidates)
            for a in iterator:
                b = next(iterator, None)
                if b is None:
                    next_round.append(a)
                    continue

                pair_seed = rng.getrandbits(63)
                decision = PairwiseProtocol(
                    backend=self.backend,
                    best_of=self.best_of,
                    seed=pair_seed,
                ).decide(a, b)
                next_round.append(decision.winner)
                bouts.extend(decision.bouts)

            round_candidates = next_round

        return Decision(winner=round_candidates[0], bouts=tuple(bouts))
