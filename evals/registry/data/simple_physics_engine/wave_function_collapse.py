import random

# The Wave Function Collapse algorithm is defined here:
# https://github.com/mxgmn/WaveFunctionCollapse
# Though it is best explained here:
# https://www.boristhebrave.com/2020/04/13/wave-function-collapse-explained/


class ContradictionException(Exception):
    """
    It's possible for the wave function collapse to result in an impossibility,
    meaning that the state is such that there are no possible options left to
    continue to collapse additional tiles.

    In this implementation, we just throw the exception so that we can re-run it.
    """


ABOVE = (-1, 0)
BELOW = (1, 0)
LEFT = (0, -1)
RIGHT = (0, 1)

BLOCK = "■"
LEFT_RAMP = "◢"
RIGHT_RAMP = "◣"
AIR = "▯"
BALL = "◦"


def get_rules():
    return [
        (AIR, ABOVE, AIR),
        (AIR, BELOW, AIR),
        (AIR, LEFT, AIR),
        (AIR, RIGHT, AIR),
        (BLOCK, ABOVE, BLOCK),
        (BLOCK, RIGHT, BLOCK),
        (BLOCK, LEFT, BLOCK),
        (BLOCK, BELOW, BLOCK),
        (BLOCK, RIGHT, AIR),
        (AIR, LEFT, BLOCK),
        (BLOCK, LEFT, AIR),
        (AIR, RIGHT, BLOCK),
        (BLOCK, BELOW, AIR),
        (AIR, ABOVE, BLOCK),
        (LEFT_RAMP, BELOW, AIR),
        (AIR, ABOVE, LEFT_RAMP),
        (RIGHT_RAMP, BELOW, AIR),
        (AIR, ABOVE, RIGHT_RAMP),
        (AIR, RIGHT, RIGHT_RAMP),
        (RIGHT_RAMP, LEFT, AIR),
        (AIR, LEFT, LEFT_RAMP),
        (LEFT_RAMP, RIGHT, AIR),
        (LEFT_RAMP, ABOVE, BLOCK),
        (BLOCK, BELOW, LEFT_RAMP),
        (RIGHT_RAMP, ABOVE, BLOCK),
        (BLOCK, BELOW, RIGHT_RAMP),
        (LEFT_RAMP, LEFT, BLOCK),
        (BLOCK, RIGHT, LEFT_RAMP),
        (RIGHT_RAMP, RIGHT, BLOCK),
        (BLOCK, LEFT, RIGHT_RAMP),
    ]


def init_possibilities():
    return [
        BLOCK,
        LEFT_RAMP,
        RIGHT_RAMP,
        AIR,
    ]


def create_wave_array(height, width):
    """
    Creates a two-dimensional array called the "wave" of HxW dimensions.
    The state of each tile is a superposition of all remaining possible options
    for the tile. This is represented by a list of boolean coefficients. False
    coefficient means that the corresponding pattern is forbidden, and true
    coefficient means that the corresponding pattern is not yet forbidden.

    The array is initialized in a completely unobserved state, i.e., with all
    the boolean coefficients being true.
    """
    # Create the HxW array, initially filling each tile with all possibilities
    wave = [[init_possibilities() for _ in range(width)] for _ in range(height)]

    for i in range(height):
        for j in range(width):
            # Fill the first row with air
            if i == 0:
                wave[i][j] = [AIR]

            # Fill the bottom with floor blocks
            if i == height - 1:
                wave[i][j] = [BLOCK]

            # Create the side walls
            if j in [0, width - 1]:
                wave[i][j] = [BLOCK]

    return wave


def get_final_state(tile) -> str:
    """
    Returns the key of the last remaining superposition.
    """
    return tile[0] if len(tile) == 1 else "?"


def calculate_entropy(tile):
    if len(tile) != 0:
        return 1 / len(tile)
    else:
        raise ContradictionException("Contradiction encountered. Rerun.")


def collapse_tile(tile):
    """
    Collapses the superpositions of the tile at coordinates x, y.
    From the remaining superpositions stills set to true, choose one at random
    and set the others to false.
    """
    selected_option = random.choice(tile)
    tile = [selected_option]  # Remove all other options except the selection

    return tile


def find_lowest_entropy_tile(wave):
    """
    Finds the tile with the lowest entropy an returns a tuple of the coordinates
    (i, j).
    """
    min_entropy = None

    possible_coords = []

    for i in range(len(wave)):
        for j in range(len(wave[i])):
            current_entropy = calculate_entropy(wave[i][j])

            if current_entropy == min_entropy:
                possible_coords.append((i, j))
            elif min_entropy is None or current_entropy < min_entropy:
                min_entropy = current_entropy
                min_coords = (i, j)
                possible_coords = [(i, j)]
    return random.choice(possible_coords)


# Helper functions for safely getting adjacent tiles.
def get_above_tile(wave, i, j):
    return wave[i - 1][j] if i > 0 else None


def get_below_tile(wave, i, j):
    return wave[i + 1][j] if i < len(wave) - 1 else None


def get_left_tile(wave, i, j):
    return wave[i][j - 1] if j > 0 else None


def get_right_tile(wave, i, j):
    return wave[i][j + 1] if j < len(wave[i]) - 1 else None


def place_ball(wave):
    width = len(wave[0])
    ball_placement = random.randint(1, width - 2)  # Account for walls
    wave[0][ball_placement] = [BALL]


def generate_collapsed_wave(height, width):
    wave = create_wave_array(height, width)

    for row in range(len(wave)):
        for _ in wave[row]:
            tile_coords = find_lowest_entropy_tile(wave)
            i, j = tile_coords

            wave[i][j] = collapse_tile(wave[i][j])

            # Propagate update to adjacent tiles
            propagate(wave, tile_coords)

    place_ball(wave)

    return wave


def get_valid_directions(wave, coords):
    i, j = coords
    directions = []
    if i > 0:
        directions.append(ABOVE)
    if i < len(wave) - 1:
        directions.append(BELOW)
    if j > 0:
        directions.append(LEFT)
    if j < len(wave[i]) - 1:
        directions.append(RIGHT)
    return directions


def get_possible_neighbors_in_direction(tile, direction):
    rules = get_rules()
    possible_neighbors = []
    for option in tile:
        possible_neighbors.extend(
            other
            for other, d, comp in rules
            if d == direction and comp == option
        )
    return possible_neighbors


def propagate(wave, coords):
    stack = [coords]
    while stack:
        curr_coords = stack.pop()
        curr_x, curr_y = curr_coords

        for vec in get_valid_directions(wave, curr_coords):
            vec_x, vec_y = vec
            other_coords = (curr_x + vec_x, curr_y + vec_y)
            other_x, other_y = other_coords
            other_possibilities = wave[other_x][other_y].copy()

            if len(other_possibilities) == 0:
                continue

            possible_neighbors = get_possible_neighbors_in_direction(wave[curr_x][curr_y], vec)

            for other_possibility in other_possibilities:
                if other_possibility not in possible_neighbors:
                    wave[other_x][other_y].remove(other_possibility)
                    if other_coords not in stack:
                        stack.append(other_coords)


def print_wave(wave):
    for i in range(len(wave)):
        for j in range(len(wave[i])):
            print(get_final_state(wave[i][j]), end="", sep="")
        print("\n", end="", sep="")
