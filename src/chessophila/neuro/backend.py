from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from chessophila.choice import Side

from .readout import CompetitiveSpikeReadout, ReadoutResult
from .shiu import ShiuTrialResult


@dataclass(frozen=True, slots=True)
class ActivationStimulus:
    """One explicit optogenetic-style stimulus for the pinned Shiu simulator.

    Neuron IDs are FlyWire root IDs. The stimulus contains no chess move labels or
    engine scores; translating a chess state into these populations is a separate,
    versioned experimental assumption.
    """

    activated: tuple[int, ...]
    activated_secondary: tuple[int, ...] = ()
    silenced: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        groups = {
            "activated": self.activated,
            "activated_secondary": self.activated_secondary,
            "silenced": self.silenced,
        }
        for name, values in groups.items():
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate FlyWire IDs")

        primary = set(self.activated)
        secondary = set(self.activated_secondary)
        silenced = set(self.silenced)
        if primary & secondary:
            raise ValueError("a neuron cannot use both activation frequencies")
        if (primary | secondary) & silenced:
            raise ValueError("a neuron cannot be activated and silenced in one stimulus")


@dataclass(frozen=True, slots=True)
class CombinedStimulus:
    activated: tuple[int, ...]
    activated_secondary: tuple[int, ...]
    silenced: tuple[int, ...]


def _ordered_union(*groups: Iterable[int]) -> tuple[int, ...]:
    return tuple(dict.fromkeys(value for group in groups for value in group))


def combine_stimuli(left: ActivationStimulus, right: ActivationStimulus) -> CombinedStimulus:
    """Combine the two side-specific stimuli without inventing extra neural inputs."""

    activated = _ordered_union(left.activated, right.activated)
    activated_secondary = _ordered_union(
        left.activated_secondary,
        right.activated_secondary,
    )
    silenced = _ordered_union(left.silenced, right.silenced)

    primary = set(activated)
    secondary = set(activated_secondary)
    silenced_set = set(silenced)
    if primary & secondary:
        raise ValueError("combined stimuli assign a neuron to both activation frequencies")
    if (primary | secondary) & silenced_set:
        raise ValueError("combined stimuli activate and silence the same neuron")

    return CombinedStimulus(
        activated=activated,
        activated_secondary=activated_secondary,
        silenced=silenced,
    )


class ShiuTrialRunner(Protocol):
    def run_trial(
        self,
        *,
        activated: Iterable[int],
        activated_secondary: Iterable[int] = (),
        silenced: Iterable[int] = (),
        seed: int,
        parameter_overrides: dict[str, Any] | None = None,
    ) -> ShiuTrialResult:
        ...


@dataclass(frozen=True, slots=True)
class NeuralChoiceTrace:
    """Complete in-memory evidence for one decoded physical choice."""

    seed: int
    left: ActivationStimulus
    right: ActivationStimulus
    combined: CombinedStimulus
    trial: ShiuTrialResult
    readout: ReadoutResult


@dataclass(slots=True)
class ShiuChoiceBackend:
    """Run one verified neural trial and decode it as left/right/no-response."""

    simulator: ShiuTrialRunner
    readout: CompetitiveSpikeReadout
    parameter_overrides: dict[str, Any] | None = None
    on_trial: Callable[[NeuralChoiceTrace], None] | None = None

    def choose(
        self,
        *,
        left: ActivationStimulus,
        right: ActivationStimulus,
        seed: int,
    ) -> Side | None:
        combined = combine_stimuli(left, right)
        trial = self.simulator.run_trial(
            activated=combined.activated,
            activated_secondary=combined.activated_secondary,
            silenced=combined.silenced,
            seed=seed,
            parameter_overrides=self.parameter_overrides,
        )
        readout = self.readout.decode(trial)

        if self.on_trial is not None:
            self.on_trial(
                NeuralChoiceTrace(
                    seed=seed,
                    left=left,
                    right=right,
                    combined=combined,
                    trial=trial,
                    readout=readout,
                )
            )

        return readout.side
