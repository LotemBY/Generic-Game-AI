from copy import deepcopy

import carlo_monte
import game
import minimax

HUMAN_CHAR = 'O'
AI_CHAR = 'X'


class TicTacHumanPlayer(game.Player):
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


class TicTacAiPlayer(carlo_monte.CarloMontePlayer):
    def __init__(self, char):
        super().__init__()  # 9)
        self.m_char = char

    def get_char(self):
        return self.m_char


class TicTacState(game.GameState):
    def __init__(self, cells, players, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.m_last_move = last_move
        self.m_cells = cells

    def notify_move(self):
        print(f'Player {self.m_last_move[0].get_char()} played at cell {self.m_last_move[1] + 1}.')

    def get_winner(self):
        sets = [(0, 1, 2), (3, 4, 5), (6, 7, 8),
                (0, 3, 6), (1, 4, 7), (2, 5, 8),
                (0, 4, 8), (2, 4, 6)]

        for a, b, c in sets:
            if self.m_cells[a] != ' ' and self.m_cells[a] == self.m_cells[b] and self.m_cells[a] == self.m_cells[c]:
                return next((p for p in self.m_players if p.get_char() == self.m_cells[a]), None)

        return None

    def eval(self):
        winner = self.get_winner()

        if winner is None:
            return 0

        return minimax.INF if winner.get_char() == AI_CHAR else -minimax.INF

    def get_moves(self):
        return (i for i, cell in enumerate(self.m_cells) if cell == ' ')

    def move(self, move: int):
        if move in range(len(self.m_cells)) and self.m_cells[move] == ' ':
            new_cells = deepcopy(self.m_cells)
            new_cells[move] = self.get_curr_player().get_char()
            last_move = (self.get_curr_player(), move)
            return TicTacState(new_cells, self.m_players, last_move, self._next_player_index())

    def __str__(self):
        ret = ''
        for i, cell in enumerate(self.m_cells):
            ret += cell if cell != ' ' else ' '  # str(i + 1)

            if i % 3 < 2:
                ret += '|'
            elif i % 3 == 2 and i < 8:
                ret += '\n------\n'

        return ret + '\n'


def main():
    board = [' ', ' ', ' ',  # 0 1 2
             ' ', ' ', ' ',  # 3 4 5
             ' ', ' ', ' ']  # 6 7 8

    human_player = TicTacHumanPlayer(HUMAN_CHAR)
    ai_player = TicTacAiPlayer(AI_CHAR)
    tictac_game = game.Game(TicTacState(board, [human_player, ai_player]))

    for state in tictac_game.play():
        print(state)

    winner = tictac_game.get_winner()
    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
