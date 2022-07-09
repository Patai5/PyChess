import copy
import random
from typing import Union

import pygame
from PIL import Image


class Position:
    def __init__(self, column: Union[int, tuple[int, int]], rank: int = None) -> None:
        """Position: column, rank | (column, rank)"""
        if isinstance(column, tuple):
            self.column = column[0]
            self.rank = column[1]
        else:
            self.column = column
            self.rank = rank

    def __eq__(self, other):
        return (self.column, self.rank) == other

    def __iter__(self):
        yield self.column
        yield self.rank

    def __hash__(self):
        return hash(tuple(self))

    def is_in_bounds(self) -> bool:
        """Returns a bool value representing if the position is a valid square on a chessboard"""
        if 7 >= self.column >= 0 and 7 >= self.rank >= 0:
            return True
        else:
            return False


class Board:
    def __init__(self, pieces: list) -> None:
        self.board = [None] * 64
        self.lastMove = None
        self.promotion = None
        self.result = None
        self.pieces = []
        self.attackedSquares = []
        self.attackedSquares = []
        self.counterChecks = []
        self.pinnedLines = []
        self.pinnedSquares = []
        self.underCheck = False

        for piece in pieces:
            self.add_piece(piece)
            # Saves the kings for easier access
            if isinstance(piece, King):
                if piece.color == True:
                    self.whiteKing = piece
                else:
                    self.blackKing = piece

        zobrist_init()

    def get_zobrist_key(self) -> int:
        """Returns the zobrist key of the board"""
        if self.lastMove:
            key = self.lastMove.piece.color
        else:
            key = 1
        for piece in self.pieces:
            key ^= piece.get_zobrist_key()
        return key

    def get_piece(self, position: Union[Position, tuple[int, int]]):
        """Returns a piece at the given position"""
        if not isinstance(position, Position):
            position = Position(*position)
        return self.board[position.column + position.rank * 8]

    def get_pieces(self, color: bool = None) -> list:
        """Returns all pieces. If color is given, only returns pieces of that color"""
        if color is None:
            return self.pieces
        else:
            return list(filter(lambda piece: True if piece.color == color else False, self.pieces))

    def remove_piece(self, piece):
        """Removes a piece from the board"""
        self.pieces.remove(piece)
        self.clear_square(piece.position)

    def add_piece(self, piece):
        """Adds a piece to the board"""
        self.pieces.append(piece)
        self.set_piece(piece)

    def set_piece(self, piece, position: Position = None):
        """Sets a piece at it's position"""
        # Uses the position of the piece by default. If specified, uses the given position
        if position:
            piece.position = position
        self.board[piece.position.column + piece.position.rank * 8] = piece

    def clear_square(self, position: Position):
        """Clears a square at the given position"""
        self.board[position.column + position.rank * 8] = None

    def move_piece(self, piece, position: Union[Position, tuple[int, int]], tryMove: bool = False):
        """Moves a piece to the given position\n
        piece: Piece | Position | Tuple[int, int]
        position: Position | Tuple[int, int]
        - "tryMove" argument is used for checking purposes -> "lastMove" and "hasMove" are not stored"""
        # Gets the arguments in the correct format
        if not isinstance(piece, Piece):
            piece = self.get_piece(piece)
        if not isinstance(position, Position):
            position = Position(*position)

        if not tryMove:
            # Sets the last move as the move currently made
            self.lastMove = Move(piece.position, position, piece)

        # Moves the piece
        self.clear_square(piece.position)
        self.set_piece(piece, position)

        if not tryMove:
            # For rooks and king sets their hasMoved property
            if isinstance(piece, (King, Rook)) and not piece.hasMoved:
                piece.hasMoved = True

    def get_attacked_squares(self, color: bool) -> list:
        """Returns a list of all squares that are attacked by the given color + counter checks and pinned lines"""
        # Loops through the enemy pieces and adds their attacking squares to the list
        global timer

        attackedSquares = []
        counterChecks = []
        pinnedLines = []
        for piece in self.get_pieces(color):
            moves = piece.get_valid_moves(self, includeDefense=True)
            attackedSquares += moves[0]
            if moves[1]:
                counterChecks += moves[1]
            pinnedLines += moves[2]

        return set(attackedSquares), counterChecks, pinnedLines

    def move(self, piece, position: Position):
        """Moves a piece to the given position. Returns a Move object with the move details"""
        move = Move(piece.position, position, piece, self.get_piece(position))

        # Enpassant move
        if self.is_enpassant(piece, position):
            capturedPiece = self.enpassant(piece, position)
            move.enpassant = True
            move.capturedPiece = capturedPiece
        # Castling move
        elif self.is_castling(piece, position):
            self.castle(piece, position)
            move.castling = True
        # Promotion
        elif self.is_promotion(piece, position):
            self.move_piece(piece, position)
            self.promotion = piece
            move.promotion = True
        # Normal move
        else:
            # Capturing a piece
            if self.get_piece(position):
                move.capturedPiece = self.get_piece(position)
                self.remove_piece(move.capturedPiece)

            # Moving the piece
            self.move_piece(piece, position)

        # Updates the attacked squares, counter checks and pinned lines
        self.attackedSquares, self.counterChecks, self.pinnedLines = self.get_attacked_squares(piece.color)
        self.pinnedSquares = set([square for line in self.pinnedLines for square in line])
        # Updates the king check
        self.underCheck = self.get_king(not piece.color).is_under_check(self)
        # Checks for checkmate or stalemate
        self.round_check()

        return move

    def revert(self, move, previousLastMove):
        """Reverts the board to the previous state"""
        # Reverts ended game back
        self.result = None

        # Reverts promoted pawns back to their pawn state
        if move.promotion:
            move.piece = move.piece.transform_to(Pawn)
        # If there was castling, revert the rook
        if move.castling:
            # Queenside
            if move.castling == 1:
                rook = self.get_piece(((3, move.piece.position.rank)))
                self.move_piece(rook, ((0, move.piece.position.rank)))
            # Kingside
            else:
                rook = self.get_piece(((5, move.piece.position.rank)))
                self.move_piece(rook, ((7, move.piece.position.rank)))
            rook.hasMoved = False

        # Puts the piece back to its original position
        self.move_piece(move.piece, move.start)

        # If there was a capture on the move, put the captured piece back
        if move.capturedPiece:
            self.add_piece(move.capturedPiece)

        # Reverts the hasMoved property of the king and the rook back
        if isinstance(move.piece, (Rook, King)):
            move.piece.hasMoved = move.originalHasMoved

        # Sets the previous last move
        self.lastMove = previousLastMove

    def round_check(self):
        """Checks for checkmate or stalemate"""
        whitePieces = self.get_pieces(True)
        blackPieces = self.get_pieces(False)

        # Checks if the other party has any valid moves
        color = not self.lastMove.piece.color
        if not self.get_valid_moves(color):
            if self.get_king(color).is_under_check(self):
                if color:
                    self.end_game(blackWins=True)
                else:
                    self.end_game(whiteWins=True)
            else:
                self.end_game(stalemate=True)
        elif len(whitePieces) <= 2 and len(blackPieces) <= 2:
            whitePiecesDict = piece_count(whitePieces)
            blackPiecesDict = piece_count(blackPieces)

            # King vs King
            if len(whitePieces) == 1 and len(blackPieces) == 1:
                self.end_game(stalemate=True)
            # King + Bishop(same diagonal) vs King + Bishop(same diagonal)
            if len(whitePieces) == 2 and len(blackPieces) == 2:
                if whitePiecesDict.get(Bishop) == 1 and blackPiecesDict.get(Bishop):
                    bishop1, bishop2 = filter(
                        lambda piece: True if isinstance(piece, Bishop) else False, whitePieces + blackPieces
                    )
                    if bishop1.diagonal == bishop2.diagonal:
                        self.end_game(stalemate=True)
            # King vs King + Knight or Bishop
            whiteList = [whitePieces, whitePiecesDict]
            blackList = [blackPieces, blackPiecesDict]
            for color1, color2 in [[whiteList, blackList], [blackList, whiteList]]:
                if len(color1[0]) == 1:
                    if len(color2[0]) == 2:
                        if color2[1].get(Bishop) == 1 or color2[1].get(Knight) == 1:
                            self.end_game(stalemate=True)

    def end_game(self, whiteWins: bool = False, blackWins: bool = False, stalemate: bool = False):
        """Sets the the board atributes coresponding to the game result"""
        if whiteWins:
            self.result = 0
        elif blackWins:
            self.result = 1
        elif stalemate:
            self.result = 2

    def is_enpassant(self, piece, position: Position) -> bool:
        """Returns true if the move is an enpassant move"""
        if isinstance(piece, Pawn):
            if piece.position.column != position.column:
                if not self.get_piece(position):
                    return True
        return False

    def enpassant(self, piece, position: Position):
        """Does the enpassant move. Returns the captured piece"""
        self.move_piece(piece, position)
        # Clears the enpassanted pawn
        if piece.color == True:
            position = Position(piece.position.column, piece.position.rank + 1)
        else:
            position = Position(piece.position.column, piece.position.rank - 1)
        capturedPiece = self.get_piece(position)

        return capturedPiece

    def is_castling(self, piece, position: Position) -> bool:
        """Returns true if the move is a castling move"""
        if isinstance(piece, King) and not piece.hasMoved:
            if position.column == 2 or position.column == 6:
                return True
        return False

    def castle(self, piece, position: Position) -> int:
        """Does the castling move. Returns castling side as 1 for queenside and 2 for kingside"""
        # Queen side castling
        if position.column == 2:
            castling = 1
            rook = self.get_piece((0, piece.position.rank))
            self.move_piece(rook, Position(3, rook.position.rank))
        # King side castling
        else:
            castling = 2
            rook = self.get_piece((7, piece.position.rank))
            self.move_piece(rook, Position(5, rook.position.rank))

        # Moves the king
        self.move_piece(piece, position)

        return castling

    def is_promotion(self, piece, position: Position) -> bool:
        if isinstance(piece, Pawn):
            if position.rank == 0 or position.rank == 7:
                return True

    def promote(self, promoteTo):
        """Promotes a pawn to a piece of the given type"""
        promotedPiece = self.promotion.transform_to(promoteTo)
        self.set_piece(promotedPiece)

        # Adds and removes the pieces from the list of pieces
        self.add_piece(promotedPiece)
        self.remove_piece(promoteTo)

        self.promotion = None

    def get_king(self, color: bool):
        """Returns the king of the given color"""
        if color:
            return self.whiteKing
        else:
            return self.blackKing

    def get_valid_moves(self, color: bool = None) -> dict:
        """Returns a 2D dict of pieces and their moves as {Piece:[Moves]}"""
        pieces = {}
        # Looping through the pieces and storing their valid moves in a dict
        for piece in self.get_pieces(color):
            moves = piece.get_valid_moves(self)
            if moves:
                pieces[piece] = moves
        return pieces


