"""Board outline and footprint placement. Coordinates in mm from the board's top-left corner, y down."""
OUTLINE_W = 30.48
OUTLINE_H = 70.0
CORNER_R = 1.5
RM2_Y = 8.75  # RM2 origin: module top edge 0.5 mm inside the board edge, antenna keepout ends at y = 5.5
KEEPOUT_Y = RM2_Y - 3.25
# silkscreen labels drawn at 90°. The API drops text angles, so finish_files.py rotates these
VERTICAL_SILK = ("BOOT", "RST")

# Parts with fixed positions: ref -> (x, y, rotation_deg)
FIXED = {
    "U4": (15.24, RM2_Y, 0),
    "J5": (1.27, 7.62, 0),
    "J6": (29.21, 7.62, 0),
    "U1": (15.24, 29.0, 90),
    "Y1": (21.6, 29.6, 0),
    "U2": (13.8, 40.4, 0),
    "U3": (23.0, 40.4, 0),
    "J4": (5.1, 50.0, 270),
    "J2": (24.1, 52.0, 270),  # card mouth (footprint -y, with pads 1-8) faces the right board edge
    "J1": (10.0, OUTLINE_H - 3.1, 0),
    "J3": (23.4, OUTLINE_H - 3.28, 0),
    "U5": (14.6, 49.6, 0),
    "U6": (14.4, 56.4, 0),
    "U7": (17.4, 61.0, 90),
    "SW1": (6.0, 34.6, 90),
    "SW2": (6.0, 40.6, 90),
    "D1": (25.2, 21.2, 0),
}

# Small parts placed by a greedy search next to the pad they serve: ref -> (anchor ref, anchor pad)
ANCHORED = {
    # RP2350 decoupling, one cap per supply pin
    "C10": ("U1", "1"), "C11": ("U1", "11"), "C12": ("U1", "20"), "C13": ("U1", "30"),
    "C14": ("U1", "38"), "C15": ("U1", "45"), "C16": ("U1", "44"), "C17": ("U1", "54"),
    "C19": ("U1", "6"), "C20": ("U1", "23"), "C21": ("U1", "39"), "C29": ("U1", "23"),
    "C22": ("U1", "49"), "L1": ("U1", "48"), "C23": ("U1", "50"), "R20": ("U1", "46"), "C24": ("U1", "46"),
    "C18": ("U1", "49"),
    "C25": ("Y1", "1"), "C26": ("Y1", "3"), "R21": ("U1", "22"),
    "R22": ("U1", "52"), "R23": ("U1", "51"),
    "C27": ("U2", "8"), "C28": ("U3", "8"), "R24": ("U3", "1"),
    "R25": ("SW1", "1"),
    "C7": ("U1", "42"), "R10": ("U5", "2"), "R11": ("U5", "2"),
    "C42": ("D1", "4"),
    # RM2
    "C30": ("U4", "16"), "C31": ("U4", "16"), "C32": ("U4", "14"),
    "R30": ("U4", "6"), "R31": ("U4", "10"),
    "R12": ("U4", "17"), "R13": ("U4", "17"),
    # power
    "R1": ("J1", "A5"), "R2": ("J1", "B5"),
    "C1": ("U5", "13"), "C2": ("U5", "10"), "C3": ("U5", "2"),
    "R3": ("U5", "1"), "R4": ("U5", "16"), "R5": ("U5", "12"),
    "D2": ("U5", "9"), "R6": ("U5", "9"),
    "C4": ("U6", "1"), "R9": ("U6", "3"), "C5": ("U6", "5"), "C6": ("U6", "5"),
    # io
    "C40": ("J2", "4"), "C41": ("J2", "4"),
    "R40": ("J2", "1"), "R41": ("J2", "2"), "R42": ("J2", "3"), "R43": ("J2", "7"), "R44": ("J2", "8"),
    "R45": ("J2", "9"),
    "R46": ("J3", "3"), "R47": ("J3", "4"),
    "FID1": ("J5", "1"), "FID2": ("J6", "15"), "FID3": ("J1", "A1"),
}
