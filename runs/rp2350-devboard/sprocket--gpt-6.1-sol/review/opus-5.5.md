# opus-5.5's review

## Final message

The review found 9 confirmed problems: 4 major and 5 minor, with no fatal faults. They're in [review.json](review.json), which is valid JSON. I've also deleted the scratch folder and the pickle cache.

The upgrade made no changes. `kicad-cli` reported that the schematic and board are already in the connector's latest format (KiCad 10.99), so I didn't touch either file. DRC reports no violations and no unconnected items. The footprints and the pinouts of the main ICs match their libraries and datasheets.

| # | Area | Severity | Refs | Problem |
|---|---|---|---|---|
| 1 | routing | major | U1, U2, U3 | QSPI lines are 13–41 mm long to the flash against 9–19 mm direct, with 2–4 vias each. Lines to the PSRAM are 24–44 mm. |
| 2 | routing | major | U1, J2 | SD_CLK is 83 mm against about 38 mm direct, and the rest of the SD bus is 45–70 mm with up to 6 vias. |
| 3 | routing | minor | J2, R27 | SD_MOSI runs on past the card pin as a 21 mm stub to its pull-up. |
| 4 | routing | major | U1, R25, Y1, C4 | The crystal output path is about 21 mm with 6 vias, one segment on an inner layer. XIN is 8 mm with no vias. |
| 5 | layout | minor | U1, U2, U3 | Flash and PSRAM sit 14–23 mm from the QSPI pins. |
| 6 | layout | minor | Y1, R25 | The crystal sits 6–7 mm away, behind the decoupling caps. |
| 7 | layout | minor | U4, J1 | The charger is 26 mm from the USB-C VBUS pins, and the area next to J1 is empty. |
| 8 | routing | minor | J1, U4 | The VBUS feed narrows to 0.11 mm traces and passes through single 0.2 mm vias. |
| 9 | routing | minor | U5, C26, C27 | The 3V3 output reaches its plane through one 0.2 mm trace and one via, which it shares with the feedback pin. |

I chose not to report these:
- **Battery and system power traces:** their width is adequate for the current they carry.
- **J4 and SW1/SW2:** they sit inside the board but can still be reached.
- **Q2:** its gate is tied to 3V3, so battery sensing is always on. That isn't a fatal fault, and the "other" area only takes fatal ones.