class Piece:
    def __init__(self, position: Union[Position, tuple[int, int]], color: bool):
        if isinstance(position, Position):
            self.position = position
        else:
            self.position = Position(*position)
        self.color = color

    def get_zobrist_key(self) -> int:
        """Returns the zobrist key of the piece"""
        return zobrist[self.__class__.__name__][self.color][self.position.column + self.position.rank * 8]

    def try_check(self, board: Board, position: Position) -> bool:
        """Returns a boolean indicating if the king will get into a check after the move is done"""
        # If the king is under check allready
        if board.underCheck:
            # If amount of pieces checking the kins is just one
            if len(board.counterChecks) == 1:
                if position in board.counterChecks[0]:
                    return False
        # Not under check
        else:
            # Normal Move
            if self.position not in board.pinnedSquares:
                return False
            # If the piece is pinned you can only move it on the pinned line
            else:
                for line in board.pinnedLines:
                    if self.position in line and position in line:
                        return False

        return True

    def transform_to(self, pieceType):
        """Transforms a piece to a new type"""
        return pieceType(self.position, self.color)

    def valid_empty_or_capturing(self, board: Board, position: Position):
        """You can only move to an empty square or capture an enemy piece not yours"""
        if not board.get_piece(position):
            return True
        else:
            return self.valid_capturing(board, position)

    def valid_capturing(self, board: Board, position: Position) -> bool:
        """Colors can only capture enemey colored pieces not their own"""
        piece = board.get_piece(position)
        if piece and piece.color != self.color:
            return position
        else:
            return None


