# Raspberry Pi Radio Module 2 (RM2) design notes

Written 2026-11-10. Sources, all saved in this folder:

- `rm2-datasheet.pdf`: RM2 datasheet, release 7, build 20/02/2026. Cited below as DS.
- `rm2-kicad.zip`, `rm2-step.zip`: Raspberry Pi's KiCad symbol, footprint and STEP model, from <https://pip.raspberrypi.com/categories/1223-design-files> (no login needed).
- `pico-2-w-schematic.pdf`, `pico-2-w-datasheet.pdf`: Pico 2 W reference design.
- `cyw43439-datasheet.pdf`: Infineon CYW43439 datasheet 002-30348 Rev. *D. Cited as CYW.
- `rm2-product-brief.pdf`.

Items marked "my recommendation" are not in any Raspberry Pi document.

## Library parts

| Part | Path |
|---|---|
| Symbol `devboard:RM2` | `lib/devboard.kicad_sym` |
| Footprint `devboard:RaspberryPi_RM2` | `lib/devboard.pretty/RaspberryPi_RM2.kicad_mod` |
| 3D model, Raspberry Pi's STEP unchanged | `lib/3d/RaspberryPi_RM2.step` |

The footprint origin is the centre of the 14.5 x 16.5 mm module. The antenna points to -Y, which is up in the footprint editor. `verify.py` compares all 21 pads and pin names with DS figure 6, DS table 2 and Raspberry Pi's own KiCad files.

## Pins and Pico 2 W style hookup

Pin 1 is at the top left, next to the antenna. Numbers run counter-clockwise seen from the top: 1 to 7 down the left edge, 8 to 14 along the bottom, 15 to 21 up the right edge (DS 2.5).

| Pin | Name | Function | Connect to |
|---|---|---|---|
| 1 | GND | Ground | GND plane |
| 2 | NC | No connect | Solder the pad, no net |
| 3 | SCLK | gSPI clock in | GPIO29 (WL_CLK), direct |
| 4 | GND | Ground | GND plane |
| 5 | DI | gSPI data in | GPIO24 (WL_D), direct |
| 6 | DO | gSPI data out | GPIO24 (WL_D) through 470 Ω |
| 7 | GND | Ground | GND plane |
| 8 | GPIO0 | CYW43439 GPIO0, host controlled | Optional. LED on Pico 2 W. Leave open if unused |
| 9 | CS | gSPI chip select | GPIO25 (WL_CS), direct |
| 10 | nIRQ | Host wake interrupt | GPIO24 (WL_D) through 10 kΩ |
| 11 | GND | Ground | GND plane |
| 12 | WL_ON | Wi-Fi regulator enable, WL_REG_ON | GPIO23 (WL_ON), direct |
| 13 | BT_ON | Bluetooth regulator enable, BT_REG_ON | GPIO23 (WL_ON), same net as pin 12 |
| 14 | VDDIO | I/O supply, 1.8 V or 3.3 V ±5% | 3V3, the RP2350 IOVDD rail |
| 15 | GND | Ground | GND plane |
| 16 | VIN | Main supply, 3.0 V to 4.8 V | 3V3 |
| 17 | GPIO2 | CYW43439 GPIO2 | Optional. VBUS sense on Pico 2 W. Leave open if unused |
| 18 | GPIO1 | CYW43439 GPIO1 | Optional. SMPS power-save control on Pico 2 W. Leave open if unused |
| 19 | NC | No connect | Solder the pad, no net |
| 20 | NC | No connect | Solder the pad, no net |
| 21 | GND | Ground | GND plane |

External parts:

- 470 Ω 1% between pin 6 and WL_D. Required (DS table 1 and 2). R22 on Pico 2 W.
- 10 kΩ 1% between pin 10 and WL_D. Required. R23 on Pico 2 W.
- No pull resistors are required. WL_REG_ON and BT_REG_ON each have a 200 kΩ pull-down inside the CYW43439 (CYW pin descriptions, page 12), and Pico 2 W fits none on WL_ON, WL_CS, WL_CLK or WL_D.
- Decoupling: DS specifies none and its introduction says the module needs "only SPI, power, and reset signals". My recommendation: 100 nF plus 4.7 µF at pin 16 and 100 nF at pin 14, close to the pads. Pico 2 W feeds the CYW43439 VBAT pins through a 600 Ω ferrite with 4.7 µF, and has 100 nF at its VDDIO pin. I assume these parts are inside the module. DS does not publish the module schematic.
- Unused pins: leave GPIO0 to GPIO2 and the three NC pins unconnected. GPIO1 and GPIO2 also select the chip's debug mode at power-up (CYW table 18), so my recommendation is to add no pull-ups to them.

