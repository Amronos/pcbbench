# Project-local KiCad library

This directory vendors only the symbols and footprints used by Aster2350. `sym-lib-table` and `fp-lib-table` refer to it through `${KIPRJMOD}`. Embedded schematic symbols and PCB footprints match the local library; 3D model links were removed so they are not a portability requirement.

Source: KiCad standard symbols and footprints bundled with the installed KiCad application. See https://www.kicad.org/libraries/license/ for CC-BY-SA 4.0 library terms and the board-use exception. The hardware design and manufacturing outputs are not made subject to library-source copyleft solely by using the footprints. These source-library modifications retain the library license.

Local modifications:

- All used symbols are flattened from their standard-library inheritance and named under `Aster`; electrical pin types and manufacturer pin numbers are preserved.
- `APS6404L_3SQR`: new 8-pin PSRAM symbol, manufacturer pinout; 3.3 V SOP8 variant selected.
- `TLV61046A`: new 6-pin boost symbol, TI datasheet pinout.
- TPS22919 QOD is modeled as **passive**, rather than the standard symbol's open-collector output. It is the discharge-path connection, not a digital logic output; this corrects an inappropriate ERC pin-type conflict when tied to the output rail as TI permits. ON and OUT retain their real input/power-output roles.
- ESP32-C3-WROOM-02 thermal through holes inside pad 19 are removed; the full copper ground pad and segmented paste apertures remain. Ground vias are outside open pads instead.
- TPS63060's complex optional exposed-pad fingers are simplified to the 1.7 × 2.15 mm central PGND copper pad with six segmented paste apertures. The actual ten lead-pad positions/shapes remain from the TI land-pattern footprint.
- 3D model references are omitted; they are not used for electrical/manufacturing verification.
- JST SH symbols include a hidden stacked `MP` shield/mounting-pad pin on ground, matching the two grounded mounting pads in each PCB footprint.
- Project-local bare mounting-hole and fiducial footprints are included. Fiducial copper clearance reserves its 2 mm mask opening; they are PCB features, not purchased parts.

Do not replace these footprints with automatically fetched generic packages before manufacture. The USB-C shell slots, RP2350 60-pin pin numbering, SOP vs SOIC memory widths and RF antenna keepout are particularly important.
