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

    def __iter__(self):
        yield self.column
        yield self.rank

    def is_in_bounds(self) -> bool:
        """Returns a bool value representing if the position is a valid square on a chessboard"""
        if 7 >= self.column >= 0 and 7 >= self.rank >= 0:
            return True
        else:
            return False


class Board:
    def __init__(self, pieces: List) -> None:
        self.board = [[None for rank in range(8)] for column in range(8)]
        self.lastMove = None
        self.promotion = None
        self.result = None

        for piece in pieces:
            self.set_piece(piece)
            # Saves the kings for easier access
            if isinstance(piece, King):
                if piece.color == True:
                    self.whiteKing = piece
                else:
                    self.blackKing = piece

    def get_piece(self, position: Union[Position, Tuple[int, int]]):
        """Returns a piece at the given position"""
        if not isinstance(position, Position):
            position = Position(*position)
        return self.board[position.column][position.rank]

    def get_pieces(self, color: bool = None):
        """Returns all pieces. If color is given, only returns pieces of that color"""
        pieces = []
        for column in range(8):
            for rank in range(8):
                piece = self.get_piece((column, rank))
                if piece:
                    if color != None:
                        if piece.color == color:
                            pieces.append(piece)
                    else:
                        pieces.append(piece)
        return pieces

    def set_piece(self, piece, position: Position = None):
        """Sets a piece at it's position"""
        # Uses the position of the piece by default. If specified, uses the given position
        if position:
            piece.position = position
        self.board[piece.position.column][piece.position.rank] = piece

    def clear_square(self, position: Position):
        """Clears a square at the given position"""
        self.board[position.column][position.rank] = None

    def move_piece(self, piece, position: Position, tryMove: bool = False):
        """Moves a piece to the given position\n
        - "tryMove" argument is used for checking purposes -> "lastMove" and "hasMove" are not stored"""
        if not tryMove:
            # Sets the last move as the move currently made
            self.lastMove = Move(piece, piece.position)

        # Moves the piece
        self.clear_square(piece.position)
        self.set_piece(piece, position)

        if not tryMove:
            # For rooks and king sets their hasMoved property
            if isinstance(piece, (King, Rook)) and not piece.hasMoved:
                piece.hasMoved = True

    def move(self, piece, position: Position):
        """Moves a piece to the given position"""
        # Enpassant move
        if self.is_enpassant(piece, position):
            self.enpassant(piece, position)
        # Castling move
        elif self.is_castling(piece, position):
            self.castle(piece, position)
        # Promotion
        elif self.is_promotion(piece, position):
            self.move_piece(piece, position)
            self.promotion = piece
        # Normal move
        else:
            self.move_piece(piece, position)

        # Checks for checkmate or stalemate
        self.round_check()

    def round_check(self):
        """Checks for checkmate or stalemate"""
        whitePieces = self.get_pieces(True)
        blackPieces = self.get_pieces(False)

        # Checks if the other party has any valid moves
        color = not self.lastMove.piece.color
        if not any(self.get_valid_moves(color)):
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
        """Does the enpassant move"""
        self.move_piece(piece, position)
        # Clears the enpassanted pawn
        if piece.color == True:
            self.clear_square(Position(piece.position.column, piece.position.rank + 1))
        else:
            self.clear_square(Position(piece.position.column, piece.position.rank - 1))

    def is_castling(self, piece, position: Position) -> bool:
        """Returns true if the move is a castling move"""
        if isinstance(piece, King) and not piece.hasMoved:
            if position.column == 2 or position.column == 6:
                return True
        return False

    def castle(self, piece, position: Position):
        """Does the castling move"""
        # Queen side castling
        if position.column == 2:
            rook = self.get_piece((0, piece.position.rank))
            self.move_piece(rook, Position(3, rook.position.rank))
        # King side castling
        else:
            rook = self.get_piece((7, piece.position.rank))
            self.move_piece(rook, Position(5, rook.position.rank))

        # Moves the king
        self.move_piece(piece, position)

    def is_promotion(self, piece, position: Position) -> bool:
        if isinstance(piece, Pawn):
            if position.rank == 0 or position.rank == 7:
                return True

    def promote(self, promoteTo):
        """Promotes a pawn to a piece of the given type"""
        self.set_piece(self.promotion.transform_to(promoteTo))
        self.promotion = None

    def get_king(self, color: bool):
        """Returns the king of the given color"""
        if color:
            return self.whiteKing
        else:
            return self.blackKing

    def get_valid_moves(self, color: bool = None) -> List:
        """Returns a 2D array of pieces and their moves as [Piece[Move]]"""
        pieces = self.get_pieces(color)
        # Looping through the pieces and storing their valid moves in a list
        for i, piece in enumerate(pieces):
            pieces[i] = piece.get_valid_moves(self)
        return pieces


