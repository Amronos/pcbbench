# PCBWay notes for a 4-layer RP2350 board with turnkey assembly

All pages were read on 2026-11-10. Every number carries the ID of its source from the list at the end. "Unverified" means I found no PCBWay page that states it. Lines marked "Inference" are my reading of the numbers, not a PCBWay statement.

PCBWay publishes several rule sets that disagree with each other. Where they conflict, the tables show each value and the "Design to" column takes the strictest one.

## 1. PCB fabrication, standard tier, 4-layer FR-4 1.6 mm

PCBWay's capabilities page has two tables. "Standard PCB" is the quick-turn tier. The "Advanced PCB" table grades each parameter as "Normal process", "Medium difficulty" or "High difficulty". Staying inside "Normal process" avoids review surcharges.

### Traces and copper

| Item | Published value | Source | Design to |
| --- | --- | --- | --- |
| Min trace and spacing, standard tier | "0.1mm/4mil" trace, "4mil(0.1mm)" spacing | [CAP] | See next rows |
| Outer layer, 1 oz finished | Normal "≥5/6 mil", medium "≥5/5 mil", high "<4/4 mil" (width/spacing, before compensation) | [CAP] row 15, [TRK] | 0.127 mm trace, 0.15 mm gap |
| Inner layer, 1 oz | Normal "≥4/5 mil", medium "≥4/4 mil" | [CAP] row 14, [TRK] | 0.1 mm trace, 0.127 mm gap |
| Inner layer, 0.5 oz (18 um) | Normal "≥4/4 mil", medium "≥4/3.5 mil" | [CAP] row 14 | 0.1 / 0.1 mm |
| Cost advice | "We strongly suggest to design trace width/spacing above 6mil(0.15mm) to save cost." | [TRK] | 0.15 / 0.15 mm where space allows |
| Outer copper choices | "1oz/2oz/3oz/4oz/5oz/6oz/7oz/8oz" | [CAP] | 1 oz |
| Inner copper choices, standard tier | "1oz/1.5oz/2oz/3oz/4oz" | [CAP] | 1 oz |
| Trace width tolerance | Normal "≥±20%" | [CAP] row 18 | |

0.5 oz inner copper is not in the standard tier's inner copper list, and none of the published 4-layer 1.6 mm stackups use it [STK]. The advanced table lists base copper "0.5-4" oz as normal process [CAP row 22]. Whether 0.5 oz inner can be ordered at the cheapest tier is unverified.

PCBWay's KiCad DRC file has a commented-out block "4-layer , 1oz and 0.5oz copper" with 0.09 mm outer and 0.1/0.09 mm inner [DRU]. That is tighter than the capabilities page, and the file says "All statemets without guarantee!" [DRC]. Do not rely on it.

### Vias, holes and annular ring

| Item | Published value | Source | Design to |
| --- | --- | --- | --- |
| Drill range | "0.15-6.0mm". "Any holes greater than 6mm or smaller than 0.2mm will be subject to extra charges." | [CAP] | Drill ≥ 0.2 mm |
| Drill vs thickness | "hole diameter 0.2mm: maximum board thickness 1.6mm". Aspect ratio "≤8" is normal process. | [CAP] rows 5, 6 | 0.2 mm is the limit at 1.6 mm. 0.3 mm has margin. |
| Min annular ring, standard tier | "0.15mm(6mil)" | [CAP], [ANN] | 0.15 mm |
| Min annular ring, 1 oz outer, advanced table | Via: normal "≥5mil", medium "≥4mil". Component hole: normal "≥10mil", medium "≥8mil". | [CAP] row 17 | Via 0.15 mm, component hole 0.25 mm |
| Via sizes in PCBWay's KiCad DRC file | "4-layer standard": hole 0.3 mm, diameter 0.45 mm. "4-layer advanced": 0.25/0.4, 0.2/0.35, 0.15/0.3 mm. | [DRU] | 0.3 mm drill, 0.6 mm pad |
| Finished hole tolerance | "PTH: +/-0.08mm, NPTH: +/-0.05mm" | [CAP] | |
| Hole position tolerance | "±0.075mm" | [CAP] row 8 | |
| Min non-plated hole | "for non-plated holes, the min size should be 0.45 mm". DRC file says 0.5 mm. | [NPTH], [DRU] | 0.5 mm |
| Through-hole copper | "18-25 µm" normal. Order form default "Standard(20um)". | [CAP] row 21, [ORD] | |
| Tented vias | "To avoid soldermask ink flowing to hole, pls make the diameter below 0.35mm." | [VIA] | Via drill ≤ 0.3 mm if tented |
| Via covering option | With Gerbers, PCBWay follows the file and ignores the order form's via option. | [VIAP] | Set tenting in the Gerbers |