On Pico 2 W, GPIO29 is shared with the VSYS/3 ADC input through a FET that WL_CS controls. A board that does not measure VSYS does not need that FET.

## How Pico 2 W wires the data line, and what RM2 does internally

Pico 2 W sheet 2, U4A (CYW43439):

| CYW43439 ball | gSPI role | Pico 2 W connection |
|---|---|---|
| SDIO_CLK | clock | WL_CLK, direct |
| SDIO_CMD | data in | WL_D, direct |
| SDIO_DATA2 | strap, low at reset selects gSPI | WL_D, direct |
| SDIO_DATA0 | data out | WL_D through R22 470 Ω |
| SDIO_DATA1 | interrupt | WL_D through R23 10 kΩ |
| SDIO_DATA3 | chip select | WL_CS, direct |
| WL_REG_ON, BT_REG_ON | enables | both on WL_ON |

RM2 does not do this internally. Data in, data out and nIRQ come out on separate pins 5, 6 and 10, and DS tables 1 and 2 tell you to join them at one GPIO with the same 470 Ω and 10 kΩ resistors. WL_ON and BT_ON are also separate pins that you tie together. The SDIO_DATA2 strap has no module pin, so the module must set it itself. This is my inference. DS does not say so.

## Supply and current

- VIN: 3.0 V to 4.8 V. Below 3.2 V RF performance drops (DS 2.6), so keep the 3V3 rail tolerance and droop tight.
- VDDIO: 1.8 V ±5% or 3.3 V ±5%. It must match the host I/O voltage.
- Current from VIN: 271 mA transmitting MCS7 at 16 dBm, 43 mA receiving, 1.19 mA average in power save PM1 DTIM1 (DS 1.1). CYW table 38 gives the worst case as 320 mA transmitting 1 Mbps at 19.5 dBm with VBAT = 3.6 V. My recommendation: budget 400 mA peak for the module on the 3V3 regulator.
- Logic levels at VDDIO = 3.3 V: VIH 2.0 V, VIL 0.8 V, VOH VDDIO - 0.4 V and VOL 0.4 V at 2 mA.

## Absolute maximum ratings

DS has no absolute maximum table for the module. These are the CYW43439 chip limits (CYW table 20). Treat them as an upper bound for the module pins.

| Rating | Value |
|---|---|
| VBAT, module VIN | -0.5 V to +6.0 V |
| VDDIO | -0.5 V to +3.9 V |
| I/O undershoot / overshoot | -0.5 V / VDDIO + 0.5 V, at most 25% duty |
| Junction temperature | 125 °C |
| ESD (DS table 5) | 1000 V HBM, 300 V CDM, 30 V machine model |
| Operating / storage temperature (DS table 6) | -30 °C to +70 °C / -40 °C to +125 °C |
| Humidity (DS table 6) | under 85% operating, under 60% storage |

The 1 kV HBM rating is low. Handle the module with ESD precautions.

## Mechanical

- Body 14.5 mm wide x 16.5 mm long x 2.55 mm high including the shield can. DS calls these approximate and gives no tolerances.
- 21 castellated pads, ENIG, 1.5 mm pitch. 7 on the left, 7 on the bottom, 7 on the right. The antenna end has no pads.
- Land pattern (DS figure 6): every pad 2.0 x 1.0 mm, reaching 0.5 mm outside the module edge. Side pad columns centred 6.75 mm from the module centre line. Pin 7 and 15 centres 1.8 mm above the bottom edge. Pin 8 centre 2.75 mm from the left edge.
- The shield can covers 12.0 x 10.0 mm (from the STEP model).

## Antenna and keep-out

