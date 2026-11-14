# Assembly and bring-up

## PCBWay order

Upload `fab/rp2350-devboard-gerbers.zip` to the PCB order form with these options:

| Option | Value |
| --- | --- |
| Layers | 4 |
| Size | 28 × 78.54 mm |
| Thickness | 1.6 mm |
| Stackup | PCBWay standard (0.2 mm prepreg between each outer and inner layer). The job file lists it |
| Copper | 1 oz outer, 0.5 oz or 1 oz inner |
| Min track / spacing | 5 mil (0.127 mm) |
| Min hole | 0.2 mm for the thermal vias in the U1, U5 and U6 exposed pads, 0.3 mm for all other vias |
| Surface finish | ENIG (needed for the 0.4 mm QFN and the RM2 castellations) |
| Solder mask | Any colour |
| Via process | Via in pad: all vias filled with resin and capped (IPC-4761 Type VII) |
| Assembly | Turnkey, top side only, with stencil |

The via process is required. 82 vias sit in or touch SMD pads, and open barrels there would wick solder away from
the joints. The Gerbers cannot carry this, so select it on the order form and repeat it in the order remarks.

For assembly, upload `fab/rp2350-devboard-bom-pcbway.csv` and `fab/rp2350-devboard-centroid.csv`.
The centroid is in mm from the board's bottom-left corner, Y up, with KiCad rotations (counter-clockwise, top view).
Check PCBWay's rotation preview against the pin 1 marks on the silkscreen, especially U1, U5, U6, U7 and D3.

Do not place:

- J5, J6: header holes only.
- FID1-FID3: copper fiducials, nothing to place.

## Part notes

- U1 (RP2350A, QFN-60, 0.4 mm pitch), U5 (BQ24074, VQFN-16) and U6 (TPS63001, VSON-10) have exposed pads with
  thermal vias. Ask for a stencil with windowed paste on the exposed pads, as in the paste layer.
- U7 (RM2) is a castellated module placed by machine like any SMD part. Nothing else may sit under or beside the
  antenna end at the top edge.
- J1 (USB-C) has four plated shell tabs. Solder them fully, because they carry the plug's mechanical load.
- J2 pin 1 is GND and pin 2 is battery +. LiPo vendors differ, so check the cell's wiring before plugging it in.
  Q1 blocks a reversed cell.

## Optional headers

For breadboard use, push two 1 × 14, 2.54 mm pin headers into J5 and J6 from the bottom, so the pins point down,
and solder them on the top. The rows are 22.86 mm (0.9 in) apart. The pin names are printed on the bottom.

## Bring-up

1. Inspect U1, U5 and U6 for bridges, and J1's contacts under magnification.
2. With no battery, power from a current-limited USB supply (100 mA limit). Idle current should be a few tens of mA.
3. Measure 3.3 V on J5 pin 2 and about 4.4 V on VSYS (C20). The orange charge LED stays off with no battery.
4. Hold BOOTSEL and plug into a computer. The `RP2350` USB drive appears.
5. Copy a MicroPython `RPI_PICO2_W` UF2 and check:
   - `machine.freq()` and `gc.mem_free()` run. For PSRAM, use a build with PSRAM on GPIO8 enabled.
   - `network.WLAN(network.STA_IF).scan()` lists access points.
   - A WS2812 on GPIO22 lights (`neopixel.NeoPixel(Pin(22), 1)`).
   - An SD card mounts over SPI or SDIO on GPIO10-15. GPIO9 reads 0 with a card in.
   - An I²C scan on GPIO4/5 finds a Qwiic board.
6. Plug in a LiPo. The charge LED lights while charging, and `ADC(28).read_u16() * 3.3 / 65535 * 2` reads the cell
   voltage within a few percent.
7. Unplug USB. The board keeps running from the cell.
