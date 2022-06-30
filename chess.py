from typing import List, Tuple, Union

import pygame
from PIL import Image


class Position:
    def __init__(self, column: int, rank: int = None) -> None:
        if isinstance(column, tuple):
            self.column = column[0]
            self.rank = column[1]
        else:
            self.column = column
            self.rank = rank

    def __eq__(self, other):
        return (self.column, self.rank) == other


class Board:
    def __init__(self, pieces: List) -> None:
        self.board = [[None for rank in range(8)] for column in range(8)]
        self.lastMove = None

        for piece in pieces:
            self.set_piece(piece)

    def get_piece(self, position: Union[Position, Tuple[int, int]]):
        if not isinstance(position, Position):
            position = Position(*position)
        return self.board[position.column][position.rank]

    def set_piece(self, piece):
        self.board[piece.position.column][piece.position.rank] = piece

    def clear_square(self, position: Position):
        self.board[position.column][position.rank] = None

    def move_piece(self, piece, position: Position):
        validMove = piece.is_valid_move(self, position)
        # Only moves the piece if the move is valid
        if validMove:
            # Sets last move to the current one
            self.lastMove = Move(piece, piece.position)

            # Moves the piece to the new position and clears the old one
            self.clear_square(piece.position)
            piece.position = position
            self.set_piece(piece)

            # Sets the hasMoved property of the piece to True for king and rooks
            if isinstance(piece, Rook) or isinstance(piece, King):
                piece.hasMoved = True

            # Enpassant move
            if validMove == 2:
                if piece.color == True:
                    self.clear_square(Position(piece.position.column, piece.position.rank + 1))
                else:
                    self.clear_square(Position(piece.position.column, piece.position.rank - 1))

            # Castling move
            if validMove == 3:
                # Queen side castling
                if piece.position.column == 2:
                    rook = self.get_piece((0, piece.position.rank))
                    self.clear_square(rook.position)
                    rook.position.column = 3
                    self.set_piece(rook)
                # King side castling
                else:
                    rook = self.get_piece((7, piece.position.rank))
                    self.clear_square(rook.position)
                    rook.position.column = 5
                    self.set_piece(rook)


class Piece:
    def __init__(self, position: Union[Position, Tuple[int, int]], color: bool):
        if isinstance(position, Position):
            self.position = position
        else:
            self.position = Position(*position)
        self.color = color

    def color_to_play(self, board: Board) -> bool:
        # Only allows the right color to play -> white at start and then changing
        if not board.lastMove or board.lastMove.piece.color == False:
            if self.color == True:
                return True
        elif self.color == False:
            return True

    def capturing(self, board: Board, move: Position) -> bool:
        # Colors can only capture enemey colored pieces not their own
        if not board.get_piece(move) or board.get_piece(move).color != self.color:
            return True
        else:
            return False

    def generally_valid_move(self, board: Board, move: Position) -> bool:
        # Checks for some basic conditions that all pieces have in common for a valid move
        if self.color_to_play(board) and self.capturing(board, move):
            return True

    def transform_to(self, pieceType):
        return pieceType(self.position, self.color)


class Move:
    def __init__(self, piece: Piece, start: Position):
        self.piece = piece
        self.start = start


