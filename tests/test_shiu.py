import pytest

from chessophila.neuro import FlyWireIndex, ShiuTrialResult, UnknownFlyWireIdError


def test_flywire_index_round_trip() -> None:
    index = FlyWireIndex.from_ids([101, 202, 303])

    assert index.indices([303, 101]) == [2, 0]
    assert index.index_to_flywire == {0: 101, 1: 202, 2: 303}


def test_flywire_index_rejects_duplicate_ids() -> None:
    with pytest.raises(ValueError, match="unique"):
        FlyWireIndex.from_ids([101, 101])


def test_flywire_index_rejects_unknown_id() -> None:
    index = FlyWireIndex.from_ids([101, 202])

    with pytest.raises(UnknownFlyWireIdError, match="999"):
        index.indices([999])


def test_trial_result_counts_only_requested_neurons() -> None:
    result = ShiuTrialResult(
        seed=7,
        spikes_by_flywire_id={
            101: (0.1, 0.2),
            202: (0.4,),
        },
    )

    assert result.spike_count([101]) == 2
    assert result.spike_count([101, 202]) == 3
    assert result.spike_count([999]) == 0
