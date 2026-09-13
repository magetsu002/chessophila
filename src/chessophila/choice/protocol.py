from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Generic, Protocol, TypeVar

T = TypeVar("T")


class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class ChoiceBackend(Protocol[T]):
    """Convert one left/right presentation into a physical choice or non-response.

    A fly-connectome backend implements this protocol. The protocol deliberately knows
    nothing about chess, Stockfish, or opening names. Returning `None` means that the
    neural readout did not produce a decisive physical response.
    """

    def choose(self, *, left: T, right: T, seed: int) -> Side | None:
        ...


@dataclass(frozen=True, slots=True)
class Bout(Generic[T]):
    left: T
    right: T
    selected_side: Side | None
    selected: T | None
    seed: int


@dataclass(frozen=True, slots=True)
class Decision(Generic[T]):
    winner: T
    bouts: tuple[Bout[T], ...]


class InsufficientDecisionsError(RuntimeError):
    """Raised when bounded neural bouts do not produce enough decisive responses."""

    def __init__(self, message: str, bouts: tuple[object, ...]) -> None:
        super().__init__(message)
        self.bouts = bouts


@dataclass(slots=True)
class PairwiseProtocol(Generic[T]):
    """Resolve a noisy A/B preference with randomized left/right placement.

    `best_of` counts decisive responses and is intentionally odd. Non-responses are
    recorded but never coerced into a side. Total attempts are bounded by `max_bouts`.
    """

    backend: ChoiceBackend[T]
    best_of: int = 5
    seed: int = 0
    max_bouts: int | None = None

    def __post_init__(self) -> None:
        if self.best_of < 1 or self.best_of % 2 == 0:
            raise ValueError("best_of must be a positive odd integer")
        if self.max_bouts is not None and self.max_bouts < self.best_of:
            raise ValueError("max_bouts must be at least best_of")

    def decide(self, a: T, b: T) -> Decision[T]:
        if a == b:
            raise ValueError("pairwise candidates must be distinct")

        rng = random.Random(self.seed)
        a_wins = 0
        b_wins = 0
        bouts: list[Bout[T]] = []
        limit = self.max_bouts if self.max_bouts is not None else self.best_of * 3

        while a_wins + b_wins < self.best_of and len(bouts) < limit:
            if rng.getrandbits(1):
                left, right = a, b
            else:
                left, right = b, a

            bout_seed = rng.getrandbits(63)
            side = self.backend.choose(left=left, right=right, seed=bout_seed)
            selected: T | None
            if side is Side.LEFT:
                selected = left
            elif side is Side.RIGHT:
                selected = right
            elif side is None:
                selected = None
            else:
                raise ValueError(f"backend returned invalid side: {side!r}")

            if selected == a:
                a_wins += 1
            elif selected == b:
                b_wins += 1

            bouts.append(
                Bout(
                    left=left,
                    right=right,
                    selected_side=side,
                    selected=selected,
                    seed=bout_seed,
                )
            )

        if a_wins + b_wins < self.best_of:
            raise InsufficientDecisionsError(
                f"only {a_wins + b_wins} decisive responses in {len(bouts)} bouts",
                tuple(bouts),
            )

        winner = a if a_wins > b_wins else b
        return Decision(winner=winner, bouts=tuple(bouts))


@dataclass(slots=True)
class KnockoutProtocol(Generic[T]):
    """Select one candidate using repeated, randomized pairwise decisions.

    This is a transport protocol, not a claim that biological preferences are transitive.
    Every bout is returned so experiments can quantify bracket/order effects later.
    """

    backend: ChoiceBackend[T]
    best_of: int = 5
    seed: int = 0
    max_bouts: int | None = None

    def decide(self, candidates: Sequence[T]) -> Decision[T]:
        if not candidates:
            raise ValueError("at least one candidate is required")
        for index, candidate in enumerate(candidates):
            if any(candidate == prior for prior in candidates[:index]):
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
                    max_bouts=self.max_bouts,
                ).decide(a, b)
                next_round.append(decision.winner)
                bouts.extend(decision.bouts)

            round_candidates = next_round

        return Decision(winner=round_candidates[0], bouts=tuple(bouts))