def color_to_play(get_valid_moves):
    """Decorator function that only allows the right color to play -> white at the start and then changing"""

    def wrapper(*args, **kwargs):
        piece = args[0]
        board = args[1]
        # Right color to play
        if kwargs.get("includeDefense") == True:
            return get_valid_moves(*args, **kwargs)
        elif (
            not board.lastMove and piece.color == True or board.lastMove and board.lastMove.piece.color != piece.color
        ):
            return get_valid_moves(*args, **kwargs)
        # Wrong color to play
        else:
            return []

    return wrapper


def filter_checks(get_valid_moves):
    """Decorator function to filter out positions where you end up in check from function Piece.get_valid_moves"""

    def wrapper(*args, **kwargs):
        piece = args[0]
        board = args[1]

        if kwargs.get("includeDefense") == True:
            return get_valid_moves(*args, **kwargs)
        else:
            validPositions = []
            for position in get_valid_moves(*args, **kwargs):
                if not piece.try_check(board, position):
                    validPositions.append(position)
            return validPositions

    return wrapper


def piece_count(pieces: list) -> dict:
    """Returns a dict of piece types and their count in the given list"""
    piecesDict = {}
    for piece in [piece.__class__ for piece in pieces]:
        if piece in piecesDict:
            piecesDict[piece] += 1
        else:
            piecesDict[piece] = 1
    return piecesDict


