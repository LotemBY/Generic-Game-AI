import socket
import struct
from enum import Enum

import game
from carlo_monte import CarloMontePlayer

P1_CHAR = '()'
P2_CHAR = '[]'

ROWS = 5
COLS = 5


class Direction(Enum):
    NORTH = 'n'
    SOUTH = 's'
    WEST = 'w'
    EAST = 'e'
    NORTH_WEST = 'nw'
    NORTH_EAST = 'ne'
    SOUTH_WEST = 'sw'
    SOUTH_EAST = 'se'

    def as_diff(self):
        AS_DIFF = {
            Direction.NORTH.value: (-1, 0),
            Direction.SOUTH.value: (1, 0),
            Direction.WEST.value: (0, -1),
            Direction.EAST.value: (0, 1),
            Direction.NORTH_WEST.value: (-1, -1),
            Direction.NORTH_EAST.value: (-1, 1),
            Direction.SOUTH_WEST.value: (1, -1),
            Direction.SOUTH_EAST.value: (1, 1)
        }

        return AS_DIFF[self.value]


class SantoriniHumanPlayer(game.Player):
    def __init__(self, char):
        self.m_char = char

    def get_char(self):
        return self.m_char

    def get_move(self, _state):
        print('Enter your move: ', end='')
        while True:
            try:
                inputs = input().lower().split(' ')
                if len(inputs) == 3:
                    worker = int(inputs[0])
                    assert worker < SantoriniState.WORKERS_NUMBER

                    walk = Direction(inputs[1])
                    build = Direction(inputs[2])
                    return worker, walk, build
            except (ValueError, AssertionError):
                pass
            print(f'Illegal move. Enter your move: ', end='')

    def notify_bad_move(self):
        print('Illegal move.')

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class SantoriniNetworkPlayer(game.Player):
    def __init__(self, char, address):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.socket.connect(address)
        self.m_char = char

    def send_opponent_move(self, state):
        _player, worker, walk, build = state.last_move

        def direction_to_str(direction):
            if direction in (Direction.EAST, Direction.WEST):
                return ' ' + direction.value
            else:
                return f'{direction.value:2}'

        move = f'{worker} {direction_to_str(walk)} {direction_to_str(build)}'
        self.socket.send(move.encode('ascii'))

    def get_move(self, state: 'SantoriniState'):
        self.send_opponent_move(state)

        inputs = self.socket.recv(8).decode('ascii')

        worker = int(inputs[0])
        walk = Direction(inputs[2:4].replace(' ', ''))
        build = Direction(inputs[5:7].replace(' ', ''))
        return worker, walk, build

    def get_char(self):
        return self.m_char

    def notify_game_end(self, state):
        self.send_opponent_move(state)
        self.socket.close()

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class SantoriniAiPlayer(CarloMontePlayer):  # minimax.MinimaxPlayer):
    def __init__(self, char, iterations, secs=None, think_ahead=False):
        super().__init__(iterations, secs, think_ahead)
        self.m_char = char

    def get_char(self):
        return self.m_char

    def __str__(self):
        return f'PLAYER_{self.m_char}'


