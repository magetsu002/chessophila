from dataclasses import dataclass, field
from typing import Any

import pytest

from chessophila.choice import Side
from chessophila.neuro import (
    ActivationStimulus,
    CompetitiveSpikeReadout,
    NeuralChoiceTrace,
    ShiuChoiceBackend,
    ShiuTrialResult,
    combine_stimuli,
)


@dataclass
class FakeSimulator:
    result: ShiuTrialResult
    calls: list[dict[str, Any]] = field(default_factory=list)

    def run_trial(
        self,
        *,
        activated: tuple[int, ...],
        activated_secondary: tuple[int, ...] = (),
        silenced: tuple[int, ...] = (),
        seed: int,
        parameter_overrides: dict[str, Any] | None = None,
    ) -> ShiuTrialResult:
        self.calls.append(
            {
                "activated": tuple(activated),
                "activated_secondary": tuple(activated_secondary),
                "silenced": tuple(silenced),
                "seed": seed,
                "parameter_overrides": parameter_overrides,
            }
        )
        return self.result


def test_stimulus_rejects_contradictory_neuron_assignments() -> None:
    with pytest.raises(ValueError, match="both activation frequencies"):
        ActivationStimulus(activated=(1,), activated_secondary=(1,))

    with pytest.raises(ValueError, match="activated and silenced"):
        ActivationStimulus(activated=(1,), silenced=(1,))


def test_combining_stimuli_is_ordered_and_deduplicated() -> None:
    left = ActivationStimulus(activated=(1, 2), silenced=(8,))
    right = ActivationStimulus(activated=(2, 3), silenced=(9,))

    combined = combine_stimuli(left, right)

    assert combined.activated == (1, 2, 3)
    assert combined.silenced == (8, 9)


def test_combining_stimuli_rejects_cross_side_frequency_conflict() -> None:
    left = ActivationStimulus(activated=(1,))
    right = ActivationStimulus(activated_secondary=(1,))

    with pytest.raises(ValueError, match="both activation frequencies"):
        combine_stimuli(left, right)


def test_backend_runs_combined_trial_and_decodes_physical_side() -> None:
    simulator = FakeSimulator(
        ShiuTrialResult(
            seed=77,
            spikes_by_flywire_id={101: (0.1, 0.2, 0.3), 202: (0.1,)},
        )
    )
    traces: list[NeuralChoiceTrace] = []
    backend = ShiuChoiceBackend(
        simulator=simulator,
        readout=CompetitiveSpikeReadout(left_channel=(101,), right_channel=(202,)),
        parameter_overrides={"example": 1},
        on_trial=traces.append,
    )

    side = backend.choose(
        left=ActivationStimulus(activated=(11,), silenced=(31,)),
        right=ActivationStimulus(activated=(12,), silenced=(32,)),
        seed=77,
    )

    assert side is Side.LEFT
    assert simulator.calls == [
        {
            "activated": (11, 12),
            "activated_secondary": (),
            "silenced": (31, 32),
            "seed": 77,
            "parameter_overrides": {"example": 1},
        }
    ]
    assert len(traces) == 1
    assert traces[0].readout.side is Side.LEFT
    assert traces[0].readout.left_spikes == 3


def test_backend_preserves_ambiguous_neural_output_as_non_response() -> None:
    simulator = FakeSimulator(
        ShiuTrialResult(
            seed=88,
            spikes_by_flywire_id={101: (0.1,), 202: (0.1,)},
        )
    )
    backend = ShiuChoiceBackend(
        simulator=simulator,
        readout=CompetitiveSpikeReadout(left_channel=(101,), right_channel=(202,)),
    )

    side = backend.choose(
        left=ActivationStimulus(activated=(11,)),
        right=ActivationStimulus(activated=(12,)),
        seed=88,
    )

    assert side is None
