import game
import minimax
from carlo_monte import CarloMontePlayer

HUMAN_CHAR = 'O'
AI_CHAR = 'X'

AMOUNT_IN_A_ROW = 4
ROWS = 6
COLS = 7


class FourInRowHumanPlayer(game.Player):
    def __init__(self, char):
        self.m_char = char

    def get_char(self):
        return self.m_char

    def get_move(self, state):
        print('Enter your move: ', end='')
        while True:
            try:
                ret = int(input()) - 1
                if 0 <= ret < COLS:
                    return ret
            except ValueError:
                print('Illegal move. ', end='')
            print(f'Enter your move (1-{COLS}): ', end='')

    def notify_bad_move(self):
        print('Illegal move.')

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class FourInRowAiPlayer(CarloMontePlayer):
    def __init__(self, char):
        super().__init__(5000)
        self.m_char = char

    def get_char(self):
        return self.m_char

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class FourInRowState(game.GameState):
    def __init__(self, cells, players, amount_per_col=None, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.last_move = last_move
        self.cells = cells
        self.rows = len(self.cells)
        self.cols = len(self.cells[0])
        self.amount_per_col = amount_per_col if amount_per_col else [0] * self.cols

    def notify_move(self):
        print(f'Player {self.last_move[0].get_char()} played at column {self.last_move[1] + 1}.')

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

    def get_winner(self):
        if self.last_move:
            last_player = self.last_move[0]
            col = self.last_move[1]
            row = self.amount_per_col[col] - 1

            for row_dir, col_dir in (1, 0), (0, 1), (1, 1), (1, -1):
                first = self.count_in_direction(row, col, row_dir, col_dir)
                second = self.count_in_direction(row, col, -row_dir, -col_dir)
                if first + second >= AMOUNT_IN_A_ROW + 1:  # The last move is counter twice
                    return last_player

        return None

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

    def get_moves(self):
        return (i for i, amount in enumerate(self.amount_per_col) if amount < self.rows)

    def move(self, move: int):
        if 0 <= move < self.cols and self.amount_per_col[move] < self.rows:
            col = move
            row = self.amount_per_col[col]
            new_cells = [r if index != row else r[::] for index, r in
                         enumerate(self.cells)]  # copy only the row that is about to change
            new_cells[row][col] = self.get_curr_player().get_char()
            new_amount_per_col = self.amount_per_col[::]
            new_amount_per_col[col] += 1
            last_move = (self.get_curr_player(), move)
            return FourInRowState(cells=new_cells,
                                  players=self.m_players,
                                  amount_per_col=new_amount_per_col,
                                  last_move=last_move,
                                  player_index=self._next_player_index())

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.cells == other.cells

    def __str__(self):
        ret = '|' + "-" * (self.cols * 4 - 1) + '|\n'
        for row_index, row in enumerate(self.cells[::-1]):
            ret += '| '
            for col_index, cell in enumerate(row):
                ret += cell if cell != ' ' else ' '  # str(i + 1)
                if col_index < self.cols - 1:
                    ret += ' | '

            ret += f' |\n|{"-" * (self.cols * 4 - 1)}|\n'

        ret += '  ' + '   '.join(str(i + 1) for i in range(self.cols))

        return ret + '\n'


def main():
    board = [[' ' for _ in range(COLS)] for _ in range(ROWS)]
    human_player = FourInRowHumanPlayer(HUMAN_CHAR)
    ai_player = FourInRowAiPlayer(AI_CHAR)
    five_in_row_game = game.Game(FourInRowState(board, [human_player, ai_player]))

    for state in five_in_row_game.play():
        print(state)

    winner = five_in_row_game.get_winner()
    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