- The inverted-F PCB antenna fills the top 5 mm of the module, the edge opposite the bottom pad row and nearest pins 1 and 21.
- Keep-out (DS 2.4 and figure 6): 35.5 mm wide x 18.5 mm tall, centred on the module. It reaches 13.5 mm beyond the antenna edge and 10.5 mm past each side, and its lower edge is 5.0 mm inside the module, 0.2 mm above the pin 1 and 21 pads. DS calls it "the minimum region ... that must remain free of any metal". That means no copper on any layer, and no parts, screws, connectors or metal enclosure walls.
- In footprint coordinates the keep-out is x -17.75 to +17.75, y -21.75 to -3.25. The footprint has it as a rule area on all copper layers that blocks tracks, vias, pads, pours and footprints.
- Placement, my recommendation: put the module on a board edge with the antenna facing out and its top edge flush with the board edge. The keep-out left on the board is then a 35.5 x 5.0 mm strip. Keep metal outside the board, such as enclosure walls, out of the 13.5 mm beyond the edge. DS does not show an overhanging mount. With a 5 mm overhang, pads 1 and 21 would sit 0.2 mm from the board edge, so I would not do it.
- Ground (DS 2.6): the module needs "a good ground plane". Connect all six GND pins to the plane with a via beside each pad. Put a solid ground plane under the padded part of the module and stop it at the keep-out edge. "The area around the antenna must be clear of grounding".
- My recommendation: route no signal tracks or vias on the top layer under the module body, because DS does not describe the module's underside.
- Raspberry Pi publishes antenna patterns at <https://pip.raspberrypi.com/categories/602-antenna-patterns> (login needed, not downloaded).
- The modular approvals (EU, UK, USA, Canada) rest on following this integration guidance.

## Reflow (DS 2.8, table 7)

| Parameter | Value |
|---|---|
| Preheat | 150 °C to 200 °C for 60 to 120 s |
| Ramp up | 3 °C/s max |
| Time above 217 °C | 60 to 150 s |
| Peak body temperature | 260 °C max, measured top centre of the module |
| Time within 5 °C of peak | 30 s |
| Ramp down | 6 °C/s max |
| 25 °C to peak | 8 minutes max |

Pb-free. This is the classification profile, so the assembly profile must stay inside it. If the module goes through reflow upside down on a double-sided board, DS requires the peak to stay within ±2 °C of 260 °C, so place it on the side that is reflowed last. DS gives no moisture sensitivity level and no stencil advice.

## Ordering

- Manufacturer part number: RMC20452T. The T means tape and reel, 960 per reel. Raspberry Pi product code: SC1169, not SC1689. Distributors list it under either number. There is one variant only.
- List price $4. In production until at least January 2036. HS code 8473302000.

Stock on 2026-11-10, read from the product pages. I checked DigiKey myself. A subagent collected the other rows, and `sourcing-raw.md` has its full table and caveats.

| Distributor | Part number | Pack | Unit price | Stock |
|---|---|---|---|---|
| DigiKey | 2648-SC1169CT-ND | Cut tape, from 1 | $4.59 | 1,728 in stock |
| DigiKey | 2648-SC1169TR-ND | Reel of 960 | $4.00 | Same stock. Factory lead time 22 weeks |
| DigiKey | 2648-SC1169DKR-ND | Digi-Reel, $7 fee | $4.59 | Same stock |
| Mouser | 358-SC1169 | Cut tape from 1, reel in multiples of 960 | $4.00 | 2,892 in stock. Factory lead time 20 weeks |
| Newark (Farnell group) | 47AM0664 | Each, from 1 | $4.30 | 895 in stock, shipped from UK |
| Farnell / element14 | 4737257 | Not verified | Not verified | Page blocked the scraper. Check by hand |
| RS Components | none found | | | No listing found |
| Pimoroni | SC1169 | Single, cut tape | £3.00 | Available |
| The Pi Hut | SC1169 | Single, cut tape | £3.80 | In stock |
| Reichelt | RPI RMC20452T | Each | €4.10 incl. VAT | In stock |
| SparkFun | WRL-29424 | Each | $4.60 | In stock |
| PiShop.us | 966-2 | Each | $4.40 | In stock |
| Welectron | RP9-911690 | Each | €4.90 incl. VAT | 100+ in stock |
| BerryBase | RPI-RM2 | Each | €3.90 incl. VAT | Not available |
| TME | SC1169 | Reel of 960 only | Not shown | 0 in stock, special order |

## Open points

- Keep-out height: DS figure 6 says 18.5 mm. Raspberry Pi's own KiCad footprint draws the keep-out 20.0 mm tall, 1.5 mm further beyond the antenna. The footprint here follows the datasheet, which is newer (February 2026 against June 2025). Leave the extra 1.5 mm free if the board allows.
- DS gives no module-level absolute maximum ratings, decoupling guidance, moisture sensitivity level, paste stencil advice or dimensional tolerances.
- KiCad's stock library already has a footprint for this module, `RF_Module:RMC20452T`, with the same pad positions. It uses rounded pads, omits the keep-out on inner layers 2 and up, and has no matching stock symbol in this install.
- Raspberry Pi supports RM2 only with RP2040 or RP2350 hosts running the Pico SDK's PIO gSPI driver (DS 1.3.2).
