import sys
from typing import Tuple

import pygame

import ai
import chess

AI_DEPTH = 4

# Window settings
WIDTH = 1000
HEIGHT = 1000
FPS = 60

# Pygame setup
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Chess")
pygame.font.init()

# Chessboard visual settings
TILE_SIZE = 90
WHITE_COLOR = (238, 238, 210)
BLACK_COLOR = (118, 150, 86)
WHITE_SELECTED_COLOR = (246, 246, 105)
BLACK_SELECTED_COLOR = (186, 202, 43)
WHITE_HINT_COLOR = (255, 204, 203)
BLACK_HINT_COLOR = (220, 148, 146)

# Background visual settings
BACKGROUND_COLOR = (49, 46, 43)
background = pygame.Surface((WIDTH, HEIGHT))
background.fill(BACKGROUND_COLOR)
chessboard = pygame.Surface((8 * TILE_SIZE, 8 * TILE_SIZE))

# Promotion box settings and AI button settings
PROMOTION_BORDER_SIZE = 3
PROMOTION_BORDER_COLOR = "#272522"
PROMOTION_BUTTON_BACKGROUND_COLOR = "#1F1E1B"
PROMOTION_PROMOTE_TO_PIECES = (chess.Queen, chess.Knight, chess.Rook, chess.Bishop)
# AI button
AI_BUTTON_WIDTH = int(TILE_SIZE / 1.25)
AI_BUTTON_HEIGHT = int(TILE_SIZE / 2.5)

# Results box settings
RESULTS_BORDER_SIZE = 5
RESULTS_BORDER_COLOR = "#565352"
RESULTS_BACKGROUND_COLOR = "#FFFFFF"
RESULTS_FONT = pygame.font.SysFont("Source Sans Pro", int(TILE_SIZE / 2.75), True)
RESULTS_WIDTH = TILE_SIZE * 3.5
RESULTS_HEIGHT = TILE_SIZE * 4.5
# Result buttons settings
RESULTS_BUTTON_BORDER_SIZE = 3
RESULTS_BUTTON_BORDER_COLOR = "#565352"
RESULTS_BUTTON_BACKGROUND_COLOR = "#7FA650"
RESULTS_BUTTON_FONT = pygame.font.SysFont("Arial", int(TILE_SIZE / 3.25), True)
RESULTS_BUTTON_WIDTH = TILE_SIZE * 2.4
RESULTS_BUTTON_HEIGHT = RESULTS_BUTTON_FONT.get_height() * 1.5


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
    # Gets the valid moves if there is a selected piece
    if selectedPiece:
        possibleMoves = selectedPiece.get_valid_moves(board)

    # Looping through all the tiles
    for column in range(8):
        for rank in range(8):
            # Background color for the square
            # Default colors unless rewriten below
            white = WHITE_COLOR
            black = BLACK_COLOR
            # While having a selected piece
            if selectedPiece:
                # The selected square
                if selectedPiece.position == (column, rank):
                    white = WHITE_SELECTED_COLOR
                    black = BLACK_SELECTED_COLOR
                # Available moves
                elif chess.Position(column, rank) in possibleMoves:
                    white = WHITE_HINT_COLOR
                    black = BLACK_HINT_COLOR

            # Switches black and white color
            if (rank + column) % 2 == 0:
                color = white
            else:
                color = black

            # Gets the tile and draws it
            tile = pygame.Rect((column * TILE_SIZE, rank * TILE_SIZE), (TILE_SIZE, TILE_SIZE))
            pygame.draw.rect(chessboard, color, tile)

            # Adds the piece image to the square
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


def draw_result_box(board: chess.Board):
    """Draws the results of the game"""
    resultBox = pygame.Surface((RESULTS_WIDTH, RESULTS_HEIGHT))
    # Background
    resultBox.fill(RESULTS_BACKGROUND_COLOR)
    # Border
    pygame.draw.rect(resultBox, RESULTS_BORDER_COLOR, resultBox.get_rect(), RESULTS_BORDER_SIZE)
    # Write a text of who has won
    if board.result == 0:
        text = "White has won!"
    elif board.result == 1:
        text = "Black has won!"
    else:
        text = "It's a draw!"
    resultText = RESULTS_FONT.render(text, True, (0, 0, 0))
    resultBox.blit(resultText, ((RESULTS_WIDTH - resultText.get_width()) / 2, resultText.get_height() * 2))

    def draw_button(text: str, position: Tuple[int, int]):
        """Draws a button with the given text"""
        # Button size
        button = pygame.Surface((BUTTON_WIDTH, BUTTON_HEIGHT))
        # Background
        button.fill(RESULTS_BUTTON_BACKGROUND_COLOR)
        # Border
        pygame.draw.rect(button, RESULTS_BUTTON_BORDER_COLOR, button.get_rect(), RESULTS_BUTTON_BORDER_SIZE)
        # Button text
        buttonText = RESULTS_BUTTON_FONT.render(text, True, (255, 255, 255))
        # Drawing the text
        button.blit(
            buttonText, ((BUTTON_WIDTH - buttonText.get_width()) / 2, (BUTTON_HEIGHT - buttonText.get_height()) / 2)
        )
        # Drawing the button
        resultBox.blit(button, position)

    BUTTON_WIDTH = RESULTS_BUTTON_WIDTH
    BUTTON_HEIGHT = RESULTS_BUTTON_HEIGHT
    # New game button
    draw_button("New game", ((RESULTS_WIDTH - BUTTON_WIDTH) / 2, RESULTS_HEIGHT / 2 + BUTTON_HEIGHT))
    # Quit button
    draw_button("Quit", ((RESULTS_WIDTH - BUTTON_WIDTH) / 2, RESULTS_HEIGHT / 2 + BUTTON_HEIGHT * 2.5))

    win.blit(resultBox, (WIDTH / 2 - RESULTS_WIDTH / 2, WIDTH / 2 - RESULTS_HEIGHT / 2))


