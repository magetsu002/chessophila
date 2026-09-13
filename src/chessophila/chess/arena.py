from __future__ import annotations

from dataclasses import dataclass

import chess


@dataclass(frozen=True, slots=True)
class ChessCandidate:
    """One legal move represented by the resulting board state.

    `uci` exists for logging and replay only. A neural backend should consume the
    resulting position/stimulus, not the move label itself.
    """

    uci: str
    resulting_fen: str


@dataclass(frozen=True, slots=True)
class ChessPosition:
    fen: str = chess.STARTING_FEN

    def board(self) -> chess.Board:
        return chess.Board(self.fen)

    def candidates(self) -> tuple[ChessCandidate, ...]:
        board = self.board()
        result: list[ChessCandidate] = []
        for move in board.legal_moves:
            next_board = board.copy(stack=False)
            next_board.push(move)
            result.append(ChessCandidate(uci=move.uci(), resulting_fen=next_board.fen()))
        return tuple(result)

    def apply(self, candidate: ChessCandidate) -> "ChessPosition":
        board = self.board()
        move = chess.Move.from_uci(candidate.uci)
        if move not in board.legal_moves:
            raise ValueError(f"illegal move for current position: {candidate.uci}")
        board.push(move)
        if board.fen() != candidate.resulting_fen:
            raise ValueError("candidate resulting_fen does not match the legal move")
        return ChessPosition(board.fen())