Inference: a 0.3 mm drill with a 0.6 mm pad satisfies every rule set. A 0.2 mm drill with a 0.5 mm pad satisfies the capabilities page. The DRC file's 0.2/0.35 mm option implies a 0.075 mm ring, which contradicts the 0.15 mm ring on the capabilities page.

### Hole and copper clearances

| Item | Published value | Source | Design to |
| --- | --- | --- | --- |
| Hole to hole, different nets | "0.45 mm for plated through holes and 0.30 mm for vias" (1 oz) | [HH2] | 0.5 mm, which also meets [DRU] |
| Hole to hole, same net | "≥ 0.3 mm for plated through holes", "≥ 0.15 mm for vias", "≥ 0.2 mm for non-plated holes" | [HH1] | 0.254 mm for vias, per [DRU] |
| Hole to hole, advanced table | Component hole "≥16MIL", via (≤0.45 mm) "≥11MIL" | [CAP] row 10 | |
| Hole to trace, outer | "min 0.2 mm from non-plated hole to trace, and min 0.35 mm from plated hole to trace" | [HT] | 0.35 mm PTH, 0.25 mm NPTH |
| Hole to copper, inner layers, 4L | Normal "≥7MIL", medium "6MIL≤...<7MIL" | [CAP] row 13 | 0.2 mm |
| NPTH with a copper pad | "normally we need cut copper by 0.2mm if making as NPTH" | [NPR] | Keep NPTH in copper-free areas |
| Non-plated slot to trace | "≧ 0.2mm" | [ST] | |
| Hole to board edge | "≧ 0.5mm", and "1.0mm" for V-scored edges | [HE] | 0.5 mm |
| Copper to board edge | "The distance between the trace and board outline should be 0.20mm". Advanced table: CNC normal "0.25mm", medium "0.20mm". DRC file: 0.3 mm. | [EDGE], [CAP] row 19, [DRU] | 0.3 mm |

### Slots and castellated holes

| Item | Published value | Source |
| --- | --- | --- |
| Plated slot width, quick-turn | "You can design plated slot to be at least 0.5mm, non-plated slot to be at least 0.8mm." | [SLOT], [PTS], [CAP] row 11, [DRU] |
| Slot length to width | Normal "Length to width≥2", medium "Length to width<2" | [CAP] row 11 |
| Newer slot guidance (2025-06-25) | "The minimum width of a plated slot should be ≥ 0.3 mm". Slots longer than 5 mm are milled, and then "The plated slot width should be ≥ 0.65 mm". | [HH1] |
| How to draw a slot | "Avoid creating slots by connecting multiple overlapping or adjacent holes." Use an oval or rectangular slot. | [HH1], [OVAL] |
| Castellated holes, standard table | "Minimum Diameter of Plated Half Holes ... 0.4mm" | [CAP] |
| Castellated holes, advanced table | Diameter normal "≥0.5mm", medium "0.5mm>diameter≥0.4mm". Edge-to-edge spacing normal "≥0.3mm". | [CAP] row 12 |
| Castellated holes, help center | "The minimum diameter of castellated holes is 0.6 mm and the minimum distance between two Plated half holes is 0.55 mm." | [CAST] |
| Castellated cost | Extra cost applies and "Charge for double-sided differs from the charge for muti-layer board." | [COST] item 6 |

Inference for the USB-C shell legs: a 0.6 mm wide plated slot is above the 0.5 mm minimum in all four sources. Make each slot at least 1.2 mm long so the length to width ratio stays at 2 or more. A 0.6 x 1.0 mm slot falls into "medium difficulty". The PTH tolerance of ±0.08 mm applies, so check the connector's leg thickness against a 0.52 mm worst case.

### Solder mask

