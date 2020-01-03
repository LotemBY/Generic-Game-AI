import carlo_monte
import game
import minimax

HUMAN_CHAR = 'O'
AI_CHAR = 'X'


class HugeTicTacHumanPlayer(game.Player):
    def __init__(self, char):
        self.m_char = char

    def get_char(self):
        return self.m_char

    def get_move(self, state):
        move = None
        print('Enter your move: ', end='')
        while move is None:
            try:
                move = int(input())
            except ValueError:
                print('Enter your move (1-9): ', end='')

        return move - 1

    def notify_bad_move(self):
        print('Illegal move.')

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class HugeTicTacAiPlayer(carlo_monte.CarloMontePlayer):
    def __init__(self, char):
        super().__init__(3000)  # 9)
        self.m_char = char

    def get_char(self):
        return self.m_char


class HugeTicTacState(game.GameState):
    def __init__(self, sub_boards, players, main_board=None, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.last_move = last_move

        self.sub_boards = sub_boards
        self.main_board = main_board if main_board else [' '] * 9

        # Find the next sub-board
        self.current_sub_board = self.last_move[1] if last_move else 0

        # Try all 9 boards until a free one is found
        for i in range(10):
            if self.main_board[self.current_sub_board] == ' ' and \
                    any(cell == ' ' for cell in self.sub_boards[self.current_sub_board]):
                break
            else:
                self.current_sub_board += 1
                self.current_sub_board %= len(self.sub_boards)  # == 9
        else:
            self.current_sub_board = None

        self.winner_found = False

    def notify_move(self):
        print(f'Player {self.last_move[0].get_char()} '
              f'played at cell {self.last_move[1] + 1} '
              f'in sub-board {self.last_move[2] + 1}.')

    def get_winner_in_board(self, board):
        sets = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)]

        for a, b, c in sets:
            if board[a] != ' ' and \
                    board[a] == board[b] and board[a] == board[c]:
                return next((p for p in self.m_players if p.get_char() == board[a]), None)

        return None

    def get_winner(self):
        return self.get_winner_in_board(self.main_board)

    def eval(self):
        winner = self.get_winner()

        if winner is None:
            return 0

        return minimax.INF if winner.get_char() == AI_CHAR else -minimax.INF

    def get_moves(self):
        if self.current_sub_board is None:
            return iter([])  # No moves

        return (i for i, cell in enumerate(self.sub_boards[self.current_sub_board]) if cell == ' ')

    def move(self, move: int):
        if move in range(len(self.sub_boards[self.current_sub_board])) \
                and self.sub_boards[self.current_sub_board][move] == ' ':
            # copy only the sub-board that is about to change
            new_sub_boards = [sub_board if index != self.current_sub_board else sub_board[::]
                              for index, sub_board in enumerate(self.sub_boards)]
            new_sub_boards[self.current_sub_board][move] = self.get_curr_player().get_char()
            if self.get_winner_in_board(new_sub_boards[self.current_sub_board]):
                new_main_board = self.main_board[::]
                new_main_board[self.current_sub_board] = self.get_curr_player().get_char()
            else:
                new_main_board = self.main_board

            last_move = (self.get_curr_player(), move, self.current_sub_board)
            return HugeTicTacState(new_sub_boards, self.m_players, new_main_board, last_move, self._next_player_index())

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.sub_boards == other.sub_boards

    def __str__(self):
        ret = ''

        for row in range(9):
            for col in range(9):
                sub_board = (row // 3) * 3 + (col // 3)
                cell_index = (row % 3) * 3 + (col % 3)

                if self.main_board[sub_board] == ' ':
                    cell = self.sub_boards[sub_board][cell_index]

                    if cell != ' ':
                        cell_char = cell
                    elif sub_board == self.current_sub_board:
                        cell_char = str(cell_index + 1)
                    else:
                        cell_char = '.'
                else:
                    cell_char = ' ' if cell_index != 4 else self.main_board[sub_board]

                sep = '|' if col % 3 == 2 and col != 8 else ' '
                ret += cell_char + sep

            ret += '\n'
            if row % 3 == 2 and row != 8:
                ret += '+'.join(['-' * 5] * 3) + '\n'

        # for i, cell in enumerate(self.sub_boards):
        #     ret += cell if cell != ' ' else ' '  # str(i + 1)
        #
        #     if i % 3 < 2:
        #         ret += '|'
        #     elif i % 3 == 2 and i < 8:
        #         ret += '\n------\n'

        return ret + '\n'


def main():
    board = [[' ' for _ in range(9)] for _ in range(9)]
    human_player = HugeTicTacHumanPlayer(HUMAN_CHAR)
    ai_player = HugeTicTacAiPlayer(AI_CHAR)
    tictac_game = game.Game(HugeTicTacState(board, [human_player, ai_player]))

    for state in tictac_game.play():
        print(state)

    winner = tictac_game.get_winner()
    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
