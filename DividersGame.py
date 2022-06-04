from copy import deepcopy

import carlo_monte
import game
import minimax

HUMAN_CHAR = 'O'
AI_CHAR = 'X'


class DividersHumanPlayer(game.Player):
    def __init__(self, char):
        self.m_char = char

    def get_char(self):
        return self.m_char

    def get_move(self, state):
        move = None
        print('Enter your choice: ', end='')
        while move is None:
            try:
                move = int(input())
            except ValueError:
                print(f'Enter your choice (1-{state.MAX_NUM}): ', end='')

        return move

    def notify_bad_move(self):
        print('Illegal number.')

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class DividersAiPlayer(minimax.MinimaxPlayer):
    def __init__(self, char):
        super().__init__(50)
        self.m_char = char

    def get_char(self):
        return self.m_char


class DividersState(game.GameState):
    def __init__(self, numbers, players, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.m_last_move = last_move
        self.numbers = numbers

    def notify_move(self):
        s = f'Player {self.m_last_move[0].get_char()} took {self.m_last_move[1][0]}'

        if len(self.m_last_move[1]) > 1:
            s += f' (and {", ".join(map(str, self.m_last_move[1][1:]))})'

        print(s + '.')

    def get_winner(self):
        if not self.numbers:
            return self.m_players[self._next_player_index()]

    def eval(self):
        winner = self.get_winner()

        if winner is None:
            return 0

        return minimax.INF if winner.get_char() == AI_CHAR else -minimax.INF

    def get_moves(self):
        return iter(self.numbers)

    def move(self, move: int):
        if move in self.numbers:
            last_move = (self.get_curr_player(), [])
            new_numbers = self.numbers[::]
            for n in self.numbers[::-1]:
                if move % n == 0:
                    last_move[1].append(n)
                    new_numbers.remove(n)

            return DividersState(new_numbers, self.m_players, last_move, self._next_player_index())

    def __str__(self):
        return ', '.join(map(str, self.numbers)) + '\n'

    def __eq__(self, other) -> bool:
        return super().__eq__(other) and self.numbers == other.numbers


def main():
    human_player = DividersAiPlayer(HUMAN_CHAR)
    ai_player = DividersAiPlayer(AI_CHAR)

    dividers_game = game.Game(DividersState(list(range(1, 16)), [human_player, ai_player]))

    for state in dividers_game.play():
        print(state)

    winner = dividers_game.get_winner()

    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
