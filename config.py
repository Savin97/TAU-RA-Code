# Paths
OUTPUT_PATH = "output"
ROOT_PATH = "."   # point this to the folder containing the 4 repos

# Progression categories and values
SAWINONE_PROG_CATEGORIES = ("S", "A", "W", "I", "None")
SIMPLE_PROGRESSION_CATEGORIES_URI = ("S", "A", "W")
SIMPLE_PROGRESSION_CATEGORIES_MARTIN = ("S", "A", "W",  "I")

# Variables
REPOS = [
        "bach_en_fr_suites",
        "bach_solo",
        "beethoven_piano_sonatas",
        "ABC",
        "chopin_mazurkas",
        "mozart_piano_sonatas",
        "liszt_pelerinage"
    ]

#
UNNECESSARY_COLS = (
    ["mn", 
    "mn_onset",
    "mn_onset_numeric",
    "staff", 
    "voice", 
    "offset_x", 
    "offset_y", 
    "offset", 
    "alt_label", 
    "globalkey", 
    "localkey", 
    "pedal", 
    "chord", 
    "numeral", 
    "form", 
    "figbass", 
    "changes", 
    "relativeroot", 
    "cadence", 
    "phraseend", 
    "chord_type", 
    "globalkey_is_minor", 
    "localkey_is_minor", 
    "chord_tones", 
    "added_tones", 
    "bass_note", 
    "n_colored", 
    "n_untouched", 	
    "count_ratio",
    "dur_colored",
    "dur_untouched",
    "dur_ratio"
    ])