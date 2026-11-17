# opus-5.5's review

## Final message

I wrote [review.json](review.json) with 11 findings. It loads as valid JSON, and every net in it exists on the board. The four schematics and the board were upgraded in place to the connector's KiCad version earlier, with no other design changes. The original files are in `scratch/orig/`.

| # | Area | Severity | Refs | Problem |
|---|---|---|---|---|
| 1 | layout | fatal | J3 | The microSD socket opening faces into the board at x≈167.5. R35–R39, C40 and C41 block the card path, so no card can be inserted. |
| 2 | routing | major | U6, J2 | The BAT path is 0.15 mm wide for all 13.2 mm, carrying 1.5 A. |
| 3 | routing | major | U6, U7 | VSYS narrows to 0.15 mm at the U6 output and 0.2 mm at U7's input, and uses single 0.3 mm vias. |
| 4 | routing | major | U1, J3, R41 | SD_MISO is 64.6 mm long (40.5 mm straight) with 8 vias, looping under the QSPI area. The clock resistor R41 is 20 mm of trace from its source pin. |
| 5 | routing | minor | U1, U2, U3 | QSPI traces are about twice their straight length, with 2–3 vias each, D3 daisy-chained and an 11 mm stub to R5. |
| 6 | routing | minor | Y1 | XIN uses 2 vias and runs about 10 mm on the +3V3 plane layer. |
| 7 | routing | minor | J1, F1 | The USB VBUS input is 0.15 mm wide, down to 0.1124 mm in places. |
| 8 | layout | minor | U3 | The PSRAM pins are 9–14.6 mm from the QSPI pins. |
| 9 | layout | minor | SW1–SW3 | The buttons sit in the board interior, and SW1/SW2 are behind J7. |
| 10 | layout | minor | J2 | The battery connector is about 7 mm in from the edge. |
| 11 | layout | minor | J5 | The SWD connector is in the board interior. |

The handoff left U7's +3V3 output open, and I left it out of the review. The output has one narrow part, a 0.2 mm trace 1.1 mm long at pin 9, and it reaches the In2 +3V3 plane through four vias. That's plenty for the board's real load of about 0.5 A.

I also left these out:
- The duplicated +3V3 track segments, because they're harmless.
- The antenna placement and the USB-C position, which are both fine.
- The BUCK_L1/L2 necks at the pads, which I judged marginal.

The first pass of the file had four net names that don't exist on the board. I replaced them with the real names, such as `QSPI_CLK` and `SD_SCK`, before the final check.
