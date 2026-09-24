# Per-ticket slot layouts. Slot numbers are raw indices from the game's symbol list, not screen order.

# SHAPES: name -> grid of raw slot indices (None = blank), for simple layouts.
SHAPES = {}

# TEMPLATES: name -> (ASCII art lines, {slot: (row, col_start, col_end)}, expected slot count).
TURTLE_TEMPLATE = [
    '         .-------------------.',
    '        /     \\        /     \\',
    '       /       \\      /       \\',
    '      /         .----.         \\',
    '     |         /      \\         |',
    '     |--------<        >--------|',
    '     |         \\      /         |',
    "      \\         '----'         /",
    '       \\       /      \\       /',
    '        \\     /        \\     /',
    "          '----------------'",
]

TURTLE_SLOTS = {
    0: (2, 8, 15),    # left
    1: (1, 15, 23),   # top
    2: (5, 15, 23),   # center
    3: (2, 23, 30),   # right
    4: (8, 8, 15),    # bottom-left
    5: (9, 15, 23),   # bottom
    6: (8, 23, 30),   # bottom-right
}

LUCKY_CAT_TEMPLATE = [
    '           .-----.         .-----.',
    '          /       \\       /       \\',
    '         |         |     |         |',
    '          \\       /       \\       /',
    "           '-----'         '-----'",
    '',
    '    .-----.                       .-----.',
    '   /       \\                     /       \\',
    '  |         |     .-------.     |         |',
    '   \\       /     /         \\     \\       /',
    "    '-----'     /           \\     '-----'",
    '               |             |',
    '              /               \\',
    '             |                 |',
    '              \\     /---\\     /',
    "               '---'     '---'",
]

LUCKY_CAT_SLOTS = {
    1: (2, 10, 19),   # top-left
    3: (2, 26, 35),   # top-right
    0: (8, 3, 12),    # mid-left (by elimination, never observed directly)
    2: (8, 33, 42),   # right
    4: (12, 15, 30),  # center (paw print)
}

TWO_WIN_TEMPLATE = [
    '+-------+-------+-------+',
    '|       |       |       |',
    '|       |       |       |',
    '|       |       |       |',
    '+-------+-------+-------+',
]

TWO_WIN_SLOTS = {
    0: (2, 1, 8),     # left (left/mid order unverified: both were Money Bag)
    1: (2, 9, 16),    # middle
    2: (2, 17, 24),   # right (confirmed: unique Bill symbol)
}

MINI_SCRATCH_TEMPLATE = [
    '   .---.        .---.        .---.',
    '  /     \\      /     \\      /     \\',
    '  |     |      |     |      |     |',
    '   \\___/        \\___/        \\___/',
    '',
    '       .---.        .---.',
    '      /     \\      /     \\',
    '      |     |      |     |',
    '       \\___/        \\___/',
]

MINI_SCRATCH_SLOTS = {
    0: (2, 3, 8),     # top-left
    4: (2, 16, 21),   # top-mid
    1: (2, 29, 34),   # top-right
    2: (7, 7, 12),    # bottom-left
    3: (7, 20, 25),   # bottom-right
}

APPLE_TREE_TEMPLATE = [
    '   .---.                .---.',
    '  /     \\              /     \\',
    '  |     |              |     |',
    '   \\___/                \\___/',
    '',
    '               .---.',
    '              /     \\',
    '              |     |',
    '               \\___/',
    '',
    '   .---.                .---.',
    '  /     \\              /     \\',
    '  |     |              |     |',
    '   \\___/                \\___/',
]

APPLE_TREE_SLOTS = {
    0: (2, 3, 8),     # top-left (positions unverified, reading order assumed)
    1: (2, 24, 29),   # top-right
    2: (7, 15, 20),   # center
    3: (12, 3, 8),    # bottom-left
    4: (12, 24, 29),  # bottom-right
}

