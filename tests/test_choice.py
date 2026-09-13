from dataclasses import dataclass, field

import pytest

from chessophila.choice import (
    InsufficientDecisionsError,
    KnockoutProtocol,
    PairwiseProtocol,
    Side,
)


@dataclass
class PreferValue:
    target: str

    def choose(self, *, left: str, right: str, seed: int) -> Side:
        del seed
        return Side.LEFT if left == self.target else Side.RIGHT


@dataclass
class PreferLexicographicallySmallest:
    def choose(self, *, left: str, right: str, seed: int) -> Side:
        del seed
        return Side.LEFT if left < right else Side.RIGHT


@dataclass
class ScriptedBackend:
    responses: list[Side | None]
    seen: list[tuple[str, str, int]] = field(default_factory=list)

    def choose(self, *, left: str, right: str, seed: int) -> Side | None:
        self.seen.append((left, right, seed))
        return self.responses[len(self.seen) - 1]


def test_pairwise_finds_preferred_candidate_despite_orientation_randomization() -> None:
    decision = PairwiseProtocol(PreferValue("d4"), best_of=7, seed=42).decide("d4", "e4")

    assert decision.winner == "d4"
    assert len(decision.bouts) == 7
    assert all(bout.selected == "d4" for bout in decision.bouts)
    assert {bout.selected_side for bout in decision.bouts} == {Side.LEFT, Side.RIGHT}


def test_pairwise_is_reproducible_for_same_seed() -> None:
    protocol_a = PairwiseProtocol(PreferValue("d4"), best_of=5, seed=123)
    protocol_b = PairwiseProtocol(PreferValue("d4"), best_of=5, seed=123)

    assert protocol_a.decide("d4", "e4") == protocol_b.decide("d4", "e4")


def test_pairwise_requires_positive_odd_best_of() -> None:
    with pytest.raises(ValueError):
        PairwiseProtocol(PreferValue("d4"), best_of=0)
    with pytest.raises(ValueError):
        PairwiseProtocol(PreferValue("d4"), best_of=4)


def test_pairwise_records_non_response_without_turning_it_into_a_vote() -> None:
    backend = ScriptedBackend([None, Side.LEFT, Side.LEFT, Side.LEFT])
    decision = PairwiseProtocol(backend, best_of=3, seed=7, max_bouts=4).decide("a", "b")

    assert len(decision.bouts) == 4
    assert decision.bouts[0].selected_side is None
    assert decision.bouts[0].selected is None
    assert sum(bout.selected is not None for bout in decision.bouts) == 3


def test_pairwise_bounds_repeated_non_responses() -> None:
    backend = ScriptedBackend([None, None, None, None])
    protocol = PairwiseProtocol(backend, best_of=3, seed=7, max_bouts=4)

    with pytest.raises(InsufficientDecisionsError) as error:
        protocol.decide("a", "b")

    assert len(error.value.bouts) == 4
    assert all(bout.selected is None for bout in error.value.bouts)


def test_pairwise_rejects_max_bouts_smaller_than_decisive_target() -> None:
    with pytest.raises(ValueError, match="max_bouts"):
        PairwiseProtocol(PreferValue("d4"), best_of=5, max_bouts=3)


def test_knockout_selects_one_candidate_and_preserves_bout_log() -> None:
    decision = KnockoutProtocol(
        PreferLexicographicallySmallest(),
        best_of=3,
        seed=9,
    ).decide(["e4", "d4", "g3", "c4"])

    assert decision.winner == "c4"
    assert len(decision.bouts) == 9


def test_knockout_single_candidate_needs_no_bouts() -> None:
    decision = KnockoutProtocol(PreferValue("d4"), seed=1).decide(["d4"])

    assert decision.winner == "d4"
    assert decision.bouts == ()
