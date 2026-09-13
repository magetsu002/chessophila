import chess
import pytest

from chessophila.chess import ChessCandidate, ChessPosition


def test_starting_position_exposes_exactly_all_legal_moves() -> None:
    position = ChessPosition()
    candidates = position.candidates()

    assert len(candidates) == 20
    assert {candidate.uci for candidate in candidates} == {
        move.uci() for move in chess.Board().legal_moves
    }


def test_candidate_contains_resulting_position_not_only_move_label() -> None:
    d4 = next(candidate for candidate in ChessPosition().candidates() if candidate.uci == "d2d4")
    resulting = chess.Board(d4.resulting_fen)

    assert resulting.piece_at(chess.D4) == chess.Piece(chess.PAWN, chess.WHITE)
    assert resulting.turn == chess.BLACK


def test_apply_rejects_tampered_resulting_fen() -> None:
    position = ChessPosition()
    candidate = ChessCandidate(uci="d2d4", resulting_fen=chess.STARTING_FEN)

    with pytest.raises(ValueError, match="resulting_fen"):
        position.apply(candidate)
