# Procurement check

Checked 2026-11-13. Quantities are per board. PCBWay must quote the requested board count plus assembly attrition and packaging minimums. Public stock is not PCBWay inventory or a reservation.

L1 now uses Bourns SRN4018-2R2M with its dedicated land pattern instead of the discontinued Murata part. See [inductor-selection.md](inductor-selection.md). Q1/Q2 use full Nexperia ordering codes. C5/C31/C32 use the Raspberry Pi reference capacitor.

## Revised parts

| Exact MPN | References | JLCPCB stock | LCSC stock |
|---|---|---:|---:|
| SRN4018-2R2M | L1 | 1,588 | 200 |
| GRM155R60J475ME47D | C5 C31 C32 | 403,983 | 386,350 |
| RC0402FR-070RL | R19 | 1,628,191 | 779,300 |
| RC0402FR-072K2L | R9 R20 | 426,081 | 363,400 |
| RC0402FR-07330RL | R33 | 4,833,841 | 4,709,200 |
| BSS84,215 | Q1 | 5,661 | 5,660 |
| 2N7002,215 | Q2 | 198,305 | 193,550 |

Nexperia's [BSS84](https://www.nexperia.com/chemical-content/BSS84.html) and [2N7002](https://www.nexperia.com/chemical-content/2N7002.html) tables confirm these ordering codes. BSS84 is marked "Not for Design In", but remains stocked. Keep the specified part for this prototype; revisit it for long-term production.

## Global sourcing needed

| Part | Evidence | Sourcing instruction |
|---|---|---|
| Y1, ABM8-272-T3 | JLCPCB stock 1. [DigiKey](https://www.digikey.com/en/products/detail/abracon-llc/ABM8-272-T3/22472366) reported 23,357, active, USD 0.69 at quantity 1. | Source the exact Abracon part globally. |
| R14, RC0402FR-073K83L | JLCPCB stock 19. [Arrow](https://www.arrow.com/en/products/rc0402fr-073k83l/yageo.html) reported 10,877. [Findchips/Mouser](https://www.findchips.com/detail/RC0402FR-073K83L/YAGEO-Corporation) reported 317,754, USD 0.10 at quantity 1. | Confirm packaging and date code. Mouser figures came from its distributor feed. |
| L2, AOTA-B201610S3R3-101-T | JLCPCB stock 172, reported MOQ 26. | Confirm exact marked Abracon part and assembly attrition. |
| R3/R4, RC0402FR-0727RL | JLCPCB stock 36,261, no LCSC stock reported. | Allow global sourcing. |
| R15, RC0402FR-0746K4L | JLCPCB stock 432, no LCSC stock reported. | Allow global sourcing. |
| J5/J6, 61302021121 / 61300411121 | JLCPCB stock 346 / 1,465. | Include through-hole assembly in the quote. |

## Design-driving parts

| Exact MPN | JLCPCB stock | LCSC stock |
|---|---:|---:|
| RP2350A | 5,431 | 5,345 |
| W25Q128JVSIQ | 68,940 on the larger exact listing | Not reported |
| APS6404L-3SQR-SN | 2,656 | 2,656 |
| BQ24074RGTR | 4,431 | 4,194 |
| TPS63001DRCR | 8,419 | 8,158 |
| ESP32-C3-WROOM-02-N4 | 12,806 | 12,806 |
| USBLC6-2SC6, STMicroelectronics | 42,205 | 39,075 |

The remaining resistor/capacitor MPNs, WS2812C-2020-V6, B3U-1000P and J1–J4 returned exact stocked listings during the BOM check. Same-name parts from another manufacturer are not approved substitutes.

## PCBWay quote

PCBWay's [sourcing policy](https://www.pcbway.com/pcb_prototype/Electronic_Components.html) allows international distributors and customer-recommended sources. Request manufacturer, full MPN, quantity including attrition, packaging, lot/date code, landed price and delivery date. Require approval before any substitution.

Refresh stock before ordering. No quote, sourcing approval or order has been placed.
