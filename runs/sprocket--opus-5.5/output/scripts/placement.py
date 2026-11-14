"""Footprint placement in board coordinates (mm, origin at the board's top-left corner, y down), as (x, y, rot).

KiCad rotation is counter-clockwise on screen. U1 is rotated 180°: pins 46-60 (VREG, USB, QSPI) face down,
31-45 face left, 1-15 face right and 16-30 face up."""

W, H = 28.0, 78.54
HDR_X = (14 - 11.43, 14 + 11.43)
HDR_Y0 = 10.16

FIXED = {
    # wireless and headers. R19 joins RM2 pads 5 and 6 from outside, in the channel beside the left header.
    "U7": (14.0, 8.25, 0),
    "J5": (HDR_X[0], HDR_Y0, 0),
    "J6": (HDR_X[1], HDR_Y0, 0),
    "R19": (5.3, 12.45, 270),
    "R20": (9.9, 18.4, 90),
    "C27": (20.4, 18.3, 0),
    "C28": (20.4, 19.6, 0),
    "C29": (20.4, 20.6, 0),
    "R22": (22.6, 13.6, 90),
    "R23": (22.6, 11.4, 90),
    # MCU and crystal; R2 sits in the gap left by pin 23, which connects inward
    "U1": (14.0, 29.29, 180),
    "Y1": (14.6, 21.54, 180),
    "R2": (14.2, 24.24, 90),
    "C15": (17.55, 20.94, 270),
    "C16": (11.65, 20.8, 90),
    # decoupling: only caps whose pins have a free neighbour sit in line; the rest use the planes
    "C1": (19.35, 32.39, 0),
    "C3": (19.35, 33.39, 0),
    "C7": (19.35, 34.39, 0),
    "C2": (19.35, 35.39, 0),
    "C8": (8.55, 29.49, 180),
    "C9": (6.65, 29.49, 180),
    "C11": (8.55, 31.89, 180),
    "C6": (8.55, 32.84, 180),
    "C5": (6.65, 31.89, 180),
    "C4": (6.65, 32.84, 180),
    "C10": (14.2, 34.34, 270),
    # core regulator copied from Raspberry Pi's hwdesign figure 4 (rotated 180°)
    "C12": (12.0, 33.94, 180),
    "C13": (12.0, 34.89, 180),
    "L1": (11.8, 36.59, 180),
    "C14": (9.75, 34.54, 90),
    "R1": (9.75, 36.39, 90),
    "R3": (13.57, 39.19, 270),
    "R4": (12.62, 39.19, 270),
    "R5": (21.4, 33.99, 90),
    # memory
    "U2": (18.7, 38.94, 0),
    "C17": (22.4, 35.04, 90),
    "U3": (8.4, 40.89, 180),
    "C18": (5.9, 44.09, 180),
    "R7": (10.75, 44.14, 0),
    # charger
    "U5": (8.0, 48.74, 0),
    "C19": (9.4, 45.61, 180),
    "R11": (6.8, 45.64, 90),
    "R10": (11.1, 47.54, 0),
    "C20": (11.0, 49.54, 270),
    "C21": (5.0, 49.14, 270),
    "R12": (4.95, 46.94, 0),
    "Q1": (2.2, 50.14, 270),
    "D1": (8.0, 51.94, 180),
    "R13": (5.4, 51.94, 0),
    # 3V3 buck-boost
    "U6": (18.2, 48.94, 0),
    "L2": (14.9, 48.94, 90),
    "C23": (17.7, 51.64, 0),
    "C25": (16.0, 45.94, 180),
    "C26": (19.6, 45.94, 0),
    "R16": (20.65, 48.94, 90),
    "C24": (21.65, 48.94, 90),
    "R17": (21.2, 51.14, 0),
    "R18": (21.2, 52.14, 0),
    # battery: JST on the left edge beside the charger, sense divider between it and the USB channel
    "J2": (5.1, 58.14, 270),
    "R14": (11.2, 54.14, 90),
    "R15": (11.2, 56.04, 90),
    "Q2": (11.3, 58.34, 90),
    "C22": (11.2, 60.54, 90),
    # user IO; the RUN pull-up sits by the reset button
    "SW1": (17.4, 55.14, 0),
    "SW2": (17.4, 59.14, 0),
    "R6": (16.0, 62.6, 0),
    "J4": (W - 3.28, 57.54, 90),
    "R30": (20.6, 62.84, 90),
    "R31": (21.6, 62.84, 90),
    # RGB LED beside U1's left side, so RGB_DIN (pin 34) stays short
    "D3": (7.6, 35.4, 180),
    "C32": (7.6, 37.4, 0),
    # USB
    "J1": (6.3, H - 3.675, 0),
    "U4": (6.3, H - 10.7, 270),
    "R8": (3.0, H - 10.2, 90),
    "R9": (9.6, H - 10.2, 90),
    # microSD
    "J3": (20.5, H - 6.25, 180),
    "R24": (22.9, 45.94, 90),
    "R25": (23.9, 45.94, 90),
    "R26": (24.9, 45.94, 90),
    "R27": (25.9, 45.94, 90),
    "R28": (26.9, 45.94, 90),
    "R29": (22.9, 48.34, 90),
    "C30": (12.65, H - 4.1, 90),
    "C31": (12.65, H - 1.7, 90),
    # fiducials: the RM2 antenna keepout and the headers leave no room for them near the top
    "FID1": (1.6, 46.74, 0),
    "FID2": (W - 2.2, 51.94, 0),
    "FID3": (1.6, H - 14.2, 0),
}

# U1 pins that connect inward to a via under the package: power pins whose neighbours both escape outward
# (50 sits between the VREG_VIN and USB lines), and WL_ON (35) and WL_CLK (43), which reach the RM2 on B.Cu from
# under the package.
# Value: how far the via shifts along the package edge, away from the corner, to clear the next side's pads.
INWARD_VIAS = {"6": 0, "11": 0, "20": 0, "23": 0, "30": 0.5, "35": 0, "38": 0, "43": 0, "50": 0}