class SantoriniState(game.GameState):
    WORKERS_NUMBER = 2
    MAX_BUILD_HEIGHT = 4

    def __init__(self, cells, players, workers, last_move=None, player_index=0):
        super().__init__(players, player_index)
        self.last_move = last_move
        self.workers = workers
        self.cells = cells
        self.rows = len(self.cells)
        self.cols = len(self.cells[0])

    def notify_move(self):
        print(f'Player {self.last_move[0].get_char()} '
              f'moved worker #{self.last_move[1]} '
              f'to {self.last_move[2]} '
              f'and built at {self.last_move[3]}.')
        print(f'{self.last_move[1]} {self.last_move[2].value} {self.last_move[3].value}\n')

    def in_board(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_winner(self):
        if self.no_moves():
            return self.m_players[self._next_player_index()]

        for player, workers in zip(self.m_players, self.workers):
            for worker_row, worker_col in workers:
                if self.cells[worker_row][worker_col] == self.MAX_BUILD_HEIGHT - 1:
                    return player

        return None

    def eval(self):
        return 0

    # TODO: we can do this in O(1) and not O(4), or at least cache it
    def is_worker_location(self, row, col, about_to_move=None):
        if not about_to_move or (row, col) != about_to_move:
            for workers in self.workers:
                if (row, col) in workers:
                    return True
        return False

    def get_moves(self):
        for worker_id, (worker_row, worker_col) in enumerate(self.workers[self.m_curr_player_index]):
            worker_height = self.cells[worker_row][worker_col]

            for walk_dir in Direction:
                row_diff, col_diff = walk_dir.as_diff()
                new_row, new_col = worker_row + row_diff, worker_col + col_diff
                if not self.in_board(new_row, new_col) \
                        or self.cells[new_row][new_col] > worker_height + 1 \
                        or self.is_worker_location(new_row, new_col):
                    continue

                for build_dir in Direction:
                    row_diff, col_diff = build_dir.as_diff()
                    build_row, build_col = new_row + row_diff, new_col + col_diff
                    if self.in_board(build_row, build_col) \
                            and self.cells[build_row][build_col] < self.MAX_BUILD_HEIGHT \
                            and not self.is_worker_location(build_row, build_col,
                                                            about_to_move=(worker_row, worker_col)):
                        yield worker_id, walk_dir, build_dir

    def move(self, move: (int, Direction, Direction)):
        worker_id, walk_dir, build_dir = move
        worker_row, worker_col = self.workers[self.m_curr_player_index][worker_id]
        worker_height = self.cells[worker_row][worker_col]

        walk_row_diff, walk_col_diff = walk_dir.as_diff()
        new_row, new_col = worker_row + walk_row_diff, worker_col + walk_col_diff

        if self.in_board(new_row, new_col) \
                and self.cells[new_row][new_col] <= worker_height + 1 \
                and not self.is_worker_location(new_row, new_col):
            row_diff, col_diff = build_dir.as_diff()
            build_row, build_col = new_row + row_diff, new_col + col_diff
            if self.in_board(build_row, build_col) \
                    and self.cells[build_row][build_col] < self.MAX_BUILD_HEIGHT \
                    and not self.is_worker_location(build_row, build_col, about_to_move=(worker_row, worker_col)):
                new_cells = [r if index != build_row else r[::] for index, r in
                             enumerate(self.cells)]  # copy only the row that is about to change
                new_cells[build_row][build_col] = self.cells[build_row][build_col] + 1

                new_workers = [w if index != self.m_curr_player_index else w[::] for index, w in
                               enumerate(self.workers)]  # copy only the row that is about to change
                new_workers[self.m_curr_player_index][worker_id] = (new_row, new_col)

                last_move = (self.get_curr_player(), *move)
                return SantoriniState(cells=new_cells,
                                      players=self.m_players,
                                      workers=new_workers,
                                      last_move=last_move,
                                      player_index=self._next_player_index())

        return None

    def __eq__(self, other) -> bool:
        return super().__eq__(other) \
               and self.cells == other.cells \
               and self.workers == other.workers

    def __str__(self):
        ret = ''
        for row_index, row in enumerate(self.cells):
            for col_index, cell in enumerate(row):
                curr_worker = '  '
                for player, workers in zip(self.m_players, self.workers):
                    if (row_index, col_index) in workers:
                        curr_worker = player.get_char()
                ret += f'{curr_worker[0]}{cell}{curr_worker[1]}'
            ret += '\n'

        for i, workers_at_index in enumerate(zip(*self.workers)):
            ret += f'\nWorker #{i}:'
            for player, (worker_row, worker_col) in zip(self.m_players, workers_at_index):
                player_char_1, player_char_2 = player.get_char()
                ret += f' {player_char_1}{worker_row}, {worker_col}{player_char_2}'

        return ret


class SantoriniGame(game.Game):
    def _is_tie(self):
        return False


def main():
    board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    # board[2][2] = 3
    # board[3][3] = 2

    player1 = SantoriniAiPlayer(P1_CHAR, iterations=10_000, secs=10)
    # player2 = SantoriniAiPlayer(P2_CHAR, iterations=10_000, secs=10)
    player2 = SantoriniNetworkPlayer(P2_CHAR, ('84.229.89.76', 9999))
    santorini_game = SantoriniGame(SantoriniState(cells=board,
                                                  players=[player1, player2],
                                                  workers=[[(1, 1), (ROWS - 2, COLS - 2)],
                                                           [(1, COLS - 2), (ROWS - 2, 1)]]))

    for state in santorini_game.play():
        print(state)

    winner = santorini_game.get_winner()
    if winner is not None:
        print(f'The winner is {winner.get_char()}!')
    else:
        print(f'It\'s a tie!')


if __name__ == '__main__':
    main()