QUICK_CASH_TEMPLATE = [
    '+-------+-------+-------+',
    '|       |       |       |',
    '|       |       |       |      +-------+',
    '|       |       |       |      |       |',
    '+-------+-------+-------+      |       |',
    '|       |       |       |      |       |',
    '|       |       |       |      +-------+',
    '|       |       |       |',
    '+-------+-------+-------+',
]

QUICK_CASH_SLOTS = {
    0: (2, 1, 8),     # top-left (all positions unverified, reading order assumed)
    1: (2, 9, 16),    # top-middle
    2: (2, 17, 24),   # top-right
    3: (6, 1, 8),     # bottom-left
    4: (6, 9, 16),    # bottom-middle
    5: (6, 17, 24),   # bottom-right
    6: (4, 32, 39),   # 7th box (right side)
}

SAND_DOLLARS_TEMPLATE = [
    '    +-------+-------+-------+-------+',
    '    |       |       |       |       |',
    '    |       |       |       |       |',
    '    |       |       |       |       |',
    '    +-------+-------+-------+-------+',
    '',
    '+-------+-------+-------+-------+-------+',
    '|       |       |       |       |       |',
    '|       |       |       |       |       |',
    '|       |       |       |       |       |',
    '+-------+-------+-------+-------+-------+',
]

SAND_DOLLARS_SLOTS = {
    0: (2, 5, 12),    # top row, left to right (all positions unverified, reading order assumed)
    1: (2, 13, 20),
    2: (2, 21, 28),
    3: (2, 29, 36),
    4: (8, 1, 8),     # bottom row, left to right
    5: (8, 9, 16),
    6: (8, 17, 24),
    7: (8, 25, 32),
    8: (8, 33, 40),
}

SNAKE_EYES_TEMPLATE = [
    '+-------+-------+-------+',
    '|       |       |       |',
    '|       |       |       |',
    '|       |       |       |',
    '+-------+-------+-------+',
    '|       |       |       |',
    '|       |       |       |',
    '|       |       |       |',
    '+-------+-------+-------+',
]

SNAKE_EYES_SLOTS = {
    0: (2, 1, 8),     # top-left (all positions unverified, reading order assumed)
    1: (2, 9, 16),    # top-middle
    2: (2, 17, 24),   # top-right
    3: (6, 1, 8),     # bottom-left
    4: (6, 9, 16),    # bottom-middle
    5: (6, 17, 24),   # bottom-right
}

DAY_JOB_TEMPLATE = [
    '   .---.',
    '  /     \\',
    '  |     |',
    '   \\___/',
]

DAY_JOB_SLOTS = {
    0: (2, 3, 8),
}

# TEMPLATES entries: (art, slot positions, expected slot count, always_show).
# always_show=True draws the shape on a penalty result too, not just a win —
# for tickets like Day Job that have no neutral outcome, only win or penalty.
TEMPLATES = {
    "Day Job": (DAY_JOB_TEMPLATE, DAY_JOB_SLOTS, 1, True),
    "Snake Eyes": (SNAKE_EYES_TEMPLATE, SNAKE_EYES_SLOTS, 6, False),
    "Sand Dollars": (SAND_DOLLARS_TEMPLATE, SAND_DOLLARS_SLOTS, 9, False),
    "Quick Cash": (QUICK_CASH_TEMPLATE, QUICK_CASH_SLOTS, 7, False),
    "Apple Tree": (APPLE_TREE_TEMPLATE, APPLE_TREE_SLOTS, 5, False),
    "Mini Scratch": (MINI_SCRATCH_TEMPLATE, MINI_SCRATCH_SLOTS, 5, False),
    "Two Win": (TWO_WIN_TEMPLATE, TWO_WIN_SLOTS, 3, False),
    "Scratch My Back": (TURTLE_TEMPLATE, TURTLE_SLOTS, 7, False),
    "Lucky Cat": (LUCKY_CAT_TEMPLATE, LUCKY_CAT_SLOTS, 5, False),
}
