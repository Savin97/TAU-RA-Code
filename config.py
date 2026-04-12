# Paths
OUTPUT_PATH = "output"
ROOT_PATH = "."   # point this to the folder containing the 4 repos

# Progression categories and values
SAWINONE_PROG_CATEGORIES = ("S", "A", "W", "I", "None")
SIMPLE_PROGRESSION_CATEGORIES_URI = ("S", "A", "W")
SIMPLE_PROGRESSION_CATEGORIES_final = ("S", "A", "W",  "I")


composer_mid_life_dates = {
    'Bach': 1717,
    'Bartok': 1913,
    'Beethoven': 1798,
    'CPE_Bach': 1751,
    'Chopin': 1829,
    'Clara_Schumann': 1857,
    'Corelli': 1683,
    'Couperin': 1700,
    'Debussy': 1890,
    'Dvorak': 1872,
    'Frescobaldi': 1613,
    'Grieg': 1875,
    'Handel': 1722,
    'JC_Bach': 1758,
    'Kozeluh': 1782,
    'Liszt': 1848,
    'Mahler': 1885,
    'Medtner': 1915,
    'Mendelssohn': 1828,
    'Monteverdi': 1605,
    'Mozart': 1773,
    'Pergolesi': 1723,
    'Peri': 1597,
    'Pleyel': 1794,
    'Poulenc': 1931,
    'Rachmaninoff': 1908,
    'Ravel': 1906,
    'Scarlatti': 1721,
    'Schubert': 1812,
    'Schuetz': 1628,
    'Schulhoff': 1918,
    'Schumann': 1833,
    'Sweelinck': 1591,
    'Tchaikovsky': 1866,
    'WF_Bach': 1747,
    'Wagner': 1848
}

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