def piece_count(pieces: List) -> dict:
    """Returns a dict of piece types and their count in the given list"""
    piecesDict = {}
    for piece in [piece.__class__ for piece in pieces]:
        if piece in piecesDict:
            piecesDict[piece] += 1
        else:
            piecesDict[piece] = 1
    return piecesDict


class Piece:
    def __init__(self, position: Union[Position, Tuple[int, int]], color: bool):
        if isinstance(position, Position):
            self.position = position
        else:
            self.position = Position(*position)
        self.color = color

    def try_check(self, board: Board, move: Position) -> bool:
        """Returns a boolean indicating if the king will get into a check after the move is done"""
        # Stores the original position and the possibly captured piece in case of a check to revert it back
        origPosition = Position(tuple(self.position))
        origPiece = board.get_piece(move)

        board.move_piece(self, move, tryMove=True)

        # Checks for a check
        check = board.get_king(self.color).is_under_check(board)

        # Reverts the moves
        board.move_piece(self, origPosition, tryMove=True)
        if origPiece:
            board.set_piece(origPiece)

        return check

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
        if not board.lastMove and piece.color == True or board.lastMove and board.lastMove.piece.color != piece.color:
            return get_valid_moves(*args, **kwargs)
        # Wrong color to play
        else:
            return []

    return wrapper


def filter_checks(get_valid_moves):
    """Decorator function to filter out positions where you end up in check from function Piece.get_valid_moves"""

    def wrapper(*args, **kwargs):
        validPositions = get_valid_moves(*args, **kwargs)
        # We will not remove the checked positions from the list if the flag noFilterChecks exists
        if not "noFilterChecks" in kwargs:
            for position in validPositions[:]:
                if args[0].try_check(args[1], position):
                    validPositions.remove(position)
        return validPositions

    return wrapper


class Move:
    def __init__(self, piece: Piece, start: Position):
        self.piece = piece
        self.start = start


