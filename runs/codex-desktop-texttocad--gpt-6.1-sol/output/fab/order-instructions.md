# PCBWay order instructions — Atlas2350 Rev A

## Quote request

Request **five fully assembled prototype boards**. Upload the manufacturing ZIP
for PCB fabrication **and turnkey component sourcing/assembly**, not bare boards
alone. PCBWay supplies and fits **115 components per board in 53 BOM groups**,
including all SMT parts, J5/J6/J7 through-hole headers and USB shell stakes.
No DNP, customer-supplied component, or customer-soldered population is planned.

Specify four-layer FR-4, 80 × 75 mm chamfered outline, 1.6 mm finished thickness,
ENIG, green soldermask, white silkscreen, lead-free assembly, IPC Class 2,
outer 1 oz / inner 0.5 oz copper. Quote the requested nominal stackup in
`fabrication-notes.md`; there is no controlled-impedance certification.

**Mandatory selective via process:** resin fill and copper cap all **334 holes**
in `drill/filled-capped-hole-schedule.csv`, IPC-4761 Type VII. These comprise
322 routing vias plus 12 U6 thermal holes. Do not fill the 40 component lead/shell
holes. Keep all seven NPTH features unplated. A cheaper open/tented-via process
is not an approved substitution. Include bare-board electrical testing against
`Atlas2350.ipc` and solder-joint inspection appropriate to fine-pitch packages.

## Before approving the quotation

- Confirm exact MPN availability for every BOM line, including RP2350A,
  APS6404L-3SQR-SN, ESP32-C3-WROOM-02-N4 and WS2812B-2020-V6. Any proposed
  substitution requires explicit engineering review; do not silently substitute.
- Confirm fill/cap capability, stencil and solder profile, THT assembly,
  QFN/module thermal-pad inspection and panel/fixture clearance for U6's
  approximately 6.1 mm antenna overhang beyond the board's top edge.
- Reconcile the surface-only `assembly/pcbway-centroids.csv` with the complete
  BOM, separate THT placement records, assembly drawings and actual pin1 data.
  Apply any panel offset to copper, drills, paste and placement together.
- Check source revision and supplied SHA-256 checksums. Do not rescale plots
  because the Gerber-job dimensions include the outline stroke thickness.

## Programming, accessories and acceptance

No application or ESP-AT programming image is supplied. Quote assembly and
electrical inspection without promising firmware-dependent functional testing;
use `test-plan.md` for first-article qualification once suitable firmware exists.
No battery, microSD card, cables, screws, or mating adapters are in the BOM.
The battery connector is custom: pin1 BAT+, pin2 GND, pin3 cell-mounted 10k NTC,
for an external protected 1S 4.2V LiPo of at least 500mAh.

Ship boards without a battery in suitable antistatic protective packaging.
Review and qualify first articles before a larger production order. This package
does not establish a supplier quote, stock commitment, DFM approval, functional
performance, USB/RF certification, or safety certification.