| Item | Published value | Source |
| --- | --- | --- |
| Mask opening (expansion per side) | Normal "≥2mil", medium "1.5", high "1". "1mil is only concentrated in the BGA area. If the window can be enlarged, increase it as much as possible, but the maximum is 3mil" | [CAP] row 23 |
| Suggested clearance | "the suggested soldermask clearance in GERBER is 2-4 mils" | [SM] |
| Mask bridge width, copper below 2 oz | Normal "4（spacing between ICs is 8 mil, green oil），variegated or black oil≥4.5mil". Medium "3-4（spacing between ICs is 7-8 mil, green oil）". | [CAP] row 23 |
| Pad gap needed for a bridge, 1 oz | "The Space between IC pads should be at least 0.2mm" for green. Below 0.22 mm, no bridge for blue, red, white, yellow, black or matte black. | [SMB] |
| Pad gap needed for a bridge, 1 oz, other page | "min 0.19mm(7.5mil) for green, blue, red, purple color,others require min 0.22mm(9mil)" | [SM] |
| Free mask colors | "No extra charge (Green, Red, Yellow, Blue)" | [CAP] |

Inference for the QFN-60 at 0.4 mm pitch: with 0.2 mm wide pads the gap is 0.2 mm, which is exactly the green limit and below the limit for black, white and yellow. Use green mask and keep the pad width at 0.2 mm or less. Otherwise PCBWay will ask to remove the bridges and open the mask along the whole pad row ("Just do as your file and accept no soldermask bridge between IC pads" [SMB]).

### Silkscreen and outline

| Item | Published value | Source |
| --- | --- | --- |
| Min silkscreen line width | "0.15mm" | [CAP], [SILK] |
| Min silkscreen text height | "0.8mm" | [CAP], [SILK] |
| Width to height ratio | "1:5" | [CAP] |
| Silkscreen to mask opening | "The spacing from lengend to openings is requireed to be 0.15mm" | [SILK2] |
| Outline tolerance | "±0.2mm for CNC routing, and ±0.5mm for V-scoring" | [CAP] |
| Thickness tolerance | "±10%" for boards 1.0 mm and thicker | [CAP] |
| Small-board surcharge | "there is extra routing cost for any board with one side less than 20mm or two sides less than 50*50mm" when delivered as single boards | [COST] item 2 |
| Removing PCBWay's order number from the board | "Remove product No. : No Yes (extra+$ 1.5)" | [ORD] |

### Default 4-layer stackups at 1.6 mm, 1 oz outer

The stackup page lists exactly three 4-layer 1.6 mm stackups with 1 oz finished outer copper [STK]. They are identical except for the pressed prepreg thickness, which depends on how much copper remains on the inner layers. All three use 1 oz inner copper.

| Layer | Material | Nominal thickness (mm) |
| --- | --- | --- |
| L1 | "Outer Base Copper 0.5OZ", "Plating to 1OZ" | 0.0175 base |
| Prepreg | "7628 RC46% DK:4.74" | 0.1960 before pressing |
| L2 | "Inner Copper 1OZ" | 0.0350 |
| Core | "Core DK:4.6" | 1.0300 (1.1 with copper) |
| L3 | "Inner Copper 1OZ" | 0.0350 |
| Prepreg | "7628 RC46% DK:4.74" | 0.1960 before pressing |
| L4 | "Outer Base Copper 0.5OZ", "Plating to 1OZ" | 0.0175 base |

| Inner layer residual copper | Pressed prepreg L1-L2 and L3-L4 (mm) | Finished thickness (mm) |
| --- | --- | --- |
| 70% (use when ratio > 60%) | 0.1855 | 1.61 |
| 50% (use when 40% < ratio ≤ 60%) | 0.1785 | 1.59 |
| 30% (use when ratio ≤ 40%) | 0.1715 | 1.58 |

Finished thickness tolerance is "±10%" [STK]. Inference: with solid GND and power planes on L2 and L3, the 70% row applies, so L1 to L2 is about 0.185 mm of 7628 with DK 4.74.

The same page lists 4-layer 1.6 mm stackups for 2 oz outer copper with 1, 1.5 or 2 oz inner copper, and for 3, 4 and 5 oz. No thin-prepreg (2116, 3313 or 1080) 4-layer 1.6 mm stackup with 1 oz outer copper is listed [STK]. Getting one requires the "Custom stackup" option. PCBWay notes "the build time will be longer than PCBWay's" for custom stackups [STKQ].

### Impedance control cost

On the order form, "Impedance control" and "Custom stackup" sit under "Customized Services and Advanced Options (Castellated holes,Edge plating,Impedance control...)", with the note "We may add extra cost for these special options which will be confirmed after review." [ORD]. The stackup page says custom stackup or impedance control means choosing those options, and "After place order,we will calculate whether it meets the requirements based on the stackup , material and impedance information." [STK]. The tolerance is "±10%，50Ω and below：±5Ω" [CAP row 35].

