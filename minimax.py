import random

import game

INF = 0xFFFF  # float("inf")
NO_MOVE = None
TIE_SCORE = 0


class MinimaxPlayer(game.Player):
    def __init__(self, depth):
        self.depth = depth

    def get_move(self, state):
        return minimax_alpha_beta([], state, self, self.depth)[0]


def minimax_alpha_beta(moves_log, state: game.GameState, max_player: MinimaxPlayer, max_depth=5, depth=0, alpha=-INF,
                       beta=INF) -> (int, int):
    winner = state.get_winner()
    if winner is not None:
        # TODO: consider depth
        score = INF - depth if winner is max_player else -INF + depth
        return NO_MOVE, score  # state.eval_state()

    moves = game.to_non_empty(state.get_moves())
    if not moves:
        return NO_MOVE, TIE_SCORE

    moves = list(moves)
    random.shuffle(moves)

    if depth >= max_depth:
        return NO_MOVE, state.eval()

    is_max_player = (depth % 2 == 0)
    best_moves = []
    best_score = None
    for move in moves:
        recursive_score = \
            minimax_alpha_beta(moves_log + [move], state.move(move), max_player, max_depth, depth + 1, alpha, beta)[1]
        if is_max_player:
            if best_score is None or recursive_score > best_score:
                best_score = recursive_score
                best_moves = [move]
                if best_score > alpha:
                    alpha = recursive_score
            elif recursive_score == best_score:
                best_moves.append(move)
        else:
            if best_score is None or recursive_score < best_score:
                best_score = recursive_score
                best_moves = [move]
                if best_score < beta:
                    beta = recursive_score
            elif recursive_score == best_score:
                best_moves.append(move)

        if alpha > beta:
            break

    # print(f'Depth {depth}/{max_depth}: [{",".join(str(i) for i in moves_log)}] | '
    #       f'As {state.get_curr_player().get_char()}, '
    #       f'my best moves are: [{",".join(str(i) for i in best_moves)}] with score: {best_score}')

    return random.choice(best_moves) if best_moves else None, best_score
