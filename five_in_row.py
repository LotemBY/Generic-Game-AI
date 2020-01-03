from string import ascii_uppercase

import game
import minimax
from carlo_monte import CarloMontePlayer

HUMAN_CHAR = 'O'
AI_CHAR = 'X'

AMOUNT_IN_A_ROW = 5
ROWS = 9
COLS = 9


class FiveInRowHumanPlayer(game.Player):
    def __init__(self, char):
        self.m_char = char

    def get_char(self):
        return self.m_char

    def get_move(self, state):
        print('Enter your move: ', end='')
        while True:
            try:
                inputs = input().split(' ')
                if len(inputs) == 2:
                    row = int(inputs[0]) - 1
                    col = ascii_uppercase.index(inputs[1])
                    return row, col
            except ValueError:
                print('Illegal move. ', end='')
            print(f'Enter your move (Row: 1-{ROWS}, Col: A-{ascii_uppercase[COLS - 1]}): ', end='')

    def notify_bad_move(self):
        print('Illegal move.')

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class FiveInRowAiPlayer(CarloMontePlayer):  # minimax.MinimaxPlayer):
    def __init__(self, char):
        super().__init__(5000)
        self.m_char = char

    def get_char(self):
        return self.m_char

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class FiveInRowState(game.GameState):
    def __init__(self, cells, players, prev_moves=None, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.last_move = last_move
        self.cells = cells
        self.rows = len(self.cells)
        self.cols = len(self.cells[0])

        self.moves = prev_moves[::] if prev_moves is not None else [(self.rows // 2, self.cols // 2)]
        # sort by distance to the middle
        # self.moves.sort(key=lambda move: abs(move[0] - self.rows / 2) + abs(move[1] - self.cols / 2))
        if last_move:
            _last_player, last_move_cell = last_move
            try:
                self.moves.remove(last_move_cell)
            except ValueError:
                # Its not in the list
                pass

            self.moves = [move for move in self.moves_in_radius(last_move_cell[0], last_move_cell[1], 1)
                          if move not in self.moves] + self.moves

            assert len(self.moves) == len(set(self.moves))

    def notify_move(self):
        print(f'Player {self.last_move[0].get_char()} '
              f'played at cell ({self.last_move[1][0] + 1}, {ascii_uppercase[self.last_move[1][1]]}).')

    def in_board(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def count_in_direction(self, row, col, row_dir, col_dir, for_eval=False):
        char = self.cells[row][col]
        if char == ' ':
            return 0

        last_row = row + row_dir * (AMOUNT_IN_A_ROW - 1)
        last_col = col + col_dir * (AMOUNT_IN_A_ROW - 1)
        if for_eval and not self.in_board(last_row, last_col):
            return 0

        counter = 1
        for i in range(1, AMOUNT_IN_A_ROW):
            if not for_eval and not self.in_board(row + row_dir * i, col + col_dir * i):
                return i

            curr = self.cells[row + row_dir * i][col + col_dir * i]
            if curr == char:
                counter += 1
            elif not for_eval or curr != ' ':
                return 0 if for_eval else i

        return counter

    def get_winner_char(self):
        for row in range(self.rows):
            for col in range(self.cols - AMOUNT_IN_A_ROW + 1):
                if self.count_in_direction(row, col, 0, 1) == AMOUNT_IN_A_ROW:
                    return self.cells[row][col]

        for row in range(self.rows - AMOUNT_IN_A_ROW + 1):
            for col in range(self.cols):
                if self.count_in_direction(row, col, 1, 0) == AMOUNT_IN_A_ROW:
                    return self.cells[row][col]

        for row in range(self.rows - AMOUNT_IN_A_ROW + 1):
            for col in range(self.cols - AMOUNT_IN_A_ROW + 1):
                if self.count_in_direction(row, col, 1, 1) == AMOUNT_IN_A_ROW:
                    return self.cells[row][col]

        for row in range(self.rows - AMOUNT_IN_A_ROW + 1):
            for col in range(AMOUNT_IN_A_ROW - 1, self.cols):
                if self.count_in_direction(row, col, 1, -1) == AMOUNT_IN_A_ROW:
                    return self.cells[row][col]

        return None

    def get_winner(self):
        if self.last_move:
            last_player = self.last_move[0]
            row, col = self.last_move[1]

            for row_dir, col_dir in (1, 0), (0, 1), (1, 1), (1, -1):
                first = self.count_in_direction(row, col, row_dir, col_dir)
                second = self.count_in_direction(row, col, -row_dir, -col_dir)
                if first + second >= AMOUNT_IN_A_ROW + 1:  # The last move is counter twice
                    return last_player

        return None

        # winner_char = self.get_winner_char()
        # if winner_char is None:
        #     return None
        #
        # for player in self.m_players:
        #     if player.get_char() == winner_char:
        #         return player

    def eval_direction(self, rows_dir, cols_dir, rows_end, cols_end, rows_start=0, cols_start=0):
        score = 0

        for row in range(rows_start, rows_end):
            for col in range(cols_start, cols_end):
                char = self.cells[row][col]
                if char != ' ':
                    curr_score = 5 ** self.count_in_direction(row, col, rows_dir, cols_dir, True)
                    curr_score = curr_score if char == AI_CHAR else -curr_score
                    # print(f'({row}, {col}) in direction {rows_dir}, {cols_dir} is {curr_score}')
                    score += curr_score

        return score

    def eval(self):
        winner = self.get_winner()

        score = 0
        if winner is not None:
            score += minimax.INF if winner.get_char() == AI_CHAR else -minimax.INF

        score += self.eval_direction(0, 1, self.rows, self.cols - AMOUNT_IN_A_ROW + 1)
        score += self.eval_direction(1, 0, self.rows - AMOUNT_IN_A_ROW + 1, self.cols)
        score += self.eval_direction(1, 1, self.rows - AMOUNT_IN_A_ROW + 1, self.cols - AMOUNT_IN_A_ROW + 1)
        score += self.eval_direction(1, -1, self.cols - AMOUNT_IN_A_ROW + 1, self.cols, cols_start=AMOUNT_IN_A_ROW - 1)

        return score

    def moves_in_radius(self, row, col, radius):
        for i in range(-radius, radius + 1):
            if self.in_board(row + i, 0):
                for j in range(-radius, radius + 1):
                    # if abs(i) + abs(j) <= radius:
                    if self.in_board(row + i, col + j) and self.cells[row + i][col + j] == ' ':
                        # print(f'Generated {row + i}, {col + j} from {row}, {col} - r = {radius}')
                        yield (row + i, col + j)

    def get_moves(self):
        return iter(self.moves)

        # cache = set()
        # if self.m_cells[self.rows // 2][self.cols // 2] == ' ':
        #     cache.add((self.rows // 2, self.cols // 2))
        #     yield self.rows // 2, self.cols // 2
        #
        # for row_index, row in enumerate(self.m_cells):
        #     for col_index, cell in enumerate(row):
        #         if cell != ' ':
        #             # print(f'Using {row_index}, {col_index} with radius 2.')
        #             for move in self.moves_in_radius(row_index, col_index, 1):
        #                 if move not in cache:
        #                     cache.add((self.rows // 2, self.cols // 2))
        #                     yield move

    def move(self, move: (int, int)):
        row, col = move
        if self.in_board(row, col) and self.cells[row][col] == ' ':
            new_cells = [r if index != row else r[::] for index, r in
                         enumerate(self.cells)]  # copy only the row that is about to change
            new_cells[row][col] = self.get_curr_player().get_char()
            last_move = (self.get_curr_player(), move)
            return FiveInRowState(cells=new_cells,
                                  players=self.m_players,
                                  prev_moves=self.moves,  # create a copy of the moves
                                  last_move=last_move,
                                  player_index=self._next_player_index())

        assert True, 'wtf'

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.cells == other.cells

    def __str__(self):
        ret = ' ' * 2 + '   '.join(ascii_uppercase[:COLS]) + '\n'
        for row_index, row in enumerate(self.cells):
            ret += f'{row_index + 1} '
            for col_index, cell in enumerate(row):
                ret += cell if cell != ' ' else ' '  # str(i + 1)
                if col_index < self.cols - 1:
                    ret += ' | '

            if row_index < self.rows - 1:
                ret += f'\n {"-" * (self.cols * 4 - 1)}\n'

        return ret + '\n'


def main():
    board = [[' ' for _ in range(COLS)] for _ in range(ROWS)]
    human_player = FiveInRowHumanPlayer(HUMAN_CHAR)
    ai_player = FiveInRowAiPlayer(AI_CHAR)
    five_in_row_game = game.Game(FiveInRowState(board, [human_player, ai_player]))

    for state in five_in_row_game.play():
        print(state)

    winner = five_in_row_game.get_winner()
    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