Impedance control can cost extra, and the amount is set at review. The exact surcharge is unverified. To avoid it, leave the option off, use the default stackup above, and size the USB pair for it yourself.

## 2. Files PCBWay wants

### Summary

| File | Format | Required? | Source |
| --- | --- | --- | --- |
| Gerbers | RS-274X, in one zip | Yes | [AFR], [GEXT] |
| Drill files | Excellon, PTH and NPTH | Yes | [GEXT], [GINC] |
| BOM | ".xls, xlsx or .csv". PDF is refused. | Yes | [AFR], [SOG] |
| Centroid (pick and place) | "excel, .txt or .pos", SMD parts only | Yes for SMD | [FILES] |
| Assembly drawing | PDF | Only if the silkscreen lacks designators or polarity marks | [FILES], [T13] |
| Photos or 3D renders | Any image | Optional, recommended | [FILES], [AFR] |
| `.kicad_pcb` | Not listed as an accepted production format | No | [CAP] |

### Gerbers and drill files

- Format: "The same Gerber files in format of RS-274X that you send to us for your PCB fabrication will be required to assemble your boards. As a minimum request, PCB assembler needs the files of three layers: Silkscreen, Copper (Track) and Solder Paste." [AFR]
- A complete set has a board outline, copper layers, solder mask layers, silkscreen layers and an NC drill file. If one is missing, the order fails review [GINC].
- PCBWay recognizes KiCad's default names: `F_Cu.gbr`, `B_Cu.gbr`, `F_Silkscreen.gbr`, `B_Silkscreen.gbr`, `F_Mask.gbr`, `B_Mask.gbr`, `F_Paste.gbr`, `B_Paste.gbr`, `Edge_Cuts.gbr`, `NPTH.drl`, `PTH.drl` [GEXT]. The page shows a 2-layer example. Inference from KiCad's defaults: for 4 layers, add `In1_Cu.gbr` and `In2_Cu.gbr`.
- The order form has an optional field for the layer order: "Please fill in the layer order from the top-side view to the bottom-side view according to the layer names in the Gerber file." [ORD]. Fill it in for a 4-layer board. A missing layer order is a listed review failure [LORD].
- An older PCBWay KiCad guide asks for Protel extensions (.GTL, .GBL, .GTS, .GBS, .GTO, .GBO, .GKO) and says not to tick "Include extended attributes" [K5]. The current page [GEXT] accepts the `.gbr` names, so renaming is optional.
- Put slots in the drill file or the outline layer as ovals, not as chains of overlapping holes [HH1].

### KiCad source files

The capabilities page says "Please upload your PCB files in the format of gerber file, .pcb, .pcbdoc or .cam file" and "Please try best to offer gerber file" [CAP]. `.kicad_pcb` is not on that list. PCBWay's online viewer can open `.kicad_pcb` for viewing only [VIEW]. Upload Gerbers.

PCBWay also offers a KiCad plugin that exports and uploads "Gerber files in correct format for production", an "IPC-Netlist file", a BOM and a pick-and-place file. For assembly orders through the plugin it needs the "Manufacture Part Number" field on each symbol [PLUG].

### BOM

Accepted formats are ".xls, xlsx or .csv" [AFR], [BOMF]. "We do not accept BOM files in pdf" [SOG].

The header row of PCBWay's sample BOM is below. Columns marked `*` are the required ones in the sample [SAMPLE-BOM].

| Column | Example from the sample |
| --- | --- |
| `Item #` | 1 |
| `*Designator` | `U2,U4` (comma-separated, one line per part number) |
| `*Qty` | 2 |
| `Manufacturer` | Murata |
| `*Mfg Part #` | GRM21BR71C225KA12L |
| `Description / Value` | CAP CER 2.2UF 16V X7R 0805 |
| `*Package/Footprint` | 0805 |
| `Type` | `SMD`, `thru-hole`, or `DNS` for do-not-stuff |
| `Your Instructions / Notes` | Free text |

Other BOM rules:

- The file requirements page also lists "Distributors Part Number" as a field that turnkey BOMs "may include" [AFR]. The sample has no such column.
- For a preferred supplier, "please remark the supplier name or include the link in the BOM" [SUP].
- Generic passives are allowed without a part number if fully specified, for example "0.1μF 0805 25V x7r" or "10K 0805 1%" [GEN].
- "If you accept to use substitutes for assembly, please list a column of substitutes (Yes or No) in BOM" [SUB].
- Designators and quantities must match the centroid file and the silkscreen. Each designator appears once. LEDs need a color [T13].