def get_clicked_result():
    """Gets the clicked button in result box"""
    mouse = pygame.mouse.get_pos()

    BUTTON_WIDTH = RESULTS_BUTTON_WIDTH
    BUTTON_HEIGHT = RESULTS_BUTTON_HEIGHT

    newGameButton = pygame.Rect(WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 + BUTTON_HEIGHT, BUTTON_WIDTH, BUTTON_HEIGHT)
    if newGameButton.collidepoint(mouse):
        return 0

    quitButton = pygame.Rect(
        WIDTH / 2 - BUTTON_WIDTH / 2, HEIGHT / 2 + BUTTON_HEIGHT * 2.5, BUTTON_WIDTH, BUTTON_HEIGHT
    )
    if quitButton.collidepoint(mouse):
        return 1


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


def draw_ai_button(AI):
    """Draws the AI switch button"""
    BORDER_SIZE = PROMOTION_BORDER_SIZE
    BORDER_COLOR = PROMOTION_BORDER_COLOR
    BACKGROUND_COLOR = PROMOTION_BUTTON_BACKGROUND_COLOR

    button = pygame.Surface((AI_BUTTON_WIDTH, AI_BUTTON_HEIGHT))
    button.fill(BACKGROUND_COLOR)
    pygame.draw.rect(button, BORDER_COLOR, button.get_rect(), BORDER_SIZE)

    # AI off
    if AI == None:
        color = (128, 0, 0)
        left = BORDER_SIZE
    else:
        color = (128, 128, 128) if AI else (0, 0, 0)
        left = TILE_SIZE / 1.25 / 2
    pygame.draw.rect(
        button,
        color,
        (left, BORDER_SIZE, TILE_SIZE / 1.25 / 2 - BORDER_SIZE, TILE_SIZE / 2.5 - BORDER_SIZE * 2),
    )

    win.blit(
        button,
        (WIDTH * 0.75 + chessboard.get_width() / 4 - AI_BUTTON_WIDTH / 2, HEIGHT / 2 - AI_BUTTON_HEIGHT / 2),
    )


def clicked_ai_button() -> bool:
    """Returns if the mouse has clicked on the button"""
    return pygame.Rect(
        WIDTH * 0.75 + chessboard.get_width() / 4 - AI_BUTTON_WIDTH / 2,
        HEIGHT / 2 - AI_BUTTON_HEIGHT / 2,
        AI_BUTTON_WIDTH,
        AI_BUTTON_HEIGHT,
    ).collidepoint(pygame.mouse.get_pos())


def update(updateBoard: bool, board: chess.Board, selectedPiece: chess.Piece, AI):
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

        # Result box
        if board.result != None:
            draw_result_box(board)

        # AI switch button
        draw_ai_button(AI)

    pygame.display.update()


def main():
    board = generate_board()
    selectedPiece = None
    AI = None

    # Draws the screen for the first time
    chess.assign_images(TILE_SIZE)
    win.blit(background, (0, 0))
    update(True, board, selectedPiece, AI)

    clock = pygame.time.Clock()
    run = True
    while run:
        updateBoard = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Clicking on AI switch button
                if clicked_ai_button():
                    # Switches the AI on and off
                    if AI == None:
                        # Turn on
                        if not board.lastMove:
                            # First move
                            AI = True
                        else:
                            # Locks the AI to play as the current color to move
                            AI = not board.lastMove.piece.color
                        ai.make_move(board, AI_DEPTH)
                    else:
                        # Turn off
                        AI = None
                    updateBoard = True
                # Getting the clicked button in the result box (End of game)
                if board.result != None:
                    clickedOn = get_clicked_result()
                    # New game
                    if clickedOn == 0:
                        board = generate_board()
                        updateBoard = True
                    # Quit
                    elif clickedOn == 1:
                        pygame.display.quit()
                        pygame.quit()
                        sys.exit()
                # Getting the clicked button in the promotion box (When a pawn is promoting)
                elif board.promotion:
                    # Promoting a pawn
                    promoteTo = get_clicked_promotion()
                    if promoteTo:
                        board.promote(promoteTo)
                        updateBoard = True
                # Regular piece movement and selection
                else:
                    # Moving and selecting pieces
                    # If there is a selected piece, move it
                    clickedTile = get_mouse_position()
                    if selectedPiece:
                        # Only move the selected piece when clicked on the board
                        if clickedTile:
                            # Only move to a valid position
                            if clickedTile in selectedPiece.get_valid_moves(board):
                                board.move(selectedPiece, clickedTile)
                                if AI != None:
                                    ai.make_move(board, AI_DEPTH)
                                updateBoard = True
                            selectedPiece = None
                        updateBoard = True
                    else:
                        # Only selects a piece when clicked on the board
                        if clickedTile:
                            # Selects a piece
                            selectedPiece = board.get_piece(get_mouse_position())
                            updateBoard = True

        # Updates the board
        update(updateBoard, board, selectedPiece, AI)

        # Locking the framerate
        clock.tick(FPS)


if __name__ == "__main__":
    main()