class Pawn(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # Moving just forward without capturing
        elif self.position.column == move.column:
            if not board.get_piece(move):
                if self.color == True:
                    if self.position.rank == move.rank + 1:
                        return True
                    # Starting position can move two squares
                    elif self.position.rank == 6 and self.position.rank == move.rank + 2:
                        if not board.get_piece((move.column, move.rank + 1)):
                            return True
                else:
                    if self.position.rank == move.rank - 1:
                        return True
                    # Starting position can move two squares
                    elif self.position.rank == 1 and self.position.rank == move.rank - 2:
                        if not board.get_piece((move.column, move.rank - 1)):
                            return True
        # Capturing a piece
        elif self.position.column == move.column + 1 or self.position.column == move.column - 1:
            # Regular capture case
            if board.get_piece(move) and board.get_piece(move).color != self.color:
                if self.color == True:
                    if self.position.rank == move.rank + 1:
                        return True
                else:
                    if self.position.rank == move.rank - 1:
                        return True
            # Enpassant capture case
            elif board.lastMove and board.lastMove.piece.position.column == move.column:
                if isinstance(board.lastMove.piece, Pawn):
                    if self.color == 1:
                        if self.position.rank == 3 and move.rank == 2:
                            if board.lastMove.start.rank == 1 and board.lastMove.piece.position.rank == 3:
                                return 2
                    else:
                        if self.position.rank == 4 and move.rank == 5:
                            if board.lastMove.start.rank == 6 and board.lastMove.piece.position.rank == 4:
                                return 2


class Rook(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.hasMoved = False

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # On both cases of movement we are looking if we are not jumping over some pieces

        # Moving vertically
        elif self.position.column == move.column:
            if self.position.rank > move.rank:
                for rank in range(move.rank + 1, self.position.rank):
                    if board.get_piece((move.column, rank)):
                        return False
            else:
                for rank in range(self.position.rank + 1, move.rank):
                    if board.get_piece((move.column, rank)):
                        return False
            return True
        # Moving horizontally
        elif self.position.rank == move.rank:
            if self.position.column > move.column:
                for column in range(move.column + 1, self.position.column):
                    if board.get_piece((column, move.rank)):
                        return False
            else:
                for column in range(self.position.column + 1, move.column):
                    if board.get_piece((column, move.rank)):
                        return False
            return True


class Knight(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # Moving in a L shape
        elif abs(self.position.column - move.column) == 2 and abs(self.position.rank - move.rank) == 1:
            return True
        elif abs(self.position.column - move.column) == 1 and abs(self.position.rank - move.rank) == 2:
            return True


class Bishop(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # Bishop can only move diagonally
        if abs(self.position.column - move.column) == abs(self.position.rank - move.rank):
            for i in range(1, abs(self.position.column - move.column)):
                # Checking the tiles for all four diagonals
                if self.position.column > move.column:
                    if self.position.rank > move.rank:
                        if board.get_piece((self.position.column - i, self.position.rank - i)):
                            return False
                    else:
                        if board.get_piece((self.position.column - i, self.position.rank + i)):
                            return False
                else:
                    if self.position.rank > move.rank:
                        if board.get_piece((self.position.column + i, self.position.rank - i)):
                            return False
                    else:
                        if board.get_piece((self.position.column + i, self.position.rank + i)):
                            return False
            return True


class Queen(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # Queen can move in any direction
        # We can inherit the Rook and Bishop classes to make this easier
        if self.transform_to(Rook).is_valid_move(board, move) or self.transform_to(Bishop).is_valid_move(board, move):
            return True


class King(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.hasMoved = False

    def is_valid_move(self, board: Board, move: Position) -> bool:
        if not super().generally_valid_move(board, move):
            return False
        # King can move in any direction but only one square
        if abs(self.position.column - move.column) in (0, 1) and abs(self.position.rank - move.rank) in (0, 1):
            return True

        # Castling
        if self.hasMoved == False:
            # Can only castle to these tiles
            if move.column == 2 or move.column == 6:
                # Gets the rank depending on the color
                if self.color == False:
                    rank = 0
                else:
                    rank = 7

                # Gets the rook and inbetween pieces
                # Queen side castle
                if move.column == 2:
                    rook = board.get_piece((0, rank))
                    inbetweenPieces = (
                        board.get_piece((1, rank)),
                        board.get_piece((2, rank)),
                        board.get_piece((3, rank)),
                    )
                # King side castle
                else:
                    rook = board.get_piece((7, rank))
                    inbetweenPieces = (board.get_piece((5, rank)), board.get_piece((6, rank)))

                # Checks if the rook hasn't moved yet and if there are no pieces inbetween
                if rook and isinstance(rook, Rook) and rook.hasMoved == False:
                    if all(not square for square in inbetweenPieces):
                        return 3


def assign_images(tile_size: int):
    """Assings images to the pieces"""

    def get_piece_from_image(image, area, size):
        croppedImage = image.crop((area))
        bytesImage = croppedImage.tobytes("raw", "RGBA")
        pygameImage = pygame.image.fromstring(bytesImage, size, "RGBA")
        return pygame.transform.scale(pygameImage, (tile_size, tile_size))

    with Image.open(r"assets\pieces.png") as pieces:
        Pawn.whiteImg = get_piece_from_image(pieces, (426 * 5 + 5, 0, 426 * 6 + 5, 426), (426, 426))
        Pawn.blackImg = get_piece_from_image(pieces, (426 * 5 + 5, 427, 426 * 6 + 5, 426 * 2 + 1), (426, 426))

        Rook.whiteImg = get_piece_from_image(pieces, (426 * 4 + 4, 0, 426 * 5 + 4, 426), (426, 426))
        Rook.blackImg = get_piece_from_image(pieces, (426 * 4 + 4, 427, 426 * 5 + 4, 426 * 2 + 1), (426, 426))

        Bishop.whiteImg = get_piece_from_image(pieces, (426 * 2 + 2, 0, 426 * 3 + 2, 426), (426, 426))
        Bishop.blackImg = get_piece_from_image(pieces, (426 * 2 + 2, 427, 426 * 3 + 2, 426 * 2 + 1), (426, 426))

        Knight.whiteImg = get_piece_from_image(pieces, (426 * 3 + 3, 0, 426 * 4 + 3, 426), (426, 426))
        Knight.blackImg = get_piece_from_image(pieces, (426 * 3 + 3, 427, 426 * 4 + 3, 426 * 2 + 1), (426, 426))

        Queen.whiteImg = get_piece_from_image(pieces, (426 + 1, 0, 426 * 2 + 1, 426), (426, 426))
        Queen.blackImg = get_piece_from_image(pieces, (426 + 1, 427, 426 * 2 + 1, 426 * 2 + 1), (426, 426))

        King.whiteImg = get_piece_from_image(pieces, (426 * 0 + 0, 0, 426 * 1 + 0, 426), (426, 426))
        King.blackImg = get_piece_from_image(pieces, (426 * 0 + 0, 427, 426 * 1 + 0, 426 * 2 + 1), (426, 426))
