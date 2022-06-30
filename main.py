import pygame

import chess

# Window settings
WIDTH = 800
HEIGHT = 800
FPS = 60

# Pygame setup
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")

# Chessboard visual settings
TILE_SIZE = 75
WHITE_COLOR = (238, 238, 210)
BLACK_COLOR = (118, 150, 86)
WHITE_SELECTED_COLOR = (246, 246, 105)
BLACK_SELECTED_COLOR = (186, 202, 43)

# Background visual settings
BACKGROUND_COLOR = (49, 46, 43)
background = pygame.Surface((WIDTH, HEIGHT))
background.fill(BACKGROUND_COLOR)
chessboard = pygame.Surface((8 * TILE_SIZE, 8 * TILE_SIZE))


def generate_board():
    """Generates a board with pieces in the correct positions"""
    pieces = [
        chess.Rook((0, 0), False),
        chess.Knight((1, 0), False),
        chess.Bishop((2, 0), False),
        chess.Queen((3, 0), False),
        chess.King((4, 0), False),
        chess.Bishop((5, 0), False),
        chess.Knight((6, 0), False),
        chess.Rook((7, 0), False),
        chess.Rook((0, 7), True),
        chess.Knight((1, 7), True),
        chess.Bishop((2, 7), True),
        chess.Queen((3, 7), True),
        chess.King((4, 7), True),
        chess.Bishop((5, 7), True),
        chess.Knight((6, 7), True),
        chess.Rook((7, 7), True),
    ]

    # Pawns
    for column in range(8):
        pieces.append(chess.Pawn((column, 1), False))
        pieces.append(chess.Pawn((column, 6), True))

    return chess.Board(pieces)


def draw_board(board: chess.Board, selectedPiece: chess.Piece = None):
    """Draws the board with all the pieces"""
    # Looping through all the tiles
    for column in range(8):
        for rank in range(8):
            # Background color for the selected piece
            if selectedPiece and selectedPiece.position == (column, rank):
                if (rank + column) % 2 == 0:
                    color = WHITE_SELECTED_COLOR
                else:
                    color = BLACK_SELECTED_COLOR
            else:
                if (rank + column) % 2 == 0:
                    color = WHITE_COLOR
                else:
                    color = BLACK_COLOR

            # Gets the tile and draws it
            tile = pygame.Rect((column * TILE_SIZE, rank * TILE_SIZE), (TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(chessboard, color, tile)

            piece = board.get_piece((column, rank))
            if piece:
                if piece.color == False:
                    chessboard.blit(piece.blackImg, tile.topleft)
                else:
                    chessboard.blit(piece.whiteImg, tile.topleft)


def get_mouse_position() -> chess.Position:
    """Gets the square position under the mouse"""
    mouse = pygame.mouse.get_pos()

    # If the mouse is outside the board, return None
    if (
        mouse[0] > WIDTH / 2 - 8 / 2 * TILE_SIZE
        and mouse[0] < WIDTH / 2 + 8 / 2 * TILE_SIZE
        and mouse[1] > HEIGHT / 2 - 8 / 2 * TILE_SIZE
        and mouse[1] < HEIGHT / 2 + 8 / 2 * TILE_SIZE
    ):
        # Gets the position in tiles from the mouse position
        return chess.Position(
            int((mouse[0] - (WIDTH / 2 - 8 / 2 * TILE_SIZE)) // TILE_SIZE),
            int((mouse[1] - (HEIGHT / 2 - 8 / 2 * TILE_SIZE)) // TILE_SIZE),
        )
    else:
        return None


def update(updateBoard: bool, board: chess.Board, selectedPiece: chess.Piece):
    """Updates the board"""
    if updateBoard:
        draw_board(board, selectedPiece)
        win.blit(chessboard, (WIDTH / 2 - 8 / 2 * TILE_SIZE, HEIGHT / 2 - 8 / 2 * TILE_SIZE))

    pygame.display.update()


def main():
    board = generate_board()

    # Draws the screen for the first time
    chess.assign_images(TILE_SIZE)
    win.blit(background, (0, 0))
    draw_board(board)
    win.blit(chessboard, (WIDTH / 2 - 8 / 2 * TILE_SIZE, HEIGHT / 2 - 8 / 2 * TILE_SIZE))

    selectedPiece = None

    clock = pygame.time.Clock()
    run = True
    while run:
        updateBoard = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # If there is a selected piece, move it
                if selectedPiece:
                    clickedTile = get_mouse_position()
                    # Only move the selected piece when clicked on the board
                    if clickedTile:
                        # Do not move to the same position as you are already on
                        if clickedTile != selectedPiece.position:
                            board.move_piece(selectedPiece, clickedTile)
                    selectedPiece = None
                    updateBoard = True
                else:
                    # Selects a piece
                    selectedPiece = board.get_piece(get_mouse_position())
                    updateBoard = True

        # Updates the board
        update(updateBoard, board, selectedPiece)

        # Locking the framerate
        clock.tick(FPS)


if __name__ == "__main__":
    main()
