import abc
import itertools
import typing


def to_non_empty(iterable):
    try:
        return itertools.chain([next(iterable)], iterable)
    except StopIteration:
        return None


class Player(abc.ABC):
    @abc.abstractmethod
    def get_move(self, state: 'GameState'): pass

    def notify_bad_move(self):
        pass


class GameState(abc.ABC):
    # @abc.abstractstaticmethod
    # def initial_state(self) -> 'GameState': pass

    def __init__(self, players, player_index=0):
        self.m_players = players
        self.m_curr_player_index = player_index

    def get_curr_player(self):
        return self.m_players[self.m_curr_player_index]

    def _next_player_index(self):
        return (self.m_curr_player_index + 1) % len(self.m_players)

    def notify_move(self):
        pass

    @abc.abstractmethod
    def get_winner(self) -> Player: pass

    @abc.abstractmethod
    def eval(self) -> int: pass

    @abc.abstractmethod
    def get_moves(self) -> typing.Generator[int, None, None]: pass

    @abc.abstractmethod
    def move(self, move) -> 'GameState': pass

    @abc.abstractmethod
    def __eq__(self, other) -> bool:
        return self.m_curr_player_index == other.m_curr_player_index


class Game:
    def __init__(self, start_state: GameState):
        self.m_state: GameState = start_state
        self.m_winner: Player = None

    def _is_tie(self):
        return to_non_empty(self.m_state.get_moves()) is None

    def _is_game_over(self):
        self.m_winner = self.m_state.get_winner()
        return self.m_winner is not None or self._is_tie()

    def _do_next_move(self):
        new_state = None
        curr_player = self.m_state.get_curr_player()
        while new_state is None:
            move = curr_player.get_move(self.m_state)
            new_state = self.m_state.move(move)
            if new_state is None:
                curr_player.notify_bad_move()

        self.m_state = new_state
        self.m_state.notify_move()

    def get_winner(self):
        return self.m_winner

    def play(self):
        yield self.m_state
        while not self._is_game_over():
            self._do_next_move()
            yield self.m_state
