import math

import chess


def make_move(board: chess.Board, depth: int):
    """Does the best possible move for the AI"""
    move = get_move(board, depth)
    board.move(move.piece, move.end)


def get_move(board: chess.Board, depth: int):
    """Returns the best move for the AI"""
    zobristTable = {}

    def minimax(color: bool, depth: int, alpha: float = -math.inf, beta: float = math.inf):
        zobristKey = board.get_zobrist_key()
        if zobristTable.get(zobristKey) != None:
            return zobristTable[zobristKey], board.lastMove

        if depth == 0 or board.result != None:
            return evaluate(board), board.lastMove

        if color == True:
            maxEvaluation = -math.inf
        else:
            maxEvaluation = math.inf

        bestMove = None
        previousMove = board.lastMove
        # Loop through all the possible moves
        for piece, positions in board.get_valid_moves(color).items():
            for position in positions:
                move = board.move(piece, position)
                evaluation = minimax(not color, depth - 1, alpha, beta)[0]
                board.revert(move, previousMove)

                zobristTable[zobristKey] = evaluation

                # White
                if color == True:
                    if evaluation > maxEvaluation:
                        maxEvaluation = evaluation
                        bestMove = move
                    alpha = max(alpha, maxEvaluation)
                    if alpha >= beta:
                        break
                # Black
                else:
                    if evaluation < maxEvaluation:
                        maxEvaluation = evaluation
                        bestMove = move
                    beta = min(beta, maxEvaluation)
                    if beta <= alpha:
                        break
        return maxEvaluation, bestMove

    if not board.lastMove:
        color = True
    else:
        color = not board.lastMove.piece.color

    # Returns the best found move
    return minimax(color, depth)[1]


def evaluate(board: chess.Board) -> float:
    """Returns the evaluation of the board for the AI"""
    # The game is allready over
    if board.result != None:
        # White wins
        if board.result == 0:
            return 104
        # Black wins
        elif board.result == 1:
            return -104
        # Draw
        else:
            return 0
    # The game is still going
    else:
        # We sum up all the points of the pieces on the board
        evaluation = 0
        for piece in board.get_pieces():
            # White pieces are positive
            if piece.color:
                evaluation += piece.points
            # Black pieces are negative
            else:
                evaluation -= piece.points
        return evaluation