def rook_and_bishop_lines(piece: Piece, board: Board, lines: list, includeDefense: bool) -> list:
    """Returns a list of positions that the piece can move to"""
    validMoves = []
    # Looking for checks and pinned pieces
    if includeDefense:
        pinnedLines = []
        counterChecks = []
        for line in lines:
            lineSoFar = []
            foundPiece = False
            for position in line:
                if not foundPiece:
                    validMoves.append(position)
                lineSoFar.append(position)

                if board.get_piece(position):
                    if board.get_piece(position) == board.get_king(not piece.color):
                        pinnedLine = lineSoFar[:-1] + [piece.position]
                        if foundPiece:
                            pinnedLines.append(pinnedLine)
                            break
                        else:
                            counterChecks = [pinnedLine]
                    elif not foundPiece:
                        foundPiece = True
                    else:
                        break
        return validMoves, counterChecks, pinnedLines
    # looking for all possible moves
    else:
        for line in lines:
            # Loops through all the positions in a line and adds them to the list until it finds a piece
            for position in line:
                if piece.valid_empty_or_capturing(board, position):
                    validMoves.append(position)
                if board.get_piece(position):
                    break
        return validMoves


class Move:
    def __init__(
        self,
        start: Union[Position, tuple[int, int]],
        end: Union[Position, tuple[int, int]],
        piece: Piece,
        capturedPiece=None,
        enpassant=False,
        castling=False,
        promotion=False,
    ):
        if not isinstance(start, Position):
            start = Position(start)
        self.start = start
        if not isinstance(end, Position):
            end = Position(end)
        self.end = end

        self.piece = piece
        self.capturedPiece = capturedPiece

        self.enpassant = enpassant
        self.castling = castling
        self.promotion = promotion

        if isinstance(piece, (Rook, King)):
            self.originalHasMoved = piece.hasMoved


