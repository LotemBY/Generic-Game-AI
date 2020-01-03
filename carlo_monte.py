import math
import random
import time

from game import GameState, Player


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % (method.__name__, (te - ts) * 1000))
        return result

    return timed


SEARCH_CONST = 2  # math.sqrt(2)
INF = 0xFFFF  # float("inf")
TIE_SCORE = 0

g_depths = []
g_statics = 0


class CarloMontePlayer(Player):
    def __init__(self, iterations=2000):
        self.iterations = iterations
        self.root = None

    def get_root_for_state(self, state):
        if self.root is None:
            return CarloMonteTreeNode(state)

        for child in self.root.childs:
            if child.state == state:
                new_root = child
                new_root.parent = None
                new_root.depth = 0
                return new_root

        return CarloMonteTreeNode(state)

    def get_move(self, state):
        self.root = self.get_root_for_state(state)
        self.root = self.root.calc_best_move(self.iterations)
        return self.root.move


class CarloMonteTreeNode:
    def __init__(self, state: GameState,
                 depth: int = 0, max_player: bool = True, move=None, parent: 'CarloMonteTreeNode' = None) -> None:
        self.max_player = max_player
        self.depth = depth
        self.state = state
        self.move = move  # What move brought us here from the parent
        self.parent = parent
        self.total = 0
        self.visits = 0
        self.childs: [GameState] = []
        self.static_value = None
        self.selection_func = max if self.max_player else min

    def get_score(self) -> float:
        if self.static_value is not None:
            return self.static_value

        if self.visits == 0:
            return 0

        return self.total / self.visits

    def priority(self) -> float:
        # # I don't need any more visits, i know my score
        # if self.static_value is not None:
        #     return -INF if self.parent.max_player else INF

        # If it was never visited, it has a high priority
        if self.visits == 0:
            return INF if self.parent.max_player else -INF

        # Avg score + How much did we explore here
        return self.get_score() / 1000 + \
               (SEARCH_CONST if self.parent.max_player else -SEARCH_CONST) * \
               math.sqrt(math.log(self.parent.visits) / self.visits)

    def next_node(self) -> 'CarloMonteTreeNode':
        if not self.childs:
            return self

        return self.selection_func(self.childs, key=lambda node: node.priority()).next_node()

    def create_childs(self):
        assert not self.childs, 'Fuck i have childs :('

        self.childs = [CarloMonteTreeNode(self.state.move(move), self.depth + 1, not self.max_player, move, self) for
                       move in self.state.get_moves()]

    # @timeit
    def simulate(self) -> float:
        # ts = time.time()

        curr_state = self.state
        ret = None
        for i in range(100):
            winner = curr_state.get_winner()
            if winner is not None:
                # TODO: consider depth - maybe in the eval function
                # print(curr_state)
                # print(f'Winner: {winner} - Eval: {curr_state.eval()}')
                g_depths.append(i)
                ret = 1000 - i - self.depth if isinstance(winner, CarloMontePlayer) else - 1000 + i + self.depth
                # print(f'Score: {ret}')
                break

            moves = list(curr_state.get_moves())
            if not moves:
                # print(curr_state)
                # print(f'Tie!')
                g_depths.append(i)
                ret = TIE_SCORE
                break

            curr_state = curr_state.move(random.choice(moves))
            assert curr_state is not None

        # te = time.time()
        # print('%2.2f ms, depth %d. (%2.2f per move).' % ((te - ts) * 1000, i, (te - ts) * 1000 / i))
        return ret

    def update(self, score: float):
        curr_node = self
        while curr_node:
            curr_node.total += score
            curr_node.visits += 1
            curr_node = curr_node.parent

    def expend_simulate_update(self):
        global g_statics

        winner = self.state.get_winner()
        if winner is not None:
            """ Terminal state """
            # self.state.eval()
            self.static_value = 1000 - self.depth if isinstance(winner, CarloMontePlayer) else - 1000 + self.depth
            to_simulate = self
            score = self.static_value
            g_statics += 1
        else:
            if self.visits == 0:
                """ Never visited, simulate here """
                to_simulate = self
                score = to_simulate.simulate()
            else:
                """ Expand """
                self.create_childs()
                if not self.childs:
                    """ No childs, its a tie """
                    self.static_value = 0
                    to_simulate = self
                    score = self.static_value
                    """ Simulate newly expanded child """
                else:
                    to_simulate = self.childs[0]
                    score = to_simulate.simulate()

        # print(f'State:\n{self.state}\nScore: {score}\n')

        """ Update """
        to_simulate.update(score)

    @timeit
    def calc_best_move(self, iterations_num):
        global g_depths, g_statics
        g_depths = []
        g_statics = 0

        if not self.childs:
            self.create_childs()

        for iterations_counter in range(iterations_num):
            next_node = self.next_node()
            next_node.expend_simulate_update()

            # if iterations_counter == iterations_num - 1 or iterations_counter % 200 == 0:
            #     childs_str = "\n\t".join(repr(child) for child in self.childs)
            #     print(f'{iterations_counter}:\n\t{childs_str}')
            #
            # should_stop = False
            # for child in self.childs:
            #     if child.visits > 300 and child.get_score() > 800:
            #         should_stop = True
            #         print(f'[!] Breaking after {iterations_counter} iterations. ({child})')
            #         break
            # if should_stop:
            #     break

        best_move = max(self.childs, key=lambda node: node.get_score())
        #
        # print(f'Self: {self}')
        # total_visits = sum(child.visits for child in self.childs)
        # print(f'Total visits: {total_visits}')
        # print(f'Statics: {g_statics}')
        # print(f'Chose {best_move}.')
        # print(f'Avg Depth: {sum(g_depths) / len(g_depths)}')
        return best_move

    def __repr__(self):
        if self.static_value:
            return f'<{self.move}, Visits: {self.visits}, Value: {self.static_value} | Priority: {self.priority()}>'

        return f'<{self.move}, ' \
               f'Total: {self.total}, Visits: {self.visits} (={self.get_score()}), ' \
               f'Childs: {len(self.childs)} | ' \
               f'Priority: {0 if self.parent is None else self.priority()}>'
