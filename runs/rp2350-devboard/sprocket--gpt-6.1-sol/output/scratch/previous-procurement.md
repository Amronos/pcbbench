# Procurement check

Prototype BOM checked with `lookup_parts` on 2026-11-13. External sourcing checked on 2026-11-13 UTC against `fab/BOM.csv` and `tools/circuits.py`. Each of L1, Y1, R14, Q1 and Q2 requires one part per board. Board count is unspecified; PCBWay must quote part quantities for the requested board count, allowing for assembly attrition and packaging minimums. Stock snapshots are not PCBWay inventory or reservations. Only L1 has a proposed replacement, at the user's request. No CAD or BOM changes were made, and no replacement is released for assembly.

## Items requiring sourcing confirmation

| References | Manufacturer MPN | JLCPCB stock | LCSC stock | Issue |
|---|---|---:|---:|---|
| L1 | Murata LQH44PN2R2MP0L | 0 | 0 | Discontinued. Proposed active replacement and footprint hold below. |
| Y1 | Abracon ABM8-272-T3 | 1 | 0 | JLCPCB stock below its assembly minimum of 5; reported MOQ 23. Exact-part external stock below. |
| R14 | Yageo RC0402FR-073K83L | 19 | 0 | JLCPCB stock below its assembly minimum of 20. Exact-part external stock below. |
| R3 R4 | Yageo RC0402FR-0727RL | 36,261 | 0 | JLCPCB-only stock at checked sources. |
| R15 | Yageo RC0402FR-0746K4L | 432 | 0 | JLCPCB-only stock at checked sources. |
| L2 | Abracon AOTA-B201610S3R3-101-T | 172 | 0 | JLCPCB-only stock; reported MOQ 26 and assembly minimum 5. |
| U2 | Winbond W25Q128JVSIQ | 68,940 / 90 | 0 / 0 | Two exact listings, C97521 and C113767; no LCSC stock. |
| Q1 Q2 | Nexperia BSS84 / 2N7002 | See below | See below | Recommend explicit purchasing codes BSS84,215 / 2N7002,215. BOM remains unchanged. |

Nexperia BSS84,215 (C493579) had JLCPCB/LCSC stock 5,661/5,660; 2N7002,215 (C65189) had 198,305/193,550. These ordering suffixes are absent from the source MPNs. Same-name parts from other manufacturers do not meet the BOM.

## L1 active replacement recommendation and footprint hold

Checked 2026-11-13 UTC. Recommend **Murata LQH44PN2R2MPRL** as the active electrical/package replacement candidate, subject to land-pattern correction or explicit assembly qualification. It is not approved as a drop-in on the current generic footprint.

