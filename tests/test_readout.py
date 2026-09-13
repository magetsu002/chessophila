import pytest

from chessophila.choice import Side
from chessophila.neuro import CompetitiveSpikeReadout, ShiuTrialResult


def trial(**spikes: tuple[float, ...]) -> ShiuTrialResult:
    return ShiuTrialResult(
        seed=42,
        spikes_by_flywire_id={int(neuron): times for neuron, times in spikes.items()},
    )


def test_left_channel_wins_from_recorded_spike_counts() -> None:
    readout = CompetitiveSpikeReadout(left_channel=(101,), right_channel=(202,))

    result = readout.decode(trial(**{"101": (0.1, 0.2, 0.3), "202": (0.1,)}))

    assert result.side is Side.LEFT
    assert result.left_spikes == 3
    assert result.right_spikes == 1
    assert result.total_spikes == 4
    assert result.margin == 2


def test_right_channel_wins_from_recorded_spike_counts() -> None:
    readout = CompetitiveSpikeReadout(left_channel=(101,), right_channel=(202,))

    result = readout.decode(trial(**{"101": (0.1,), "202": (0.1, 0.2)}))

    assert result.side is Side.RIGHT


def test_tie_is_an_explicit_non_response() -> None:
    readout = CompetitiveSpikeReadout(left_channel=(101,), right_channel=(202,))

    result = readout.decode(trial(**{"101": (0.1,), "202": (0.2,)}))

    assert result.side is None
    assert result.margin == 0


def test_minimum_total_activity_can_reject_weak_signal() -> None:
    readout = CompetitiveSpikeReadout(
        left_channel=(101,),
        right_channel=(202,),
        minimum_total_spikes=4,
    )

    result = readout.decode(trial(**{"101": (0.1, 0.2), "202": (0.1,)}))

    assert result.side is None
    assert result.total_spikes == 3


def test_minimum_margin_can_reject_ambiguous_signal() -> None:
    readout = CompetitiveSpikeReadout(
        left_channel=(101,),
        right_channel=(202,),
        minimum_margin=3,
    )

    result = readout.decode(trial(**{"101": (0.1, 0.2, 0.3), "202": (0.1,)}))

    assert result.side is None
    assert result.margin == 2


@pytest.mark.parametrize(
    ("left", "right", "message"),
    [
        ((), (202,), "left_channel"),
        ((101,), (), "right_channel"),
        ((101, 101), (202,), "duplicate"),
        ((101,), (202, 202), "duplicate"),
        ((101, 202), (202, 303), "overlap"),
    ],
)
def test_readout_rejects_invalid_channels(
    left: tuple[int, ...],
    right: tuple[int, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CompetitiveSpikeReadout(left_channel=left, right_channel=right)


@pytest.mark.parametrize(
    ("minimum_total_spikes", "minimum_margin"),
    [(0, 1), (1, 0), (-1, 1), (1, -1)],
)
def test_readout_rejects_invalid_thresholds(
    minimum_total_spikes: int,
    minimum_margin: int,
) -> None:
    with pytest.raises(ValueError):
        CompetitiveSpikeReadout(
            left_channel=(101,),
            right_channel=(202,),
            minimum_total_spikes=minimum_total_spikes,
            minimum_margin=minimum_margin,
        )
