from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

import chess

from chessophila.chess import ChessCandidate
from chessophila.choice import Side

from .backend import ActivationStimulus, ShiuChoiceBackend
from .readout import CompetitiveSpikeReadout


@dataclass(frozen=True, slots=True)
class BilateralFeatureChannel:
    cell_type: str
    left: int
    right: int

    def neuron_for(self, side: Side) -> int:
        return self.left if side is Side.LEFT else self.right


@dataclass(frozen=True, slots=True)
class VisualFeatureMap:
    flywire_materialization: int
    annotation_commit: str
    features: dict[str, BilateralFeatureChannel]
    dna02_left: int
    dna02_right: int

    def encode_fen(self, fen: str, *, side: Side) -> ActivationStimulus:
        board = chess.Board(fen)
        names: list[str] = []
        for square, piece in sorted(board.piece_map().items()):
            names.append(f"{piece.symbol()}@{square}")
        names.append("turn:white" if board.turn == chess.WHITE else "turn:black")
        if board.has_kingside_castling_rights(chess.WHITE):
            names.append("castle:K")
        if board.has_queenside_castling_rights(chess.WHITE):
            names.append("castle:Q")
        if board.has_kingside_castling_rights(chess.BLACK):
            names.append("castle:k")
        if board.has_queenside_castling_rights(chess.BLACK):
            names.append("castle:q")
        if board.ep_square is not None:
            names.append(f"ep:{board.ep_square}")

        neurons = tuple(self.features[name].neuron_for(side) for name in names)
        return ActivationStimulus(activated=neurons)

    def steering_readout(
        self,
        *,
        minimum_total_spikes: int = 1,
        minimum_margin: int = 1,
    ) -> CompetitiveSpikeReadout:
        return CompetitiveSpikeReadout(
            left_channel=(self.dna02_left,),
            right_channel=(self.dna02_right,),
            minimum_total_spikes=minimum_total_spikes,
            minimum_margin=minimum_margin,
        )


def load_visual_feature_map() -> VisualFeatureMap:
    resource = files("chessophila.neuro").joinpath("visual_feature_map_v783.json")
    raw = json.loads(resource.read_text(encoding="utf-8"))
    features = {
        name: BilateralFeatureChannel(**channel)
        for name, channel in raw["features"].items()
    }
    return VisualFeatureMap(
        flywire_materialization=int(raw["flywire_materialization"]),
        annotation_commit=str(raw["annotation_commit"]),
        features=features,
        dna02_left=int(raw["dNa02"]["left"]),
        dna02_right=int(raw["dNa02"]["right"]),
    )


@dataclass(slots=True)
class VisualChessChoiceBackend:
    """Translate legal resulting positions into bilateral visual neural stimuli."""

    neural_backend: ShiuChoiceBackend
    feature_map: VisualFeatureMap

    def choose(
        self,
        *,
        left: ChessCandidate,
        right: ChessCandidate,
        seed: int,
    ) -> Side | None:
        left_stimulus = self.feature_map.encode_fen(left.resulting_fen, side=Side.LEFT)
        right_stimulus = self.feature_map.encode_fen(right.resulting_fen, side=Side.RIGHT)
        return self.neural_backend.choose(
            left=left_stimulus,
            right=right_stimulus,
            seed=seed,
        )
