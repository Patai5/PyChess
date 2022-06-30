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

# Promotion box settings
PROMOTION_BORDER_SIZE = 3
PROMOTION_BORDER_COLOR = "#272522"
PROMOTION_BUTTON_BACKGROUND_COLOR = "#1F1E1B"
PROMOTION_PROMOTE_TO_PIECES = (chess.Queen, chess.Knight, chess.Rook, chess.Bishop)


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


def get_clicked_promotion():
    """Gets the clicked promotion piece under the mouse"""
    BORDER_SIZE = PROMOTION_BORDER_SIZE

    mouse = pygame.mouse.get_pos()

    # Box position, width and height
    width, height = 4 * (TILE_SIZE + BORDER_SIZE) + BORDER_SIZE, TILE_SIZE + BORDER_SIZE * 2
    left = WIDTH / 2 - width / 2
    top = (HEIGHT - chessboard.get_height()) / 2 - height * 1.1

    # Gets the clicked piece and returns it
    buttons = [
        pygame.Rect(left + BORDER_SIZE + (TILE_SIZE + BORDER_SIZE) * i, top + BORDER_SIZE, TILE_SIZE, TILE_SIZE)
        for i in range(4)
    ]
    for button, piece in zip(buttons, PROMOTION_PROMOTE_TO_PIECES):
        if button.collidepoint(mouse):
            return piece


def draw_promotion_box(pieceColor: bool = None):
    """Draws the promotion box"""
    BORDER_COLOR = PROMOTION_BORDER_COLOR
    BORDER_SIZE = PROMOTION_BORDER_SIZE
    BUTTON_BACKGROUND_COLOR = PROMOTION_BUTTON_BACKGROUND_COLOR

    promotionBox = pygame.Surface((4 * (TILE_SIZE + BORDER_SIZE) + BORDER_SIZE, TILE_SIZE + BORDER_SIZE * 2))
    # If the piece color is not specified, draw the box as background
    if pieceColor is not None:
        # The actual box
        promotionBox.fill(BORDER_COLOR)

        # Loops through all the promotion pieces and draws them into the box
        for i, piece in enumerate(PROMOTION_PROMOTE_TO_PIECES):
            square = pygame.Rect((i * (TILE_SIZE + BORDER_SIZE) + BORDER_SIZE, BORDER_SIZE, TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(promotionBox, BUTTON_BACKGROUND_COLOR, square)
            if pieceColor:
                promotionBox.blit(piece.whiteImg, square)
            else:
                promotionBox.blit(piece.blackImg, square)
    else:
        # As background
        promotionBox.fill(BACKGROUND_COLOR)

    # Draws the promotion box onto the screen
    win.blit(
        promotionBox,
        (
            WIDTH / 2 - promotionBox.get_width() / 2,
            (HEIGHT - chessboard.get_height()) / 2 - promotionBox.get_height() * 1.1,
        ),
    )


def update(updateBoard: bool, board: chess.Board, selectedPiece: chess.Piece):
    """Updates the board"""
    # Draws stuff only when needed
    if updateBoard:
        # Promotion box
        if board.promotion:
            draw_promotion_box(board.promotion.color)
        else:
            draw_promotion_box()

        # Chessboard
        draw_board(board, selectedPiece)
        win.blit(chessboard, (WIDTH / 2 - 8 / 2 * TILE_SIZE, HEIGHT / 2 - 8 / 2 * TILE_SIZE))

    pygame.display.update()


def main():
    board = generate_board()
    selectedPiece = None

    # Draws the screen for the first time
    chess.assign_images(TILE_SIZE)
    win.blit(background, (0, 0))
    update(True, board, selectedPiece)

    clock = pygame.time.Clock()
    run = True
    while run:
        updateBoard = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if board.promotion:
                    # Promoting a pawn
                    promoteTo = get_clicked_promotion()
                    if promoteTo:
                        board.promote(promoteTo)
                        updateBoard = True
                else:
                    # Moving and selecting pieces
                    # If there is a selected piece, move it
                    clickedTile = get_mouse_position()
                    if selectedPiece:
                        # Only move the selected piece when clicked on the board
                        if clickedTile:
                            # Do not move to the same position as you are already on
                            if clickedTile != selectedPiece.position:
                                board.move_piece(selectedPiece, clickedTile)
                        selectedPiece = None
                        updateBoard = True
                    else:
                        # Only selects a piece when clicked on the board
                        if clickedTile:
                            # Selects a piece
                            selectedPiece = board.get_piece(get_mouse_position())
                            updateBoard = True

        # Updates the board
        update(updateBoard, board, selectedPiece)

        # Locking the framerate
        clock.tick(FPS)


if __name__ == "__main__":
    main()