### Centroid file

- Required content: "X - coordinate, Y- coordinate, components angle, designators should be included, and please set the unit to be mm" [FILES]. The file requirements page adds "side of Board (Top or Bottom)" and "Only surface mounting parts are listed in the Centroid" [AFR].
- Format: "excel, .txt or .pos" [FILES]. PCBWay's KiCad 9 guide says to use File, Fabrication Outputs, Component Placement (.pos) and "Select CSV format for output" [K9].
- "please provide pick and place file separately for each layer" [T13].
- PCBWay's sample is an Altium-style text file with these columns: `Designator`, `Footprint`, `Mid X`, `Mid Y`, `Ref X`, `Ref Y`, `Pad X`, `Pad Y`, `TB`, `Rotation`, `Comment` [SAMPLE-CEN]. `TB` holds `T` or `B`.
- Conflict: the sample's coordinates are in mil (for example "660.236mil"), while the help page asks for mm. Use mm, as the written instruction says.

### Assembly drawing and markings

- "If there is not silkscreen on pcb, please offer assembly silkscreen drawing for assembly reference." Designators must match the silkscreen, and polarity must be clear for LEDs, ICs, diodes and tantalum capacitors [FILES].
- "Please add polarity cathode or anode mark and pin 1 in silkscreen layer. If you do not want this information to be printed on the board, please send an individual assembly drawing file" [SOG].
- For cathode or anode marks, "if use one line or one dot, we may get confused". A dot is fine for pin 1 [T13].
- A stencil order is not needed: "we will make stencil accordingly by default", and the assembly quote includes it [STEN].

### Downloads

| File | URL | Local copy |
| --- | --- | --- |
| Sample BOM | https://www.pcbway.com/img/images/pcbway/Sample_BOM_PCBWay.xlsx?v=1.1 | `scratch/pcbway-samples/Sample_BOM_PCBWay.xlsx` |
| Sample centroid | https://www.pcbway.com/img/images/pcbway/a-sample-of-PCBWay-Centroid-File.txt | `scratch/pcbway-samples/a-sample-of-PCBWay-Centroid-File.txt` |
| KiCad DRC rules (zip) | https://pcbwayfile.s3.us-west-2.amazonaws.com/web/230915/KiCAD_Custom_DRC_Rules_for_PCBWay.zip | `scratch/pcbway-samples/KiCAD_Custom_DRC_Rules_for_PCBWay.kicad_dru` (extracted) |
| Track and spacing table (image) | https://pcbwayfile.s3.us-west-2.amazonaws.com/web/24/06/07/1427441892250t.png | `scratch/pcbway-samples/min-track-spacing-by-copper-weight.png` |
| Polarity marking reference (PDF) | https://pcbwayfile.s3-us-west-2.amazonaws.com/mail/19/08/14/1623550993447.pdf | Not downloaded |

The DRC file is written for KiCad 7 and ships with the 2-layer rules active. The 4-layer blocks are commented out.

## 3. Parts sourcing and assembly limits

### Where the parts come from

- Named distributors: "Digi-key Electronics, Mouser Electronics, Farnell element14, Arrow Electronics, Avnet, etc" [EC].
- Local suppliers come first: "Local supplier is our top choice since they have a lot of stock locally ... Only when components are not available locally will we arrange purchasing from above international distributors. It will take about 5-7 business days to obtain the components", or 7-10 business days if customs is slow [EC].
- LCSC is not named on any page I read. Whether it is one of the "reliable local electronic suppliers" is unverified.
- "No substitutes will be used without getting your approval." [EC]
- The order form asks "Do you accept alternatives/substitutes made in China?" [SMT]. Answer No if the BOM must be built exactly.
- You can name the supplier per line [SUP]. If PCBWay buys from a supplier you recommend, "we won't guarantee the quality of components" [EC].
- "We do not mark up on the parts cost" [ACAP]. Quoted prices can still exceed distributor prices because they include "the shipping cost, customs charge, Labor procurement cost" and spare parts [PRICE].
- PCBWay buys spares. For consigned parts it asks for 0201 and 0402 passives at "a minimum of 100 pieces" and "50 pieces over assemble quantity" [SR]. Inference: expect similar overage on a turnkey quote.

