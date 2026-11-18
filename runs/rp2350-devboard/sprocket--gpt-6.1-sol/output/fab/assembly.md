# PCBWay assembly

First prototype. Complete PCBWay's sourcing and fabrication [release checks](release-review.md) before ordering. Qualify the built prototype before production release.

PCBWay must supply and assemble every reference in [BOM.csv](BOM.csv), including through-hole headers J5/J6. No part is DNP or reserved for user assembly.

Use the listed manufacturer and MPN. Substitutions require approval. Quantities are per board; account for the board count and assembly attrition.

The BOM is exported from the final schematic and matched to the board. PCBWay must confirm sourcing, through-hole assembly and placement data before release.

Use `assembly/sprocket2350-F_Fab.png` with `positions.csv` to confirm top-side references, rotations and pin 1. The bottom drawing has no fitted components. J3 is a custom BAT+/GND/NTC connector, not a standard two-wire battery connector.

Do not substitute older WS2812 revisions, a different PSRAM pinout, or an unmarked core-regulator inductor. L2's winding dot faces the lower-left 1V1 end at the shown rotation. Do not reverse it to match a different library's pad numbering.

Require IPC-4761 Type VII nonconductive resin fill, planarization and copper capping at all 18 sites in [via-in-pad.csv](via-in-pad.csv). These include capacitor pads, the USB fanout, R32, U2 and U4/U5 thermal pads. Review exposed-pad paste coverage before reflow. Ordinary vias may be tented.

No battery or firmware image is included. The protected LiPo pack is external, and firmware must implement the input-current and radio-enable policy in the README.
