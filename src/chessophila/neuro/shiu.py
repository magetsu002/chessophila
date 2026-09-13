from __future__ import annotations

import importlib.util
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from .provenance import verify_upstream


class SimulatorDependencyError(RuntimeError):
    pass


class UnknownFlyWireIdError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FlyWireIndex:
    flywire_to_index: dict[int, int]
    index_to_flywire: dict[int, int]

    @classmethod
    def from_ids(cls, flywire_ids: Sequence[int]) -> "FlyWireIndex":
        normalized = [int(value) for value in flywire_ids]
        if len(set(normalized)) != len(normalized):
            raise ValueError("FlyWire IDs must be unique")
        forward = {flywire_id: index for index, flywire_id in enumerate(normalized)}
        reverse = {index: flywire_id for flywire_id, index in forward.items()}
        return cls(flywire_to_index=forward, index_to_flywire=reverse)

    def indices(self, flywire_ids: Iterable[int]) -> list[int]:
        result: list[int] = []
        for raw_id in flywire_ids:
            flywire_id = int(raw_id)
            try:
                result.append(self.flywire_to_index[flywire_id])
            except KeyError as exc:
                raise UnknownFlyWireIdError(f"FlyWire ID not present in connectome: {flywire_id}") from exc
        return result


@dataclass(frozen=True, slots=True)
class ShiuTrialResult:
    seed: int
    spikes_by_flywire_id: dict[int, tuple[float, ...]]

    def spike_count(self, flywire_ids: Iterable[int]) -> int:
        return sum(len(self.spikes_by_flywire_id.get(int(flywire_id), ())) for flywire_id in flywire_ids)


class ShiuSimulator:
    """Thin adapter around the pinned Shiu et al. Brian2 model.

    The upstream source remains external and is verified before it is imported. This class
    only translates FlyWire IDs to the integer indices expected by upstream `run_trial`
    and translates spike trains back to FlyWire IDs.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        verify_upstream(self.root)
        self._model: ModuleType | None = None
        self._index: FlyWireIndex | None = None

    @property
    def completeness_path(self) -> Path:
        return self.root / "Completeness_783.csv"

    @property
    def connectivity_path(self) -> Path:
        return self.root / "Connectivity_783.parquet"

    def _load_model(self) -> ModuleType:
        if self._model is not None:
            return self._model

        model_path = self.root / "model.py"
        spec = importlib.util.spec_from_file_location("chessophila_upstream_shiu_model", model_path)
        if spec is None or spec.loader is None:
            raise SimulatorDependencyError(f"could not load upstream model from {model_path}")

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except ModuleNotFoundError as exc:
            raise SimulatorDependencyError(
                "the pinned simulator dependencies are not installed; create an environment "
                "from the upstream environment.yml before running neural trials"
            ) from exc
        self._model = module
        return module

    def _load_index(self) -> FlyWireIndex:
        if self._index is not None:
            return self._index

        try:
            import pandas as pd
        except ModuleNotFoundError as exc:
            raise SimulatorDependencyError(
                "pandas is required by the pinned simulator environment"
            ) from exc

        frame = pd.read_csv(self.completeness_path, index_col=0)
        self._index = FlyWireIndex.from_ids([int(value) for value in frame.index])
        return self._index

    @staticmethod
    def _seed_simulator(seed: int) -> None:
        try:
            import brian2
            import numpy as np
        except ModuleNotFoundError as exc:
            raise SimulatorDependencyError(
                "Brian2 and NumPy are required by the pinned simulator environment"
            ) from exc

        np.random.seed(seed & 0xFFFFFFFF)
        brian2.seed(seed)

    def run_trial(
        self,
        *,
        activated: Iterable[int],
        activated_secondary: Iterable[int] = (),
        silenced: Iterable[int] = (),
        seed: int,
        parameter_overrides: dict[str, Any] | None = None,
    ) -> ShiuTrialResult:
        model = self._load_model()
        index = self._load_index()
        self._seed_simulator(seed)

        params = dict(model.default_params)
        if parameter_overrides:
            params.update(parameter_overrides)

        spikes = model.run_trial(
            index.indices(activated),
            index.indices(activated_secondary),
            index.indices(silenced),
            self.completeness_path,
            self.connectivity_path,
            params,
        )

        translated: dict[int, tuple[float, ...]] = {}
        for raw_index, spike_times in spikes.items():
            brian_index = int(raw_index)
            try:
                flywire_id = index.index_to_flywire[brian_index]
            except KeyError as exc:
                raise RuntimeError(f"upstream emitted unknown Brian index: {brian_index}") from exc
            translated[flywire_id] = tuple(float(value) for value in spike_times)

        return ShiuTrialResult(seed=seed, spikes_by_flywire_id=translated)