The [original Murata page](https://pim.murata.com/en-us/pim/details/?partNum=LQH44PN2R2MP0L) marks LQH44PN2R2MP0L discontinued, last order 2023-09-30, end of production 2024-03-31. [Murata withdrawal notice D05558-A-A2127](https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/3951/D05558-A-A2127.pdf), issued 2022-10-01, confirms these dates. Removing `L` to obtain LQH44PN2R2MP0 does not establish an active orderable replacement. No manufacturer evidence was found to validate LQH44PN2R2MP0D; do not order a guessed suffix.

The [current Murata page](https://pim.murata.com/en-us/pim/details/?partNum=LQH44PN2R2MPRL) explicitly says "In Production" and lists full codes LQH44PN2R2MPRL and LQH44PN2R2MPRK. `L` means 180 mm embossed tape, 1,000/reel; `K` means 330 mm tape, 3,500/reel. Use the verified `L` code for the recommendation, not the unsuffixed family name.

### Public replacement stock

Checked 2026-11-13 UTC. [Findchips' exact-part distributor feed](https://www.findchips.com/detail/LQH44PN2R2MPRL/Murata-Manufacturing-Co-Ltd) reports the following reputable distributor offers. These are feed snapshots, not reserved stock or PCBWay quotes; confirm directly before ordering. Higher price breaks do not imply that quantity is in stock.

| Supplier and purchasing code | Reported stock | USD unit price in feed | Supplier URL |
|---|---:|---|---|
| Mouser, 81-LQH44PN2R2MPRL | 19 | 0.4600 at 1, 0.3830 at 10, 0.3640 at 25 | [Exact listing](https://www.mouser.com/ProductDetail/Murata-Electronics/LQH44PN2R2MPRL) |
| Newark, cut tape 57AK3257 | 6 | 0.3334 at 1, 0.2800 at 10, 0.2674 at 25 | [Exact listing](https://www.newark.com/murata/lqh44pn2r2mprl/power-ind-2-2uh-semishielded-3/dp/57AK3257) |

The feed's Mouser description says "30%", while the manufacturer's inductance tolerance is ±20%. Use the manufacturer specification and exact MPN, not that distributor description. These small stocks may cover only a few prototypes after attrition; get a firm global-sourcing quote for the board count.

### Electrical suitability for this circuit

The actual root PCB has U5 TPS63001DRCR at (124, 120) mm, fixed 3.3 V output. Its pins 1 and 10 connect to `/3V3`; VIN/VINA/EN pins 5/8/6 connect to `/SYS`; PS/SYNC pin 7 connects to GND. L1 at (124, 114) mm connects `/PWR_L1` to `/PWR_L2`, between U5 pins 4 and 2. This agrees with `tools/circuits.py`: SYS comes from the BQ24074 power path fed by USB or a protected 1S LiPo. The design does not define a guaranteed minimum SYS voltage or maximum combined 3.3 V load.

| Parameter | LQH44PN2R2MPRL manufacturer rating | Relevance |
|---|---|---|
| Inductance | 2.2 µH ±20%, tested at 100 kHz | Same nominal value as the current circuit and TI's typical application |
| DCR | 42 mΩ ±20%, 50.4 mΩ maximum | At 2 A RMS, winding DC loss is approximately 0.202 W at the specified maximum DCR, before temperature increase and AC/core loss |
| Inductance-change current | 3.3 A | Defined as inductance within ±30% of initial value at ordinary temperature, not a hard saturation boundary |
| Temperature-rise current | 2.4 A | Defined by ≤40°C self-heating at ordinary temperature; not an unrestricted hot-ambient current guarantee |
| Temperature | -40 to +85°C ambient in reference specification; component including self-heating ≤125°C | Check actual temperature and derating on the built board |

Source: [Murata reference specification JELF243A-0190A-01](https://pim.murata.com/asset/pim4/inductor/JELF243A-0190_PDF_INDUCTOR), sections 3 and 7.4-7.5. The [TI TPS63001 datasheet](https://www.ti.com/lit/ds/symlink/tps63001.pdf), SLVS520C, sections 6.5 and 8.2.2.2, calls for low DCR and an inductance-change/saturation rating at least 20% above the calculated boost peak current. Switch current limit is 1.6/1.8/2.0 A min/typ/max under the stated 3.6 V, 25°C test condition. This is an average switch-current limit, not a universal 2 A instantaneous peak clamp.

Use TI's equation: `D = 1 - VIN/VOUT`; `Ipeak = IOUT / [η(1-D)] + VIN·D / (2·f·L)`. For an illustrative 2.4 V SYS, 3.3 V output, 0.8 A load, η = 0.90, minimum oscillator frequency 1.25 MHz and tolerance-low L = 1.76 µH, Ipeak ≈1.37 A; 20% margin requires ≈1.65 A, below 3.3 A. This is an example, not the board's established worst case. Recalculate at the actual minimum SYS voltage and total load, including ripple, bias/temperature-dependent inductance, startup and transients. TI section 8.2.2.2 mentions 2.5 MHz, but its electrical table specifies a 1.25 MHz minimum and 1.5 MHz typical oscillator; the example conservatively uses the table minimum.

### Actual copper versus manufacturer terminals

Read directly from root `sprocket2350.kicad_pcb`, not inferred from the library name. Coordinates below are relative to L1 center, in mm; x runs between terminals. No root files were saved.

| Geometry | Actual or specified dimensions |
|---|---|
| Existing `Inductor_SMD:L_1812_4532Metric` | Pad centers x = ±2.1375, y = 0; each 1.125 × 3.4, roundrect radius ≈0.25; center spacing 4.275 |
| Existing pad extents | Left x = -2.700 to -1.575; right x = +1.575 to +2.700; y = ±1.700; inner gap 3.150, outer span 5.400 |
| Murata body, section 5 drawing | 4.0 ±0.2 × 4.0 ±0.2, height 1.65 ±0.15; upper core width 3.7 ±0.2 |
| Murata underside terminals | Each extends 1.1 ±0.2 inward from its body edge. Nominal right x = +0.900 to +2.000, left mirrored; nominal inner gap 1.800, outer span 4.000. Profile has reference y spans 3.3 outer, 2.4 inner and 1.6 central |
| Murata recommended lands, section 12.1 drawing | Outer span 4.400, inner gap 1.500; each land extends 1.450 along x, tapering from 3.3 outer y span to 2.7 inner y span |

Centered nominal terminal-to-copper overlap along x is only `min(2.700, 2.000) - max(1.575, 0.900) = 0.425 mm` per side, **38.6% of the nominal 1.1 mm terminal depth**. The conservative central 1.6 mm-wide terminal strip gives at least 0.425 × 1.6 = **0.680 mm² nominal overlap per terminal**, clear of the pad's rounded corners. With the 3.8 mm minimum body span, centered outer terminal x becomes 1.900 and overlap falls to 0.325 mm before placement error. These are geometric checks, not guaranteed solder-joint areas or a tolerance-stack qualification.

The current pad's inner edge is **0.825 mm farther outward** than Murata's recommended inner edge, and its outer edge is **0.500 mm farther outward** than the recommended outer edge. The generic fab outline is 4.5 × 3.2, not the actual 4 × 4 body. Its courtyard y extent is ±1.95, so a maximum-width 4.2 mm body exceeds it by 0.15 mm on each side even before assembly clearance.

**Fit verdict:** both terminals have positive nominal copper overlap, but the existing generic 1812 pattern does not match Murata's recommended lands or body/courtyard. Do not call it a verified production fit for either the old or new 4040 part. Prefer a dedicated Murata land pattern during the already-required power-stage layout revision. If retaining the present copper, require explicit PCBWay/Murata approval and solder-joint qualification for the reduced heel overlap and placement tolerance. The existing [manufacturing hold](release-review.md) on long, narrow switching paths and U5 thermal connections also remains. An inductor purchase does not clear it.

## Exact Y1 sources outside JLCPCB/LCSC

Checked 2026-11-13 UTC. Keep Abracon ABM8-272-T3. The [manufacturer datasheet](https://abracon.com/datasheets/ABM8-272-T3.pdf), revision B dated 2024-09-16, identifies the exact part and 3,000-piece reel packing.

| Supplier | Public stock | Public unit prices | Evidence and limits |
|---|---:|---|---|
| DigiKey | 23,357 | USD 0.69000 at 1, 0.60100 at 10, 0.52230 at 100; full reel USD 0.42454 at 3,000 | [Exact listing](https://www.digikey.com/en/products/detail/abracon-llc/ABM8-272-T3/22472366), directly verified, status Active. Cut tape minimum 1. Backorders currently unavailable; Digi-Reel adds USD 7. |
| Braemac Americas, formerly Symmetry Electronics | 4,101 | Displayed $0.69 at 1, $0.60 at 10, $0.52 at 100; currency not explicitly identified | [Exact listing](https://americas.braemac.com/products/abracon/abm8-272-t3/), directly verified. Do not assume USD from the dollar symbol alone. |

## Nexperia full purchasing codes

Checked 2026-11-13 UTC. Recommend the following codes for procurement without editing the BOM's base type names:

| Reference | Recommended full order code | Manufacturer 12NC | Manufacturer verification | LCSC exact-part stock and USD unit prices |
|---|---|---|---|---|
| Q1 | BSS84,215 | 933946360215 | [Nexperia OPN/12NC table](https://www.nexperia.com/chemical-content/BSS84.html) confirms BSS84, SOT23 / TO-236AB | [C493579](https://www.lcsc.com/product-detail/C493579.html): 5,660; USD 0.0695 at 10+, 0.0413 at 3,000+; minimum/multiple 10 |
| Q2 | 2N7002,215 | 934003470215 | [Nexperia OPN/12NC table](https://www.nexperia.com/chemical-content/2N7002.html) confirms 2N7002, SOT23 / TO-236AB | [C65189](https://www.lcsc.com/product-detail/C65189.html): 193,550; USD 0.0166 at 50+, 0.0111 at 3,000+; minimum/multiple 50 |

The [Nexperia SOT23 packing document](https://assets.nexperia.com/documents/packing-information/SOT23_215.pdf), revision 3.0 dated 2024-08-20, defines suffix `,215`: 180 mm / 7-inch reel, 8 mm carrier tape, normally 3,000 devices. It changes packing, not the electrical base type. Supplier cut tape or re-reeling does not authorize another manufacturer or device variant. The [BSS84 product page](https://www.nexperia.com/product/BSS84) says "Not for Design In"; flag this lifecycle risk to PCBWay, without substituting another MOSFET.

## Exact R14 sources outside JLCPCB/LCSC

Checked 2026-11-13 UTC. Both listings identify Yageo RC0402FR-073K83L, not a different resistor with the same value. The [Yageo part specification](https://yageogroup.com/component-documentation/download/specsheet/RC0402FR-073K83L) confirms 3.83 kΩ, ±1%, 0402/1005 and 0.063 W.

| Supplier and order code | Public stock | Public unit price and quantity | Evidence |
|---|---:|---|---|
| Arrow, RC0402FR-073K83L | 10,877 total: 77 shipping from USA, 10,800 from Japan | USA cut strip, minimum 1: GBP 0.0031 at 1+, GBP 0.0019 at 10+, GBP 0.0008 at 25+, excluding VAT | [Supplier page](https://www.arrow.com/en/products/rc0402fr-073k83l/yageo.html), directly readable. Rendered currency was GBP; no USD conversion inferred. USA lot date code 2111; request PCBWay's date-code acceptance. |
| Mouser, 603-RC0402FR-073K83L | 317,754 reported | USD 0.1000 at 1, 0.0130 at 10, 0.0070 at 100 | [Findchips distributor feed](https://www.findchips.com/detail/RC0402FR-073K83L/YAGEO-Corporation). [Mouser listing](https://www.mouser.com/ProductDetail/YAGEO/RC0402FR-073K83L) blocked automated access, so quantity and price are feed snapshots, not direct supplier confirmation. |

TME also has an [exact-part listing](https://www.tme.eu/en/details/rc0402fr-073k83l/smd-resistors/yageo/). Search/Findchips reported 6,642 units, but the directly fetched page returned `null` stock and no prices. Do not treat that rendering as confirmed zero stock or confirmed availability.

## PCBWay sourcing instructions

PCBWay's [Electronic Components Sourcing policy](https://www.pcbway.com/pcb_prototype/Electronic_Components.html), checked 2026-11-13, permits international sourcing, customer-recommended distributors, consigned parts and mixed sourcing. It names Digi-Key, Mouser, Farnell, Arrow and Avnet. It says no substitutes will be used without approval. Its international procurement estimate is 5-7 business days, sometimes 7-10 with customs; this is not a committed lead time for these parts.

Allow global sourcing for the exact original MPNs, using the full Nexperia purchasing codes listed above for Q1 and Q2. The proposed L1 replacement still requires approval and does not clear the footprint or power-stage holds. Ask PCBWay to confirm manufacturer, full order code, available quantity including attrition, packaging, lot/date code, landed price and delivery date before releasing assembly. Do not approve equivalents or replacement MPNs. Listed supplier prices are public component prices, not PCBWay quotes, and exclude any unlisted shipping, tax, duty or assembly charges.

## Other checks

| Design-driving part | JLCPCB stock | LCSC stock |
|---|---:|---:|
| RP2350A | 5,431 | 5,345 |
| APS6404L-3SQR-SN | 2,656 | 2,656 |
| BQ24074RGTR | 4,431 | 4,194 |
| TPS63001DRCR | 8,419 | 8,158 |
| ESP32-C3-WROOM-02-N4 | 12,806 | 12,806 |

All 11 Yageo resistor MPNs returned exact matches; eight had stock at both sources. All seven Murata capacitor MPNs had stock at both sources, with at least 19,960 units of each at LCSC.

STMicroelectronics USBLC6-2SC6 (C7519) had JLCPCB/LCSC stock 42,205/39,075. Other manufacturers use the same MPN text but do not meet the BOM. Worldsemi WS2812C-2020-V6, Omron B3U-1000P and J1-J4 had stock at both sources. Würth headers J5/J6 had JLCPCB stock 346/1,465; LCSC stock was not reported.

Refresh this check after part changes and before ordering. Stock does not establish electrical suitability, footprint compatibility, lifecycle status, or batch availability.
