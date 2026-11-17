# L1 replacement selection

Checked 2026-11-13 UTC. Recommend **Bourns SRN4018-2R2M**, LCSC/JLCPCB **C913207**, for the TPS63001DRCR 3.3 V buck-boost. Use stock KiCad footprint **`Inductor_SMD:L_Bourns-SRN4018`**. This is an electrical substitute requiring a footprint change, not a drop-in replacement for the existing 1812 pads.

L1 connects `PWR_L1` to `PWR_L2`; U5 takes power from the BQ24074 `SYS` rail. `tools/circuits.py` still specifies Murata LQH44PN2R2MP0L with `L_1812_4532Metric`, which does not match its 4 x 4 mm body. This recommendation does not change the design files or authorize procurement under `fab/procurement.md`'s no-substitution policy.

## Verified ratings and availability

The [Bourns manufacturer datasheet](https://www.bourns.com/docs/product-datasheets/srn4018.pdf), revision 10/26, specifies:

| Parameter | SRN4018-2R2M |
|---|---|
| Inductance | 2.2 µH ±20%, tested at 100 kHz / 1 V |
| RMS current | 2.9 A at 40°C temperature rise |
| Saturation current | 3.0 A at 30% inductance drop |
| DCR | 44 mΩ maximum |
| Construction | Semi-shielded, ferrite core |
| Body | 4.0 ±0.2 x 4.0 ±0.2 mm |
| Maximum height | 1.88 mm |
| Operating temperature | -40°C to +125°C, including self-heating |

The search result for [Arrow's exact-part listing](https://www.arrow.com/en/products/srn4018-2r2m/bourns.html) reports Active. The current manufacturer datasheet includes this MPN but does not separately guarantee its lifecycle status.

`lookup_parts` returned these exact-MPN stock and USD price snapshots:

| Source | Stock | Unit price | Purchasing constraint |
|---|---:|---:|---|
| JLCPCB, C913207 | 1,588 | $0.3518 at 1+ | Extended library; assembly minimum 5 |
| LCSC, C913207 | 200 | $0.3552 at 5+ | MOQ 5, multiple 5 |

[LCSC listing](https://www.lcsc.com/product-detail/C913207.html). Stock is not reserved and does not reflect PCBWay inventory. Recheck quantity, packaging and price before ordering.

## Peak-current check

The [TI TPS63000/01/02 datasheet](https://www.ti.com/lit/ds/symlink/tps63001.pdf), sections 6.5 and 8.2.2.2, lists switch current limit **1.6 A minimum, 1.8 A typical, 2.0 A maximum**, with the stated test condition VIN = VINA = 3.6 V and TA = 25°C. Do not describe 2.2 A as this table's guaranteed worst-case limit. TI recommends saturation current at least 20% above calculated operating peak current.

For a conservative **2.2 A design peak budget**, the recommended saturation threshold is 1.2 x 2.2 = **2.64 A**. The selected 3.0 A rating exceeds it. Its 2.9 A RMS rating also exceeds the approximately 1.2 A battery-current target. RMS and saturation ratings use different thermal and inductance-drop criteria; they are not interchangeable.

Battery average current is not the inductor peak, especially in buck operation. In boost, TI's equation is `Ipeak = Iout / [eta * (1 - D)] + Vin * D / (2 * f * L)`, with `D = 1 - Vin/Vout`. Use minimum SYS voltage, maximum output load, minimum effective inductance and minimum switching frequency. Section 6.5 gives 1.25 MHz minimum oscillator frequency; section 8.2.2.2's parenthetical 2.5 MHz conflicts with that table and should not drive a worst-case ripple calculation.

At 3.3 V output, the ideal boost ripple term is at most 0.188 A using 1.25 MHz and 1.76 µH, before DC-bias reduction. If 1.2 A were the converter input average in boost, the estimated peak would therefore be about 1.39 A. This is an illustration, not a load guarantee: the actual minimum SYS voltage, load waveform and hot inductance remain to be checked. A stronger inductor does not increase the TPS63001's output-current capability. Verify startup, radio/SD load steps, efficiency, EMI and temperature on the assembled board. Semi-shielding can change EMI relative to the original part.

## Stock footprint verification

The [KiCad stock footprint source](https://github.com/KiCad/kicad-footprints/blob/master/Inductor_SMD.pretty/L_Bourns-SRN4018.kicad_mod) has two rectangular pads:

| Geometry | Dimension |
|---|---|
| Pad centers | X = -1.525 and +1.525 mm, Y = 0 |
| Each pad | 1.50 x 3.60 mm |
| Center spacing | 3.05 mm |
| Copper outer span | 4.55 mm |
| Copper inner gap | 1.55 mm |

These match the manufacturer's recommended layout: 4.55 mm overall span, 1.50 mm pad length and 3.60 mm pad width. The **2.40 mm** dimension is a component-terminal dimension, not the recommended copper gap. Allow the 4.2 x 4.2 mm maximum body and 1.88 mm maximum height, and recheck nearby clearances and routing after changing L1. Do not retain `L_1812_4532Metric` or select a generic footprint from the body size alone.
