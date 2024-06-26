import copy


class GameState:
    """
    Class for storing all the information about state of board
    """

    # Keep track of values of each piece
    values = {
        "Q": 9,
        "R": 5,
        "B": 3,
        "N": 3,
        "p": 1,
        "promotion": 8,
        "K": 10000,
    }

    def __init__(self) -> None:

        # Generates a list of list which represents the initial board state
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", ""],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]

        # Keeps track of who's turn to move
        self.white_move = True

        # List to keep track of moves made
        self.move_log = []

        # Dimensions of a board
        self.dimensions = 8

        # Keep track of the kings' location
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)

        # Other useful states to hold in memory
        self.in_check = False
        self.pins = []
        self.checks = []

        # Keep track of coordinate of square where en passant is possible
        self.en_passant_square = ()

        # Keep track of castling rights
        self.current_castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [self.current_castle_rights.copy()]

        # Keep track of both side's materials, both sides start off with 39 points of material
        self.white_material = self.black_material = 39
        
        # Keeps track of the draw status of the board
        self.draw_log = [DrawChecker(self.board, 0)]

    def make_move(self, move, promotion_type: str = "") -> None:
        """
        Makes a move given a move class, note that if it is a promotion, the proper input should be given

        Args:
            move (Move): A Move class of the move to be made
        """

        # Keep track of if the 50 move rule has been reset
        fifty_move_rule_reset = False
        
        # Update location of pieces
        self.board[move.start_row][move.start_column] = ""
        self.board[move.end_row][move.end_column] = move.piece_moved

        self.move_log.append(move)

        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_column)

        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_column)

        # If a piece was captured
        if move.piece_captured:
            
            fifty_move_rule_reset = True

            # Get the value of the piece and subtract it from the player
            value = self.values[move.piece_captured[1]]

            if self.white_move:
                self.black_material -= value

            else:
                self.white_material -= value

        if move.piece_moved[1] == "p":
            fifty_move_rule_reset = True

        # If it is a pawn promotion
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_column] = (
                move.piece_moved[0] + promotion_type
            )

            # Update the material count
            # TODO: Update to ensure that other possible promotion types are accounted for
            if self.white_move:
                self.white_material += 8

            else:
                self.black_material += 8

        # En passant
        elif move.is_en_passant:

            # Capture the pawn
            self.board[move.start_row][move.end_column] = ""

        # Check and update for squares where en passant is possible
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:

            self.en_passant_square = (
                (move.start_row + move.end_row) // 2,
                move.end_column,
            )

        # Else make sure no en passant is possible
        else:
            self.en_passant_square = ()

        # If it is a king side castle, moves rook to new square
        if move.king_side_castle:
            self.board[move.end_row][move.end_column - 1] = self.board[move.end_row][
                move.end_column + 1
            ]
            self.board[move.end_row][move.end_column + 1] = ""

        # Else it is a queen side castle, do the same except for the queen side
        elif move.queen_side_castle:
            self.board[move.end_row][move.end_column + 1] = self.board[move.end_row][
                move.end_column - 2
            ]
            self.board[move.end_row][move.end_column - 2] = ""

        # If either side could still castle, update castling rights
        if self.current_castle_rights.can_castle():
            self.current_castle_rights.update_castle_rights(move)

        self.castle_rights_log.append(self.current_castle_rights.copy())

        self.white_move = not self.white_move
        
        if move.piece_moved[1] == "p":
            fifty_move_rule_reset = True
        
        new_draw_checker = copy.deepcopy(self.draw_log[-1])
        new_draw_checker.update_checker(self.board, 1)
        
        if fifty_move_rule_reset:
            new_draw_checker.move_counter = 0
        
        self.draw_log.append(new_draw_checker)
        

    def undo_move(self) -> None:
        """
        Undoes the last move
        """

        if self.move_log:
            move = self.move_log.pop()

            self.board[move.start_row][move.start_column] = move.piece_moved
            self.board[move.end_row][move.end_column] = move.piece_captured

            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_column)

            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_column)

            self.white_move = not self.white_move

            # Undo en passant
            if move.is_en_passant:
                self.board[move.end_row][move.end_column] = ""
                self.board[move.start_row][move.end_column] = move.piece_captured
                self.en_passant_square = (move.end_row, move.end_column)

            # Undo castling rights
            self.castle_rights_log.pop()
            self.current_castle_rights = copy.deepcopy(self.castle_rights_log[-1])

            # Undo castle move
            # If it is a king side castle, moves rook to new square
            if move.king_side_castle:
                self.board[move.end_row][move.end_column + 1] = self.board[
                    move.end_row
                ][move.end_column - 1]
                self.board[move.end_row][move.end_column - 1] = ""

            # Else it is a queen side castle, do the same except for the queen side
            elif move.queen_side_castle:
                self.board[move.end_row][move.end_column - 2] = self.board[
                    move.end_row
                ][move.end_column + 1]
                self.board[move.end_row][move.end_column + 1] = ""

            # Undoing the material count
            if move.piece_captured:
                value = self.values[move.piece_captured[1]]

                if self.white_move:
                    self.black_material += value

                else:
                    self.white_material += value

            if move.is_pawn_promotion:
                if self.white_move:
                    self.white_material -= 8

                else:
                    self.black_material -= 8
                    
            # Removes the last draw checker
            self.draw_log.pop()
            

    def get_valid_moves(self) -> list:
        """
        Returns all the valid moves in the current game state

        Returns:
            list: list of all valid moves
        """

        moves = []

        self.in_check, self.pins, self.checks = self.check_for_pins_checks()

        # Getting the location of the king
        if self.white_move:
            king_row, king_column = self.white_king_location

        else:
            king_row, king_column = self.black_king_location

        if self.in_check:

            # If there is only 1 check, we must block the check, capture the piece, or move the king
            if len(self.checks) == 1:
                moves = self.get_all_moves()

                # Check if the move can block the check
                check = self.checks[0]
                piece_checking = self.board[check[0]][check[1]]

                valid_squares = []

                # If it is a knight, must move the king or capture the knight
                if piece_checking[1] == "N":
                    valid_squares.append((check[0], check[1]))

                # Else, it can block the check where piece can move from king to attacking piece
                else:
                    for i in range(1, 8):

                        square = (king_row + check[2] * i, king_column + check[3] * i)

                        if (
                            0 <= square[0] < self.dimensions
                            and 0 <= square[1] < self.dimensions
                        ):
                            valid_squares.append(square)
                        else:
                            break

                        # If it is the square where the piece can be captured
                        if square == (check[0], check[1]):
                            break

                # Get rid of moves that don't block the check or move the king
                for move in moves.copy():

                    if move.piece_moved[1] != "K":

                        if not (move.end_row, move.end_column) in valid_squares:
                            moves.remove(move)

            # Else it is double or triple check, and the king has to move
            else:
                self.get_king_moves(king_row, king_column, moves)

        # If king not in check, all moves are valid moves except for pins
        else:
            moves = self.get_all_moves()

        return moves

    def check_for_pins_checks(self) -> tuple[bool, list, list]:
        """
        Returns a tuple for if the king is in check, the pins and the checks that are in the game state (if any)

        Returns:
            tuple: a tuple of (in check, list of pins, list of checks)
        """

        pins = []
        checks = []
        in_check = False

        if self.white_move:
            opponent_colour, turn_colour = "b", "w"
            start_row, start_column = self.white_king_location

        else:
            opponent_colour, turn_colour = "w", "b"
            start_row, start_column = self.black_king_location

        # Check for all directions, i.e. movement of queen
        directions = (
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
            (-1, 0),
            (0, -1),
            (1, 0),
            (0, 1),
        )

        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()

            # For each direction, move and check for all possible squares in direction
            for i in range(1, 8):
                counter_row = start_row + direction[0] * i
                counter_column = start_column + direction[1] * i

                # To make sure it is within board
                if 0 <= counter_row < 8 and 0 <= counter_column < 8:

                    # If there is a piece on the specific square
                    if end_piece := self.board[counter_row][counter_column]:

                        # If it is an ally piece
                        if end_piece[0] == turn_colour and end_piece[1] != "K":

                            # If it is the first ally piece, it may be pinned, otherwise no pins
                            if not possible_pin:
                                possible_pin = (
                                    counter_row,
                                    counter_column,
                                    direction[0],
                                    direction[1],
                                )

                            else:
                                break

                        # Else if it is an opponent's piece
                        elif end_piece[0] == opponent_colour:
                            type = end_piece[1]

                            # Checking if a piece can put the king in check given its direction
                            if (
                                (0 <= j < 4 and type == "B")
                                or (4 <= j < 8 and type == "R")
                                or (type == "Q")
                                or (i == 1 and type == "K")
                                or (
                                    i == 1
                                    and type == "p"
                                    and (
                                        (opponent_colour == "w" and j in (2, 3))
                                        or (opponent_colour == "b" and j in (0, 1))
                                    )
                                )
                            ):

                                # If no piece is blocking sight, it is in check
                                if not possible_pin:
                                    in_check = True
                                    checks.append(
                                        (
                                            counter_row,
                                            counter_column,
                                            direction[0],
                                            direction[1],
                                        )
                                    )

                                    break

                                # Else if there is a piece, it is a pin
                                else:
                                    pins.append(possible_pin)

                                    break

                            else:
                                break

                else:
                    break

        # Check for knight checks
        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )

        for move in knight_moves:
            counter_row = start_row + move[0]
            counter_column = start_column + move[1]

            # To make sure it is within the board
            if 0 <= counter_row < 8 and 0 <= counter_column < 8:
                if piece := self.board[counter_row][counter_column]:

                    # If it is a knight
                    if piece[0] == opponent_colour and piece[1] == "N":
                        in_check = True
                        checks.append((counter_row, counter_column, move[0], move[1]))

        return in_check, pins, checks

    def king_in_check(self) -> bool:
        """Returns bool of if the current turn's player is in check"""

        if self.white_move:
            return self.square_attacked(self.white_king_location)

        else:
            return self.square_attacked(self.black_king_location)

    def square_attacked(self, square: tuple) -> bool:
        """Returns bool of if the square is under attack by opponent"""

        # Switch turns to get the opponents turns
        self.white_move = not self.white_move
        opponents_moves = self.get_all_moves(True)
        self.white_move = not self.white_move

        for move in opponents_moves:

            # If the opponent can attack the square
            if move.end_row == square[0] and move.end_column == square[1]:
                return True

        return False

    def get_all_moves(self, for_square_under_attack: bool = False) -> list:
        """
        Returns all moves in current game state (without considering checks)

        Args:
            for_square_under_attack (bool): if the current function is being called by that function

        Returns:
            list: list of all moves
        """

        moves = []

        # Setting a variable to hold who's turn it is
        turn = "w" if self.white_move else "b"

        # Iterate through all the pieces to determine which pieces belong to the player's turn
        for row in range(self.dimensions):
            for column in range(self.dimensions):

                if colour_piece := self.board[row][column]:

                    if turn == colour_piece[0]:

                        match colour_piece[1]:

                            # How each piece moves
                            case "p":
                                self.get_pawn_moves(row, column, moves)

                            case "R":
                                self.get_rook_moves(row, column, moves)

                            case "B":
                                self.get_bishop_moves(row, column, moves)

                            case "N":
                                self.get_knight_moves(row, column, moves)

                            case "Q":
                                self.get_queen_moves(row, column, moves)

                            case "K":
                                self.get_king_moves(row, column, moves)

                                if not for_square_under_attack:
                                    self.get_castle_moves(row, column, moves, turn)

        return moves

    def get_pawn_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all the pawn moves"""

        # For if the piece is pinned
        piece_pinned = False
        pin_direction = ()

        for pin in self.pins.copy():
            if pin[0] == row and pin[1] == column:
                piece_pinned = True
                pin_direction = (pin[2], pin[3])

                self.pins.remove(pin)

                # A piece can only be pinned from one direction
                break

        # For white pawns
        if self.white_move:

            # Keep rack of king location due to weird en passant bug
            king_row, king_column = self.white_king_location

            # Check if square in front is empty and not pinned (but moving in direction of pin is fine)
            if not self.board[row - 1][column]:
                if not piece_pinned or pin_direction == (-1, 0):
                    moves.append(Move((row, column), (row - 1, column), self.board))

                    # If it is on starting row, check if the 2nd square in front is empty
                    if row == 6:
                        if not self.board[row - 2][column]:
                            moves.append(
                                Move((row, column), (row - 2, column), self.board)
                            )

            # Check for captures

            # If can capture to left
            if column - 1 >= 0:

                # Check if piece that can be captured is black
                if self.board[row - 1][column - 1].startswith("b"):

                    # Checking for pins
                    if not piece_pinned or pin_direction == (-1, -1):
                        moves.append(
                            Move((row, column), (row - 1, column - 1), self.board)
                        )

                # If it is empty, check if it is the square where en passant is possible
                elif (row - 1, column - 1) == self.en_passant_square:

                    if not piece_pinned or pin_direction == (-1, -1):

                        # Fixing weird en passant bug
                        attacking_piece = blocking_piece = None
                        if king_row == row and row == 3:
                            if king_column < column:
                                inside_range = range(king_column + 1, column - 1)
                                outside_range = range(column + 1, 8)

                            else:
                                inside_range = range(king_column - 1, column, -1)
                                outside_range = range(column - 2, -1, -1)

                            for i in inside_range:
                                if piece := self.board[row][i]:
                                    blocking_piece = piece

                            for i in outside_range:
                                square = self.board[row][i]
                                if square.startswith("b"):
                                    if square[1] == "R" or square[1] == "Q":
                                        attacking_piece = square[1]

                                elif square:
                                    blocking_piece = square

                        if not attacking_piece or blocking_piece:
                            moves.append(
                                Move(
                                    (row, column),
                                    (row - 1, column - 1),
                                    self.board,
                                    True,
                                )
                            )

            # If can capture to right
            if column + 1 < self.dimensions:

                # Check if piece that can be captured is black
                if self.board[row - 1][column + 1].startswith("b"):

                    # Check for any pins
                    if not piece_pinned or pin_direction == (-1, 1):
                        moves.append(
                            Move((row, column), (row - 1, column + 1), self.board)
                        )

                elif (row - 1, column + 1) == self.en_passant_square:
                    if not piece_pinned or pin_direction == (-1, 1):

                        # Fixing weird en passant bug
                        attacking_piece = blocking_piece = None
                        if king_row == row and row == 3:
                            if king_column < column:
                                inside_range = range(king_column + 1, column)
                                outside_range = range(column + 2, 8)

                            else:
                                inside_range = range(king_column - 1, column + 1, -1)
                                outside_range = range(column - 1, -1, -1)

                            for i in inside_range:
                                if piece := self.board[row][i]:
                                    blocking_piece = piece

                            for i in outside_range:
                                square = self.board[row][i]
                                if square.startswith("b"):
                                    if square[1] == "R" or square[1] == "Q":
                                        attacking_piece = square[1]

                                elif square:
                                    blocking_piece = square

                        if not attacking_piece or blocking_piece:
                            moves.append(
                                Move(
                                    (row, column),
                                    (row - 1, column + 1),
                                    self.board,
                                    True,
                                )
                            )

        # For black pawns
        else:

            # Get king square to fix weird en passant bug
            king_row, king_column = self.black_king_location

            if not self.board[row + 1][column]:

                # Check for if piece is pinned/ if it can move in direction of pin
                if not piece_pinned or pin_direction == (1, 0):
                    moves.append(Move((row, column), (row + 1, column), self.board))

                    if row == 1:
                        if not self.board[row + 2][column]:
                            moves.append(
                                Move((row, column), (row + 2, column), self.board)
                            )

            if column - 1 >= 0:

                if self.board[row + 1][column - 1].startswith("w"):
                    if not piece_pinned or pin_direction == (1, -1):
                        moves.append(
                            Move((row, column), (row + 1, column - 1), self.board)
                        )

                elif (row + 1, column - 1) == self.en_passant_square:
                    if not piece_pinned or pin_direction == (1, -1):

                        # Fixing weird en passant bug
                        attacking_piece = blocking_piece = None
                        if king_row == row and row == 4:
                            if king_column < column:
                                inside_range = range(king_column + 1, column - 1)
                                outside_range = range(column + 1, 8)

                            else:
                                inside_range = range(king_column - 1, column, -1)
                                outside_range = range(column - 2, -1, -1)

                            for i in inside_range:
                                if piece := self.board[row][i]:
                                    blocking_piece = piece

                            for i in outside_range:
                                square = self.board[row][i]
                                if square.startswith("w"):
                                    if square[1] == "R" or square[1] == "Q":
                                        attacking_piece = square[1]

                                elif square:
                                    blocking_piece = square

                        if not attacking_piece or blocking_piece:
                            moves.append(
                                Move(
                                    (row, column),
                                    (row + 1, column - 1),
                                    self.board,
                                    True,
                                )
                            )

            if column + 1 < self.dimensions:

                if self.board[row + 1][column + 1].startswith("w"):
                    if not piece_pinned or pin_direction == (1, 1):
                        moves.append(
                            Move((row, column), (row + 1, column + 1), self.board)
                        )

                elif (row + 1, column + 1) == self.en_passant_square:
                    if not piece_pinned or pin_direction == (1, 1):

                        # Fixing weird en passant bug
                        attacking_piece = blocking_piece = None
                        if king_row == row and row == 4:
                            if king_column < column:
                                inside_range = range(king_column + 1, column)
                                outside_range = range(column + 2, 8)

                            else:
                                inside_range = range(king_column - 1, column + 1, -1)
                                outside_range = range(column - 1, -1, -1)

                            for i in inside_range:
                                if piece := self.board[row][i]:
                                    blocking_piece = piece

                            for i in outside_range:
                                square = self.board[row][i]
                                if square.startswith("w"):
                                    if square[1] == "R" or square[1] == "Q":
                                        attacking_piece = square[1]

                                elif square:
                                    blocking_piece = square

                        if not attacking_piece or blocking_piece:
                            moves.append(
                                Move(
                                    (row, column),
                                    (row + 1, column + 1),
                                    self.board,
                                    True,
                                )
                            )

    def get_rook_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all of the rook moves"""

        piece_pinned = False
        pin_direction = ()

        for pin in self.pins.copy():
            if pin[0] == row and pin[1] == column:
                piece_pinned = True
                pin_direction = (pin[2], pin[3])

                # If it is not the queen as you also need to check for bishop diagonal for queen
                if self.board[row][column][1] != "Q":
                    self.pins.remove(pin)

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        opponent = "b" if self.white_move else "w"

        for direction in directions:
            for i in range(1, 8):

                # Get the maximum the rook can move
                counter_row = row + direction[0] * i
                counter_column = column + direction[1] * i

                # If it is still in the board
                if (
                    0 <= counter_row < self.dimensions
                    and 0 <= counter_column < self.dimensions
                ):

                    # If piece is not pinned/ move in direction of pin
                    if (
                        not piece_pinned
                        or pin_direction == direction
                        or pin_direction == (-direction[0], -direction[1])
                    ):

                        # If there is a piece
                        if piece := self.board[counter_row][counter_column]:

                            # If it is an enemy piece
                            if piece.startswith(opponent):
                                moves.append(
                                    Move(
                                        (row, column),
                                        (counter_row, counter_column),
                                        self.board,
                                    )
                                )
                            break

                        # Else if it is an empty square
                        else:
                            moves.append(
                                Move(
                                    (row, column),
                                    (counter_row, counter_column),
                                    self.board,
                                )
                            )

                else:
                    break

    def get_bishop_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all of the bishop moves"""

        # To check for pinned pieces
        piece_pinned = False
        pin_direction = ()

        for pin in self.pins.copy():
            if pin[0] == row and pin[1] == column:
                piece_pinned = True
                pin_direction = (pin[2], pin[3])

                self.pins.remove(pin)

                break

        directions = ((-1, -1), (1, -1), (1, 1), (-1, 1))
        opponent = "b" if self.white_move else "w"

        for direction in directions:
            for i in range(1, 8):

                # Get the maximum the rook bishop move
                counter_row = row + direction[0] * i
                counter_column = column + direction[1] * i

                # If it is still in the board
                if (
                    0 <= counter_row < self.dimensions
                    and 0 <= counter_column < self.dimensions
                ):

                    # If not pinned or in direction of pin
                    if (
                        not piece_pinned
                        or pin_direction == direction
                        or pin_direction == (-direction[0], -direction[1])
                    ):

                        # If there is a piece
                        if piece := self.board[counter_row][counter_column]:

                            # If it is an enemy piece
                            if piece.startswith(opponent):
                                moves.append(
                                    Move(
                                        (row, column),
                                        (counter_row, counter_column),
                                        self.board,
                                    )
                                )
                            break

                        # Else if it is an empty square
                        else:
                            moves.append(
                                Move(
                                    (row, column),
                                    (counter_row, counter_column),
                                    self.board,
                                )
                            )

                else:
                    break

    def get_knight_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all of the knight moves"""

        # Check for if piece is pinned (direction doesn't matter for knight)
        piece_pinned = False

        for pin in self.pins.copy():
            if pin[0] == row and pin[1] == column:
                piece_pinned = True

                self.pins.remove(pin)
                break

        # All the moves that a knight can make from its position
        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )
        opponent = "b" if self.white_move else "w"

        for move in knight_moves:
            move_row = row + move[0]
            move_column = column + move[1]

            if 0 <= move_row < self.dimensions and 0 <= move_column < self.dimensions:

                # If it is not pinned
                if not piece_pinned:

                    # If there is a piece
                    if piece := self.board[move_row][move_column]:
                        if piece.startswith(opponent):
                            moves.append(
                                Move((row, column), (move_row, move_column), self.board)
                            )

                    # Else if it is an empty square
                    else:
                        moves.append(
                            Move((row, column), (move_row, move_column), self.board)
                        )

    def get_queen_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all of the queen moves"""

        self.get_rook_moves(row, column, moves)
        self.get_bishop_moves(row, column, moves)

    def get_king_moves(self, row: int, column: int, moves: list) -> None:
        """Appends to list all of the king moves"""

        # All the moves that a king can make from its position
        king_moves = (
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, 0),
            (1, -1),
            (1, 1),
        )
        turn = "w" if self.white_move else "b"

        for move in king_moves:
            move_row = row + move[0]
            move_column = column + move[1]

            if 0 <= move_row < self.dimensions and 0 <= move_column < self.dimensions:

                # If it is not self's piece (i.e. either empty or opponent piece)
                if not self.board[move_row][move_column].startswith(turn):

                    # Place king on new square and check for checks
                    if turn == "w":
                        self.white_king_location = (move_row, move_column)
                    else:
                        self.black_king_location = (move_row, move_column)

                    in_check, _, checks = self.check_for_pins_checks()

                    if not in_check:
                        moves.append(
                            Move((row, column), (move_row, move_column), self.board)
                        )

                    # Return king back to original position
                    if turn == "w":
                        self.white_king_location = (row, column)
                    else:
                        self.black_king_location = (row, column)

    def get_castle_moves(
        self, row: int, column: int, moves: list, turn_colour: str
    ) -> None:
        """Appends to list all of the castle moves"""

        def get_king_castle_moves() -> Move:
            """Returns a Move class of the king side castling move"""
            if not self.board[row][column + 1] and not self.board[row][column + 2]:
                if not self.square_attacked(
                    (row, column + 1)
                ) and not self.square_attacked((row, column + 2)):
                    moves.append(
                        Move(
                            (row, column), (row, column + 2), self.board, is_castle=True
                        )
                    )

        def get_queen_castle_moves() -> Move:
            if (
                not self.board[row][column - 1]
                and not self.board[row][column - 2]
                and not self.board[row][column - 3]
            ):
                if not self.square_attacked(
                    (row, column - 1)
                ) and not self.square_attacked((row, column - 2)):
                    moves.append(
                        Move(
                            (row, column), (row, column - 2), self.board, is_castle=True
                        )
                    )

        # If king is in check, it can't castle
        if self.in_check:
            return

        if (self.white_move and self.current_castle_rights.white_king_side) or (
            not self.white_move and self.current_castle_rights.black_king_side
        ):
            get_king_castle_moves()

        if (self.white_move and self.current_castle_rights.white_queen_side) or (
            not self.white_move and self.current_castle_rights.black_queen_side
        ):
            get_queen_castle_moves()


class Move:

    # Dict to map standard chess notation to the list of lists and vice versa
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4, "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}

    files_to_columns = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}
    columns_to_files = {v: k for k, v in files_to_columns.items()}

    def __init__(
        self,
        start: tuple,
        end: tuple,
        board: GameState,
        is_en_passant: bool = False,
        is_castle: bool = False,
    ) -> None:
        """
        Generates a chess move which keeps track of the move to be made, as well as
        the piece that is being moved and the piece that is being captured

        Args:
            start (tuple): row, column of initial starting square
            end (tuple): row, column of square for the piece to be moved to
            board (GameState.board): The current board
            is_en_passant (bool): Whether or not the move is an en passant
            is_castle (bool): Whether the current move is a castling move
        """

        # Uncouples the tuple
        self.start_row, self.start_column = self.start = start
        self.end_row, self.end_column = self.end = end

        # Stores the piece moved and piece captured (if any)
        self.piece_moved = board[self.start_row][self.start_column]
        self.piece_captured = board[self.end_row][self.end_column]

        # A unique identifier to make it easier for comparing
        self.move = [start, end]

        # To keep track of if it is a pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wp" and self.end_row == 0) or (
            self.piece_moved == "bp" and self.end_row == 7
        )

        # Keep track of if move is en passant
        self.is_en_passant = is_en_passant

        if is_en_passant:
            self.piece_captured = board[self.start_row][self.end_column]

        # Keep track of if current move is a castling move
        self.is_castle = is_castle

        if self.is_castle:

            # Take down if it is a king side castle
            self.king_side_castle = (
                True if (self.end_column - self.start_column == 2) else False
            )

            # Take down if it is queen side castle (can only be queen side if it is a castling move and it is not king side)
            self.queen_side_castle = not self.king_side_castle

        # If it is not a castling move, it cannot be either castle
        else:
            self.king_side_castle = self.queen_side_castle = False

    def __eq__(self, other):
        if isinstance(other, Move):
            return self.move == other.move

    def get_chess_notation(self) -> str:
        """
        Returns a string of chess notation of square piece moved from to moved to

        Returns:
            str: the chess notation of the move
        """

        if self.king_side_castle:
            return "O-O"

        if self.queen_side_castle:
            return "O-O-O"

        return self.get_rank_file(
            self.start_row, self.start_column
        ) + self.get_rank_file(self.end_row, self.end_column)

    def get_pgn_chess_notation(self) -> str:
        """
        Returns a string of the pgn notation of a chess notation of the move.
        Does not support promotions, checks, mates, and remove ambiguity

        Returns:
            str: the chess notation
        """

        if self.king_side_castle:
            return "O-O"

        if self.queen_side_castle:
            return "O-O-O"

        piece_captured = ""

        end_square = self.get_rank_file(self.end_row, self.end_column)

        if self.piece_captured:
            piece_captured = "x"

        if self.piece_moved[1] == "p":
            if self.piece_captured:
                return (
                    self.columns_to_files[self.start_column]
                    + piece_captured
                    + end_square
                )

            return self.get_rank_file(self.end_row, self.end_column)

        else:
            return self.piece_moved[1] + piece_captured + end_square

    def get_rank_file(self, row: int, column: int) -> str:
        """
        Returns the chess notation of the required row and column

        Args:
            row (int): Row in chess board
            column (int): Column in chess board

        Returns:
            str: Chess notation of the coordinate
        """
        return self.columns_to_files[column] + self.rows_to_ranks[row]

    def __str__(self):
        return self.get_chess_notation()


class CastleRights:

    def __init__(
        self,
        white_king_side: bool,
        black_king_side: bool,
        white_queen_side: bool,
        black_queen_side: bool,
    ):
        """
        Creates an object which holds information about either side's castling rights

        Args:
            white_king_side (bool): Whether white can still castle king side
            black_king_side (bool): Whether black can still castle king side
            white_queen_side (bool): Whether white can still castle queen side
            black_queen_side (bool): Whether black can still castle queen side
        """

        self.white_king_side = white_king_side
        self.black_king_side = black_king_side
        self.white_queen_side = white_queen_side
        self.black_queen_side = black_queen_side

    def update_castle_rights(self, move) -> None:
        """
        Update castle rights of either colour given a move

        Args:
            move (Move): Any chess move that was made using the Move class
        """

        # If either king moves, either side loses castling rights
        if move.piece_moved == "wK":
            self.white_king_side = False
            self.white_queen_side = False

        elif move.piece_moved == "bK":
            self.black_king_side = False
            self.black_queen_side = False

        # If white's king side rook is captured or moved, white can no longer castle king side
        elif move.start == (7, 7) or move.end == (7, 7):
            self.white_king_side = False

        # If white's queen side rook is captured of moved, white can no longer castle queen side
        elif move.start == (7, 0) or move.end == (7, 0):
            self.white_queen_side = False

        # Applying the same logic for black
        elif move.start == (0, 7) or move.end == (0, 7):
            self.black_king_side = False

        elif move.start == (0, 0) or move.end == (0, 0):
            self.black_queen_side = False

    def copy(self):
        """Returns a copy of the current object"""

        return CastleRights(
            self.white_king_side,
            self.black_king_side,
            self.white_queen_side,
            self.black_queen_side,
        )

    def can_castle(self) -> bool:
        """Returns a bool based on if either side can still castle"""

        return (
            self.white_king_side
            or self.black_king_side
            or self.white_queen_side
            or self.black_queen_side
        )

    def colour_can_castle(self: str, turn: str) -> bool:
        """Returns a bool based on if the turn/ colour given can still castle"""

        if turn == "w":
            return self.white_king_side or self.white_queen_side

        elif turn == "b":
            return self.black_king_side or self.black_queen_side

        else:
            raise ValueError("Incorrect turn colour given")

    def __str__(self):
        return f"White: {self.white_king_side, self.white_queen_side}, Black: {self.black_king_side, self.black_queen_side}"


class DrawChecker:
    """
    Keeps track of if the game state is a draw
    """
    
    def __init__(self, board: list[list[str]], move_counter: int = 0) -> None:
        
        self.past_boards ={tuple(tuple(row) for row in board): 1}
        
        self.move_counter = move_counter
        
    def update_checker(self, board: list[list[str]], move_counter: int) -> None:
        
        self.past_boards[tuple(tuple(row) for row in board)] = self.past_boards.get(tuple(tuple(row) for row in board), 0) + 1

        self.move_counter += move_counter
    
    def check_for_draw(self) -> bool:
        
        for count in self.past_boards.values():
            if count >= 3:
                return True
            
        if self.move_counter == 100:
            return True
        
        return False