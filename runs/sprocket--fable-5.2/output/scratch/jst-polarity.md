# JST PH battery polarity for `JST_PH_S2B-PH-SM4-TB_1x02-1MP_P2.00mm_Horizontal`

## Answer

**Pad 1 = battery + (VBAT), pad 2 = GND** for the KiCad stock footprint.
This matches Adafruit and SparkFun LiPo cells.

Physical check: board component side up, looking into the mating opening from
the front (key slots on top, away from the board), **+ is on the left**, GND on
the right. On the battery plug, viewed on its mating face with the bumps up,
red is on the right.

## Trap

Adafruit and SparkFun Eagle libraries number this same part the other way
round: their pad 1 is GND and pad 2 is VBAT. Adafruit support also states
"Pin1 = GND, Pin2 = VCC". Copying those pin numbers into KiCad reverses the
battery. Copy the physical position, not the number.

The KiCad through-hole footprint `JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal`
is not mirrored relative to the SMD one: pad 1 is also on the left looking
into the opening (pads at y=0, body to y=+6.25, pad 1 at x=0, pad 2 at x=+2).
I did not verify a THT reference design.

## Evidence

1. KiCad footprint (read from the installed library). Pad 1 at (-1, -2.85),
   pad 2 at (+1, -2.85), mounting pads at y=+2.9, body front edge at y=+4.4.
   Signal pads are at the rear, the opening faces +Y. KiCad Y points down, so
   a viewer facing the opening has pad 1 (-X) on the left.
2. JST PH datasheet, https://www.jst-mfg.com/product/pdf/eng/ePH.pdf, pages 2
   and 4. The SMT side-entry land pattern (viewed from the mounting surface)
   and the front view both put "No. 1 circuit" on the left when facing the
   opening. KiCad follows JST numbering.
3. Adafruit Feather M0 Basic, Eagle board, part X1 package `JSTPH2`:
   https://github.com/adafruit/Adafruit-Feather-M0-Basic-Proto-PCB
   Pads at y=-3.7 (rear), opening at +Y, pad 1 at x=-1 = GND, pad 2 at
   x=+1 = VBAT. Eagle Y points up, so a viewer facing the opening has pad 2
   (VBAT) on the left.
4. SparkFun ESP32 Thing Plus, Eagle board, JP2 package `JST-2-SMD`:
   https://github.com/sparkfun/ESP32_Thing_Plus/tree/master/Hardware
   Same land pattern and numbering: pad 1 = GND, pad 2 = V_BATT. + on the left.
5. DigiKey TechForum, annotated photo of the S2B-PH-SM4-TB with Adafruit and
   SparkFun polarity, + on the left looking in with the slots up:
   https://forum.digikey.com/t/polarity-standard-for-jst-ph-connectors-on-lipo-batteries/64548
6. Adafruit forum. Adafruit numbers PH pins right to left facing the
   connector, the reverse of JST, and uses Pin1=GND, Pin2=VCC in that numbering:
   https://forums.adafruit.com/viewtopic.php?t=177225
   https://forums.adafruit.com/viewtopic.php?t=185602
7. SparkFun tutorial. The battery plug has pin 1 = +VBATT (red), in JST
   numbering, which agrees with KiCad pad 1 = +:
   https://learn.sparkfun.com/tutorials/single-cell-lipo-battery-care/jst-ph-connectors

## Confidence

High, about 95%. Four independent sources (JST drawing, two vendor board
files, DigiKey photo) agree on + at the left. The remaining risk is a
third-party cell wired with reversed polarity, which is common. Check any
non-Adafruit/SparkFun cell with a meter and mark + on the silkscreen.

Not done: I did not render the footprint or check a physical part. The JST
page images came from a PDF copy already in /tmp/jst, since direct download
of the JST URL returned 403. The text of the JST URL was fetched separately.