class Pawn(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    points = 1

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        validMoves = []
        # Moving just forward without capturing
        if self.color == True:
            rank, rank1 = -1, 6
        else:
            rank, rank1 = 1, 1

        # Other pieces return all threatening moves and with this parameter also the defended pieces however the pawn -
        # behaves a little differently so we will return just it's two attacking moves
        if includeDefense:
            counterChecks = []
            positions = [Position(self.position.column + column, self.position.rank + rank) for column in [-1, 1]]
            for position in positions:
                if board.get_piece(position) == board.get_king(not self.color):
                    counterChecks = [[self.position]]
                    break
            return positions, counterChecks, []

        # Moving forward without capturing
        position = Position(self.position.column, self.position.rank + rank)
        if not board.get_piece(position):
            validMoves.append(position)
            position = Position(self.position.column, self.position.rank + rank * 2)
            if self.position.rank == rank1 and not board.get_piece(position):
                validMoves.append(position)

        # Capturing a piece
        # Regular capture case
        if self.color == True:
            rank = -1
        else:
            rank = +1

        if self.position.column != 0:
            position = Position((self.position.column - 1, self.position.rank + rank))
            if self.valid_capturing(board, position):
                validMoves.append(position)
        if self.position.column != 7:
            position = Position(self.position.column + 1, self.position.rank + rank)
            if self.valid_capturing(board, position):
                validMoves.append(position)

        # Enpassant capture case
        if self.color == True:
            rank, rank1, rank2 = -1, 3, 1
        else:
            rank, rank1, rank2 = +1, 4, 6

        if self.position.rank == rank1:
            if board.lastMove and isinstance(board.lastMove.piece, Pawn):
                if board.lastMove.start.rank == rank2 and board.lastMove.piece.position.rank == rank1:
                    if board.lastMove.start.column == self.position.column - 1:
                        validMoves.append(Position((self.position.column - 1, self.position.rank + rank)))
                    elif board.lastMove.start.column == self.position.column + 1:
                        validMoves.append(Position((self.position.column + 1, self.position.rank + rank)))

        return validMoves


class Rook(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.hasMoved = False

    points = 5

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Rook can move in any straight direction
        lines = []
        # Left
        lines.append([Position((column, self.position.rank)) for column in reversed(range(0, self.position.column))])
        # Right
        lines.append([Position((column, self.position.rank)) for column in range(self.position.column + 1, 8)])
        # Up
        lines.append([Position((self.position.column, rank)) for rank in reversed(range(0, self.position.rank))])
        # Down
        lines.append([Position((self.position.column, rank)) for rank in range(self.position.rank + 1, 8)])

        return rook_and_bishop_lines(self, board, lines, includeDefense)


class Knight(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    points = 3

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Horse can only move in 8 different combinations
        combinations = [[-2, -1], [-1, -2], [-2, 1], [1, -2], [2, -1], [-1, 2], [2, 1], [1, 2]]

        validMoves = []
        counterChecks = []
        # Loops through all of the combinations
        for position in combinations:
            position = Position(self.position.column + position[0], self.position.rank + position[1])
            # If the position is within the playing field
            if position.is_in_bounds():
                if includeDefense:
                    validMoves.append(position)
                    if board.get_piece(position) == board.get_king(not self.color):
                        counterChecks = [[self.position]]
                elif self.valid_empty_or_capturing(board, position) or includeDefense:
                    validMoves.append(position)

        if includeDefense:
            return validMoves, counterChecks, []
        else:
            return validMoves


class Bishop(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.diagonal = (self.position.column + self.position.rank) % 2

    points = 3

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Bishop can only move in 4 diagonal directions
        lines = []
        # Top-left
        less = min(self.position.column, self.position.rank)
        lines.append([Position((self.position.column - i, self.position.rank - i)) for i in range(1, less + 1)])
        # Top-right
        less = min(7 - self.position.column, self.position.rank)
        lines.append([Position((self.position.column + i, self.position.rank - i)) for i in range(1, less + 1)])
        # Bottom-right
        less = min(7 - self.position.column, 7 - self.position.rank)
        lines.append([Position((self.position.column + i, self.position.rank + i)) for i in range(1, less + 1)])
        # Bottom-left
        less = min(self.position.column, 7 - self.position.rank)
        lines.append([Position((self.position.column - i, self.position.rank + i)) for i in range(1, less + 1)])

        return rook_and_bishop_lines(self, board, lines, includeDefense)


class Queen(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    points = 9

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # We can inherit the Rook and Bishop classes to make this easier
        rookMoves = self.transform_to(Rook).get_valid_moves(board, includeDefense=includeDefense)
        bishopMoves = self.transform_to(Bishop).get_valid_moves(board, includeDefense=includeDefense)

        board.set_piece(self)

        if includeDefense:
            return rookMoves[0] + bishopMoves[0], rookMoves[1] + bishopMoves[1], rookMoves[2] + bishopMoves[2]
        else:
            return rookMoves + bishopMoves


class King(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.hasMoved = False

    points = 0

    def is_under_check(self, board: Board) -> bool:
        """Checks if the king is under check by any enemy piece"""
        if self.position in board.attackedSquares:
            return True
        else:
            return False

    @color_to_play
    def get_valid_moves(self, board: Board, noCastle: bool = False, includeDefense: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # King can move in any direction one tile
        validMoves = []
        # Looping through 3x3 grid around the king
        for column in range(self.position.column - 1, self.position.column + 2):
            for rank in range(self.position.rank - 1, self.position.rank + 2):
                position = Position((column, rank))
                # Not continue if the move is on your own square
                if not position == self.position:
                    # Check if the move is in bounds of the chess board
                    if position.is_in_bounds():
                        # Only move to empty squares or a square with an enemy piece not yours
                        if self.valid_empty_or_capturing(board, position) or includeDefense:
                            # Not moving into an attacked square
                            if not position in board.attackedSquares or includeDefense:
                                validMoves.append(position)

        # King can also castle if it has not moved yet
        # Doesn't pass if argument noCastle is set to True
        if not self.hasMoved and not noCastle:
            # Can't castle if the king is under check
            if not self.try_check(board, self.position):
                # King can castle with a rook that also hasn't moved yet
                # There must also not be any pieces inbetween the king and the rook
                if self.color == True:
                    rank = 7
                else:
                    rank = 0
                # Queenside castle
                if isinstance(board.get_piece((0, rank)), Rook) and not board.get_piece((0, rank)).hasMoved:
                    if not board.get_piece((1, rank)):
                        for column in range(2, 4):
                            if board.get_piece((column, rank)) or Position(column, rank) in board.attackedSquares:
                                break
                        else:
                            validMoves.append(Position((2, rank)))
                # Kingside castle
                if isinstance(board.get_piece((7, rank)), Rook) and not board.get_piece((7, rank)).hasMoved:
                    for column in range(5, 7):
                        if board.get_piece((column, rank)) or Position(column, rank) in board.attackedSquares:
                            break
                    else:
                        validMoves.append(Position((6, rank)))

        if includeDefense:
            return validMoves, [], []
        else:
            return validMoves


def zobrist_init():
    """Initializes the zobrist hash"""
    global zobrist

    pieces = [Pawn, Rook, Knight, Bishop, Queen, King]

    # Generates 64 * 6 * 2 = 768 unique zobrist keys
    keys = []
    while len(keys) < 768:
        randKey = random.getrandbits(64)
        if randKey not in keys:
            keys.append(randKey)

    # Generates an empty dict
    zobrist = dict((p.__name__, dict((col, dict((i, None) for i in range(64))) for col in [0, 1])) for p in pieces)

    # Assigns each key
    for piece in pieces:
        for color in [True, False]:
            for i in range(64):
                zobrist[piece.__name__][color][i] = keys[-1]
                keys.pop(-1)


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
