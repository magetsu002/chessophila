from __future__ import annotations

from dataclasses import dataclass

from chessophila.choice import Side

from .shiu import ShiuTrialResult


@dataclass(frozen=True, slots=True)
class ReadoutResult:
    """Decoded physical-side evidence from one neural trial."""

    side: Side | None
    left_spikes: int
    right_spikes: int

    @property
    def total_spikes(self) -> int:
        return self.left_spikes + self.right_spikes

    @property
    def margin(self) -> int:
        return abs(self.left_spikes - self.right_spikes)


@dataclass(frozen=True, slots=True)
class CompetitiveSpikeReadout:
    """Decode two explicitly configured neural channels into left/right/no-response.

    This class makes no claim that a particular channel is a validated biological
    left/right motor readout. Channel identities are experiment configuration and must
    be justified independently. The decoder only compares recorded spike counts.
    """

    left_channel: tuple[int, ...]
    right_channel: tuple[int, ...]
    minimum_total_spikes: int = 1
    minimum_margin: int = 1

    def __post_init__(self) -> None:
        if not self.left_channel:
            raise ValueError("left_channel must contain at least one FlyWire ID")
        if not self.right_channel:
            raise ValueError("right_channel must contain at least one FlyWire ID")
        if len(set(self.left_channel)) != len(self.left_channel):
            raise ValueError("left_channel contains duplicate FlyWire IDs")
        if len(set(self.right_channel)) != len(self.right_channel):
            raise ValueError("right_channel contains duplicate FlyWire IDs")
        overlap = set(self.left_channel) & set(self.right_channel)
        if overlap:
            raise ValueError(f"left/right channels overlap: {sorted(overlap)}")
        if self.minimum_total_spikes < 1:
            raise ValueError("minimum_total_spikes must be at least 1")
        if self.minimum_margin < 1:
            raise ValueError("minimum_margin must be at least 1")

    def decode(self, trial: ShiuTrialResult) -> ReadoutResult:
        left_spikes = trial.spike_count(self.left_channel)
        right_spikes = trial.spike_count(self.right_channel)
        result = ReadoutResult(
            side=None,
            left_spikes=left_spikes,
            right_spikes=right_spikes,
        )

        if result.total_spikes < self.minimum_total_spikes:
            return result
        if result.margin < self.minimum_margin:
            return result

        side = Side.LEFT if left_spikes > right_spikes else Side.RIGHT
        return ReadoutResult(
            side=side,
            left_spikes=left_spikes,
            right_spikes=right_spikes,
        )
