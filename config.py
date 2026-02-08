# Paths
OUTPUT_PATH = "output"
ROOT_PATH = "."   # point this to the folder containing the 4 repos

# Progression categories and values
ALL_PROG_CATEGORIES = ("S", "A", "W", "I", "!")
SIMPLE_PROGRESSION_CATEGORIES_URI = ("S", "A", "W")
SIMPLE_PROGRESSION_CATEGORIES_MARTIN = ("S", "A", "W","I")
FINE_PROGRESSION_CATEGORIES_URI = ("S_dia", "WA_dia", "S_chr", "WA_chr")
FINE_PROGRESSION_CATEGORIES_MARTIN = ("S_dia", "WA_dia", "S_chr", "WA_chr","I")
ALL_PROGRESSION_VALUES_URI = tuple(range(-10, 0)) + tuple(range(1, 11))
ALL_PROGRESSION_VALUES_MARTIN = tuple( range(-10,11) )

# Variables
REPOS = [
        "bach_en_fr_suites",
        "bach_solo",
        # "beethoven_piano_sonatas",
        # "ABC",
        # "chopin_mazurkas",
        "mozart_piano_sonatas",
        # "liszt_pelerinage"
    ]