### Limits that affect this board

| Topic | Published value | Source |
| --- | --- | --- |
| Smallest passive | "we can accept components as small as 01005, 0201,0402". "Min package 01005." | [ACAP], [MINP] |
| Fine pitch ICs | "we can assemble 0.25mm fine pitch parts". "Small Chip Packages (0.2mm pitch )". | [ACAP], [SMTC] |
| QFN | Listed as a supported package type | [SMTC] |
| BGA pitch | "0.3mm pitch for rigid PCBs" with X-ray. Other pages say 0.25 mm. | [ACAP], [AFAQ], [BGA] |
| LGA modules | Not mentioned on any page I read | Unverified |
| X-ray | "X-ray Inspection: checks for BGAs, QFN and bare circuit boards." The order form has a "Number of X-ray test" field under options whose "cost is not included in the online quotation". | [ACAP], [TEST], [SMT] |
| Assembly sides | "Assembly side(s): Top side Bottom side Both sides" | [SMT] |
| Double-sided process | "the printing, placement, and reflow process can be repeated" for the second side | [SMTC] |
| Minimum order | "Our minimum is as low as 5 pieces." | [ACAP] |
| Board size for assembly | Min "10mm x 10mm", max "250mm x 500mm" | [ACAP] |
| Workmanship standard | "IPC-A-610 Class 2" | [AFAQ] |
| Prototype soldering method | "For prototypes or assembly with few components totally, we usually solder manually" | [HAND] |
| Other makers' PCBs | "Currently we do not use other's PCB to assemble at our facilities." | [AFAQ] |

What this means for the RP2350 board:

- 0402 passives and the 0.4 mm pitch QFN-60 are inside the published limits.
- Whether X-ray is required for an LGA module is unverified. PCBWay's pages say X-ray is used for BGA and QFN, and the order form lets you request a number of X-ray tests at extra cost. Whether PCBWay X-rays the QFN-60 by default, and the price per test, are also unverified. Ask the sales rep when the quote comes back.
- The price difference between single-sided and double-sided assembly is unverified. The instant quote needs a browser session and I did not run it. The process repeats for the second side (paste print, placement and reflow) [SMTC]. Inference: that also needs a second stencil, so keeping all parts on top is the cheaper choice.
- PCBWay may hand-solder a small prototype run [HAND]. If you want machine placement and reflow for the QFN, say so in the order notes: "If you have special request on this, please make the note about it when you submit the SMT order."

### Panel and edge rules for assembly

The board is 25 mm wide, so these apply.

- "If your PCB dimension is smaller than 50mmx100mm ... your boards must be panelized in an array for assembly." [SR]. The order form says "We suggest choose to do panel if single PCB qty is more than 20pcs or any side of single board is smaller than 50mm." [SMT]
- "If the clearance between the board's edge and copper features is less than 3.5mm (138mil) ... Break-away rails (Break-away tabs) must be added at the two longer paralleled edges" [SR]. Another page says components closer than 3 mm to the edge need rails of more than 3 mm [MACH]. The USB-C connector at the board edge triggers this.
- PCBWay can design the panel. Choose "Panel by Supplier" on the form [SMT]. Panel limits: min "50*50mm", max "330*530mm", tab-route gap "1.6mm", V-score gap "0mm or 3mm" [PANEL].
- Fiducials: "usually there are 3 fiducial marks in each panel. Marks diameter is 1.0mm with 1.7mm soldermask opening and placed in the middle of edge rails." [PANEL]. Also "Please add fiducial marks on panel and single pcb" [MACH].
- Assembled boards ship in the panel unless you tick "Depanel the boards to delivery", which is a paid option outside the instant quote [SHIP], [SMT].
- For edges separated by V-score, keep holes 1.0 mm from the edge [HE]. The DRC file suggests 0.4 mm for copper to a V-cut [DRU].

## Open questions for the PCBWay sales rep

1. Is 0.5 oz inner copper available on a standard 4-layer 1.6 mm order, and with which stackup?
2. What does "Impedance control" add to a 5 to 10 piece 4-layer order?
3. Is X-ray inspection included for QFN and LGA parts, or billed per "X-ray test"? At what price?
4. What is the assembly price difference for parts on both sides?
5. Are 0.6 mm wide plated slots shorter than 1.2 mm accepted without a surcharge?
6. Does PCBWay buy from LCSC, and can a BOM line name LCSC as the supplier?

