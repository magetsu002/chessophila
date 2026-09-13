import chess

from chessophila.choice import Side
from chessophila.neuro.visual import load_visual_feature_map


def test_visual_map_covers_complete_chess_state_features() -> None:
    mapping = load_visual_feature_map()
    assert mapping.flywire_materialization == 783
    assert len(mapping.features) == 838
    assert mapping.dna02_left != mapping.dna02_right


def test_same_position_uses_bilateral_matched_channels() -> None:
    mapping = load_visual_feature_map()
    fen = chess.Board().fen()
    left = mapping.encode_fen(fen, side=Side.LEFT)
    right = mapping.encode_fen(fen, side=Side.RIGHT)

    assert len(left.activated) == len(right.activated) == 37
    assert set(left.activated).isdisjoint(right.activated)

    expected_pairs = {
        (channel.left, channel.right)
        for channel in mapping.features.values()
    }
    assert all(pair in expected_pairs for pair in zip(left.activated, right.activated, strict=True))


def test_position_change_changes_visual_pattern() -> None:
    mapping = load_visual_feature_map()
    board = chess.Board()
    before = mapping.encode_fen(board.fen(), side=Side.LEFT)
    board.push_uci("e2e4")
    after = mapping.encode_fen(board.fen(), side=Side.LEFT)
    assert before.activated != after.activated


def test_dna02_readout_is_bilateral() -> None:
    mapping = load_visual_feature_map()
    readout = mapping.steering_readout()
    assert readout.left_channel == (720575940629327659,)
    assert readout.right_channel == (720575940604737708,)


def test_visual_chess_backend_hides_move_labels_from_neural_backend() -> None:
    from dataclasses import dataclass, field

    from chessophila.chess import ChessCandidate
    from chessophila.neuro.visual import VisualChessChoiceBackend

    @dataclass
    class FakeNeural:
        calls: list[tuple[object, object, int]] = field(default_factory=list)

        def choose(self, *, left: object, right: object, seed: int) -> Side:
            self.calls.append((left, right, seed))
            return Side.RIGHT

    mapping = load_visual_feature_map()
    board = chess.Board()
    candidates = {}
    for move in board.legal_moves:
        next_board = board.copy(stack=False)
        next_board.push(move)
        candidates[move.uci()] = ChessCandidate(move.uci(), next_board.fen())

    fake = FakeNeural()
    backend = VisualChessChoiceBackend(fake, mapping)  # type: ignore[arg-type]
    side = backend.choose(left=candidates["e2e4"], right=candidates["d2d4"], seed=9)
    assert side is Side.RIGHT
    left_stimulus, right_stimulus, seed = fake.calls[0]
    assert seed == 9
    assert len(left_stimulus.activated) == len(right_stimulus.activated) == 37
