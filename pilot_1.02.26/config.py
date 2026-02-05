ALL_PROG_LABELS = ("S", "A", "W", "I", "!")
SIMPLE_PROGRESSION_CATEGORIES = ("S", "A", "W","I")
FINE_PROGRESSION_LABELS = ("S_dia", "WA_dia", "S_chr", "WA_chr")
OUTPUT_PATH = "output"
ROOT_PATH = "."   # point this to the folder containing the 4 repos
ROOT_DIFF_VALUES = tuple(range(-10, 0)) + tuple(range(1, 11))
# New fine-grained categorization (requested)
FINE_PROGRESSION_MAP = {
    "S_dia": {3, -1, -4},
    "WA_dia": {1, 2, 4, 5, -2, -3, -5},
    "S_chr": {6, 10, -8},
    "WA_chr": {7, 8, 9, -6, -7, -9, -10}
}