## Sources

| ID | Page | URL |
| --- | --- | --- |
| [CAP] | PCB capabilities (standard and advanced tables) | https://www.pcbway.com/capabilities.html |
| [STK] | Multi-layer laminated structure (298 stackups) | https://www.pcbway.com/multi-layer-laminated-structure.html |
| [ORD] | PCB instant quote form | https://www.pcbway.com/orderonline.aspx |
| [SMT] | Assembly quote form | https://www.pcbway.com/quotesmt.aspx |
| [ACAP] | Assembly capabilities | https://www.pcbway.com/assembly-capabilities.html |
| [AFR] | Files requested for PCBA | https://www.pcbway.com/assembly-file-requirements.html |
| [AFAQ] | PCB assembly FAQ | https://www.pcbway.com/assembly-faq.html |
| [SR] | Special reminders for PCBA | https://www.pcbway.com/assembly-special-remind.html |
| [SOG] | SMT ordering necessary files and info | https://www.pcbway.com/smt_ordering_guide.html |
| [EC] | Components sourcing | https://www.pcbway.com/pcb_prototype/Electronic_Components.html |
| [SMTC] | SMT assembly capabilities | https://www.pcbway.com/pcb_prototype/SMT_Assembly_Capabilities.html |
| [BGA] | BGA assembly capabilities | https://www.pcbway.com/pcb_prototype/BGA_Assembly_Capabilities.html |
| [TEST] | PCB assembly testing | https://www.pcbway.com/pcb-assembly/pcb-assembly-testing.html |
| [PANEL] | Panel requirements for assembly | https://www.pcbway.com/pcb_prototype/Panel_Requirements_for_Assembly.html |
| [PTS] | Plated-through slots | https://www.pcbway.com/pcb_prototype/Plated_through_slots.html |
| [ANN] | Annular rings | https://www.pcbway.com/pcb_prototype/Annular_rings.html |
| [SM] | PCB solder mask | https://www.pcbway.com/pcb_prototype/PCB_Solder_mask.html |
| [VIEW] | Online PCB viewer | https://www.pcbway.com/tool/ElectronicDesignViewer |
| [PLUG] | PCBWay plug-in for KiCad | https://www.pcbway.com/blog/News/PCBWay_Plug_In_for_KiCad_3ea6219c.html |
| [K5] | Generate Gerber file from KiCad 5.1.6 | https://www.pcbway.com/blog/help_center/Generate_Gerber_file_from_Kicad_5_1_6.html |
| [K9] | Export Gerber, BOM and pick-and-place in KiCad 9.0 | https://www.pcbway.com/helpcenter/generate_gerber/How_to_Export_Gerber__BOM__and_Pick_and_Place_Files_in_KiCad_9_0.html |
| [GEXT] | Gerber file extension from different software | https://www.pcbway.com/helpcenter/generate_gerber/Gerber_File_Extension_from_Different_Software.html |
| [GINC] | Gerber files are not completed | https://www.pcbway.com/helpcenter/file_issues/Gerber_files_are_not_completed.html |
| [DRC] | PCBWay custom design rules | https://www.pcbway.com/helpcenter/design_instruction/PCBWay_Custom_Design_Rules.html |
| [DRU] | KiCad DRC rules file, from the zip linked on [DRC] | https://pcbwayfile.s3.us-west-2.amazonaws.com/web/230915/KiCAD_Custom_DRC_Rules_for_PCBWay.zip |
| [TRK] | Min track and spacing by copper weight (table is an image) | https://www.pcbway.com/helpcenter/ordering_parameter_instruction/What_is_the_Min_Track_Spacing_for_1oz__2oz__3oz__Copper_weight_.html |
| [VIA] | Via diameter for solder mask covering | https://www.pcbway.com/helpcenter/design_instruction/What_diameter_of_via_is_better_to_have_soldermask_covering__.html |
| [VIAP] | Main reference to process vias | https://www.pcbway.com/helpcenter/ordering_parameter_instruction/What_is_the_main_reference_to_process_vias_by_PCBWay_.html |
| [STKQ] | Stackup information | https://www.pcbway.com/helpcenter/layers_issues/Stackup_information.html |
| [LORD] | No layer orders for multi layers boards | https://www.pcbway.com/helpcenter/layers_issues/No_layer_orders_for_multi_layers_boards.html |
| [COST] | What PCB cases will be charged extra | https://www.pcbway.com/helpcenter/paymentproblems/What_PCBs_will_be_charged_of_extra_cost_.html |
| [SLOT] | Slots standard size, quick-turn | https://www.pcbway.com/helpcenter/drill_hole_or_via_issues/Slots_standard_size___Limited_to_Quick_turn_PCB.html |
| [OVAL] | Slot in oval pads | https://www.pcbway.com/helpcenter/drill_hole_or_via_issues/Slot_in_oval_pads.html |
| [CAST] | Requirement about castellated holes | https://www.pcbway.com/helpcenter/drill_hole_or_via_issues/Requirement_about_castellated_holes.html |
| [NPTH] | Min non-plated holes | https://www.pcbway.com/helpcenter/drill_hole_or_via_issues/min_non_plated_holes.html |
| [NPR] | NPTH design rule | https://www.pcbway.com/helpcenter/drill_hole_or_via_issues/NTPH_design_rule.html |
| [HH1] | Spacing from one hole to another is too narrow | https://www.pcbway.com/helpcenter/Engineering_Questions/The_spacing_from_one_hole_to_another_is_too_narrow.html |
| [HH2] | Limited holes spacing | https://www.pcbway.com/helpcenter/Engineering_Questions/limited_holes_spacing.html |
| [HT] | Spacing from hole to trace | https://www.pcbway.com/helpcenter/Engineering_Questions/the_spacing_from_hole_to_trace.html |
| [HE] | Spacing from hole to board edge | https://www.pcbway.com/helpcenter/Engineering_Questions/the_spacing_requirement_from_hole_to_the_edge_of_board.html |
| [ST] | Spacing from slot to copper trace | https://www.pcbway.com/helpcenter/Engineering_Questions/the_spacing_requirement_from_slot_to_copper_trace.html |
| [EDGE] | Trace to board outline less than 0.20 mm | https://www.pcbway.com/helpcenter/board_outline_issues/The_distance_between_the_trace_and_board_outline_is_less_than_0_20mm.html |
| [SMB] | Soldermask bridge | https://www.pcbway.com/helpcenter/soldermask_issues/Soldermask_bridge.html |
| [SILK] | Silkscreen standard size | https://www.pcbway.com/helpcenter/Engineering_Questions/Silkscreen_standard_size.html |
| [SILK2] | Spacing between silkscreen and openings | https://www.pcbway.com/helpcenter/Engineering_Questions/Spacing_between_silkscreen_and_openings.html |
| [FILES] | What files are requested for assembly production | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_files_are_requested_for_assembly_production_.html |
| [BOMF] | What file format should BOM be | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_file_format_should_BOM_be_.html |
| [T13] | Top 13 suggestions for assembly file problems | https://www.pcbway.com/helpcenter/Assembly_files_problems/Top_13_suggestions_for_solving_PCB_Assembly_files_problems.html |
| [SUP] | Buying from a specific supplier | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_we_buy_components_from_specific_supplier_or_provide_link_for_purchasing_.html |
| [GEN] | Passives without exact part numbers | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Can_I_list_capacitors_or_resistors_in_BOM_without_exact_part_numbers_.html |
| [SUB] | Substitutes | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Will_you_recommend_substitutes_when_you_quote_.html |
| [PRICE] | Why component cost is higher than Digi-Key | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Why_the_unit_cost_of_components_is_higher_than_suppliers_such_as_Digiky_.html |
| [MINP] | Min package you can assemble | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_s_the_min_package_you_can_assemble_.html |
| [HAND] | Assembly manually or by machine | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Do_you_make_assembly_manually_or_by_machine_.html |
| [MACH] | Requests on PCB for assembly by machine | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/What_are_the_requests_on_pcb_for_assembly_by_machine_.html |
| [STEN] | Stencil order for SMT projects | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Should_I_submit_a_stencil_order_for_SMT_project_made_by_PCBWay_.html |
| [SHIP] | Why assembled PCBs ship in panel | https://www.pcbway.com/helpcenter/pcb_assembly_ordering/Why_assemblied_PCB_will_be_shipped_out_in_panel.html |
| [SAMPLE-BOM] | Sample BOM | https://www.pcbway.com/img/images/pcbway/Sample_BOM_PCBWay.xlsx?v=1.1 |
| [SAMPLE-CEN] | Sample centroid file | https://www.pcbway.com/img/images/pcbway/a-sample-of-PCBWay-Centroid-File.txt |
