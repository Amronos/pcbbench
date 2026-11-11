# Design source register — Aster2350 Rev A

Retrieved/checked during design on 2026-11-09. These are engineering references,
not inventory reservations or evidence of end-product certification.

| Local PDF | Source | Use |
|---|---|---|
| rp2350.pdf | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf | RP2350A pin assignments, QMI memory, external DVDD circuit, errata; §6.3.7 Figure 24 |
| rp2350-hardware-design.pdf | https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf | Decoupling, crystal, USB and layout guidance |
| aps6404l.pdf | https://www.apmemory.com/en/downloadFiles/032411212009597427 | AP Memory APS6404L-3SQR, revision 2.7, January 5 2024; SOP-8 SN, 2.7–3.6 V, pin table and burst limitations |
| pga2350-schematic.pdf | https://cdn.shopify.com/s/files/1/0174/1800/files/Pimoroni_PGA2350_Schematic.pdf?v=1724926880 | Independent cross-check of the RP2350 QMI PSRAM pin arrangement; not a copied board layout |
| bq24074.pdf | https://www.ti.com/lit/ds/symlink/bq24074.pdf | Power path, NTC protection, input-limit modes, charge/termination/timer programming |
| tps63060.pdf | https://www.ti.com/lit/ds/symlink/tps63060.pdf | Main buck-boost, 1.5 µH inductor, feedback and layout |
| tlv758p.pdf | https://www.ti.com/lit/ds/symlink/tlv758p.pdf | Adjustable 1.1 V core LDO, stability and dropout |
| tlv61046a.pdf | https://www.ti.com/lit/ds/symlink/tlv61046a.pdf | RGB 5 V boost, enable/output isolation, feedback |
| sn74ahct1g125.pdf | https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf | 5 V buffer with TTL-compatible 3.3 V input |
| esp32-c3-wroom-02.pdf | https://www.espressif.com/sites/default/files/documentation/esp32-c3-wroom-02_datasheet_en.pdf | WROOM-02-N4 pad assignments, UART/download straps, antenna keepout |
| w25q128jv.pdf | https://www.winbond.com/resource-files/w25q128jv%20revf%2003272018%20plus.pdf | 3.3 V flash pin assignments and 208 mil SOIC package |
| ws2812b-2020.pdf | https://cdn-shop.adafruit.com/product-files/4684/4684_WS2812B-2020_V1.3_EN.pdf | Worldsemi manufacturer datasheet mirrored by Adafruit; LED pad numbering, 5 V supply, timing |

Additional primary references used for local symbols/footprints and component selection:

- https://www.ti.com/lit/ds/symlink/tps22919.pdf — radio load switch and QOD connection.
- https://www.ti.com/lit/ds/symlink/tlv9001.pdf — battery divider buffer.
- https://gct.co/connector/usb4105 — USB4105-GF-A mating direction and land pattern.
- https://www.molex.com/en-us/products/part-detail/1040310811 — right-opening microSD connector.
- https://www.jst-mfg.com/product/detail_e.php?series=231 — SH connector family.
- https://www.jst-mfg.com/product/detail_e.php?series=199 — PH battery connector family.
- https://www.pcbway.com/capabilities.html — quoted minimum 0.10 mm track/space,
  0.15 mm via annular ring and ≥0.20 mm ordinary drilling. The layout includes
  one 0.50/0.20 mm processor escape via; all other through vias are 0.60/0.30 mm.
  PCBWay must approve the exact stack, drilling, slots and component sourcing at quotation.

Manufacturer PDFs are retained for reviewer convenience and remain subject to
their publishers' copyrights. Local `.txt` files are extraction aids, not normative
specifications. The project does not rely on files fetched from a live URL at opening time.