class Pawn(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        validMoves = []
        # Moving just forward without capturing
        if self.color == True:
            rank, rank1 = -1, 6
        else:
            rank, rank1 = 1, 1

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

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Rook can move in any direction
        validMoves = []
        # Left
        for column in reversed(range(0, self.position.column)):
            position = Position((column, self.position.rank))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Right
        for column in range(self.position.column + 1, 8):
            position = Position((column, self.position.rank))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Up
        for rank in reversed(range(0, self.position.rank)):
            position = Position((self.position.column, rank))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Down
        for rank in range(self.position.rank + 1, 8):
            position = Position((self.position.column, rank))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        return validMoves


class Knight(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Horse can only move in 8 different combinations
        combinations = [[-2, -1], [-1, -2], [-2, 1], [1, -2], [2, -1], [-1, 2], [2, 1], [1, 2]]

        validMoves = []
        for position in combinations:
            position = Position(self.position.column + position[0], self.position.rank + position[1])
            if position.is_in_bounds():
                if self.valid_empty_or_capturing(board, position):
                    validMoves.append(position)
        return validMoves


class Bishop(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.diagonal = (self.position.column + self.position.rank) % 2

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # Bishop can only move in 4 diagonal directions
        validMoves = []
        # Top-left
        less = min(self.position.column, self.position.rank)
        for i in range(1, less + 1):
            position = Position((self.position.column - i, self.position.rank - i))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Top-right
        less = min(7 - self.position.column, self.position.rank)
        for i in range(1, less + 1):
            position = Position((self.position.column + i, self.position.rank - i))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Bottom-right
        less = min(7 - self.position.column, 7 - self.position.rank)
        for i in range(1, less + 1):
            position = Position((self.position.column + i, self.position.rank + i))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        # Bottom-left
        less = min(self.position.column, 7 - self.position.rank)
        for i in range(1, less + 1):
            position = Position((self.position.column - i, self.position.rank + i))
            if self.valid_empty_or_capturing(board, position):
                validMoves.append(position)
            if board.get_piece(position):
                break
        return validMoves


class Queen(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # We can inherit the Rook and Bishop classes to make this easier
        validMoves = self.transform_to(Rook).get_valid_moves(board) + self.transform_to(Bishop).get_valid_moves(board)
        board.set_piece(self)
        return validMoves


class King(Piece):
    def __init__(self, position: Position, color: bool):
        super().__init__(position, color)
        self.hasMoved = False

    def is_under_check(self, board: Board) -> bool:
        """Checks if the king is under check by any enemy piece"""

        def check_piece(firstInstanceOf: Piece, instancesOf: List[Piece] = None) -> bool:
            """Checks if the piece can attack the king by looking at it's valid moves from the king's position and
            looking if there is such piece in the list of valid moves for that piece"""  # the fuck is this sentence lmao
            # If instancesOf is None, we set instancesOf as the firstInstanceOf
            if not instancesOf:
                instancesOf = firstInstanceOf
            # Pawn
            if firstInstanceOf == Pawn:
                # Pawn can only move forward
                if self.color:
                    rank = self.position.rank - 1
                else:
                    rank = self.position.rank + 1
                # We can capture to the left and right
                for position in ((self.position.column - 1, rank), (self.position.column + 1, rank)):
                    position = Position(position)
                    # If the position is valid
                    if position.is_in_bounds():
                        # If there is a pawn of a different color, we are under check
                        if (
                            isinstance(board.get_piece(position), Pawn)
                            and board.get_piece(position).color != self.color
                        ):
                            return True
                else:
                    return False
            # King
            elif firstInstanceOf == King:
                for position in self.get_valid_moves(board, noCastle=True, noFilterChecks=True):
                    if isinstance(board.get_piece(position), King) and board.get_piece(position).color != self.color:
                        return True
                else:
                    return False
            # Normal
            else:
                # Filters out only the positions where the piece of the enemy color is present
                return tuple(
                    filter(
                        lambda position: True
                        if isinstance(board.get_piece(position), instancesOf)
                        and board.get_piece(position).color != self.color
                        else False,
                        self.transform_to(firstInstanceOf).get_valid_moves(board, noFilterChecks=True),
                    )
                )

        # Pawn
        if check_piece(Pawn):
            return True
        # Rook and queen
        if check_piece(Rook, (Rook, Queen)):
            return True
        # Knight
        if check_piece(Knight):
            return True
        # Bishop and queen
        if check_piece(Bishop, (Bishop, Queen)):
            return True
        # King
        if check_piece(King):
            return True

    @color_to_play
    @filter_checks
    def get_valid_moves(self, board: Board, noCastle: bool = False, **kwargs) -> list:
        """Returns a list of all valid moves for the piece"""
        # King can move in any direction one tile
        validMoves = []
        # Looping through 3x3 grid around the king
        for column in range(self.position.column - 1, self.position.column + 2):
            for rank in range(self.position.rank - 1, self.position.rank + 2):
                possibleMove = Position((column, rank))
                # Not continue if the move is on your own square
                if not possibleMove == self.position:
                    # Check if the move is in bounds of the chess board
                    if possibleMove.is_in_bounds():
                        # Only move to empty squares or a square with an enemy piece not yours
                        if self.valid_empty_or_capturing(board, possibleMove):
                            validMoves.append(possibleMove)

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
                            if board.get_piece((column, rank)) or self.try_check(board, Position(column, rank)):
                                break
                        else:
                            validMoves.append(Position((2, rank)))
                # Kingside castle
                if isinstance(board.get_piece((7, rank)), Rook) and not board.get_piece((7, rank)).hasMoved:
                    for column in range(5, 7):
                        if board.get_piece((column, rank)) or self.try_check(board, Position(column, rank)):
                            break
                    else:
                        validMoves.append(Position((6, rank)))
        return validMoves


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
