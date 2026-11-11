RP2350 Wi-Fi/BLE LiPo dev board, Rev A: PCBWay fabrication and turnkey assembly notes

Files
  rp2350_dev_gerber.zip      Gerbers (RS-274X X2), Excellon drill (PTH, NPTH), Gerber job file
  rp2350_dev_bom.csv         BOM: 77 placements on 32 lines, MPN plus LCSC/Digikey numbers
  rp2350_dev_centroid.csv    Pick-and-place in mm, origin at the bottom-left board corner, top side only
  rp2350_dev_assembly.pdf    Top assembly drawing: outlines, references, polarity marks

PCB
  Size             30.48 x 70.00 mm, rectangular
  Layers           4: F.Cu / In1.Cu (GND plane) / In2.Cu (+3V3 plane and signals) / B.Cu
  Thickness        1.6 mm FR-4
  Stackup          PCBWay standard 4-layer 1.6 mm, 1 oz: F.Cu | prepreg 0.11 mm | In1 | core 1.13 mm | In2 |
                   prepreg 0.11 mm | B.Cu. No impedance control needed
  Copper           1 oz on all layers
  Min track/space  0.127 / 0.127 mm (5/5 mil)
  Min via          0.5 mm pad, 0.2 mm drill
  Surface finish   ENIG
  Solder mask      green, both sides. Silkscreen white, both sides
  Vias             VIA-IN-PAD. Resin-filled and copper-capped (plated over), IPC-4761 Type VII / POFV.
                   About 75 vias sit inside SMD pads (RP2350 QFN-60, BQ24074 QFN-16 thermal pad, 0402 parts).
                   Open vias there wick solder away from the joint. Please fill and cap all vias
  Edges            no castellations, edge plating or gold fingers

Assembly
  Side             top side only. The bottom side has no parts
  Sourcing         turnkey, PCBWay sources every part. The MPN is binding, LCSC numbers are a sourcing
                   reference. The "Alternate" column lists approved substitutes
  Not placed       J5, J6 (0.1 in header pads). They are not in the BOM or the centroid file
  Fiducials        FID1, FID2, FID3: 1 mm copper, 2 mm mask opening, top side
  Rotation         KiCad convention: 0 deg = library footprint orientation, counter-clockwise positive.
                   Please check polarity against the assembly drawing, especially U1-U7, D1 (pin-1 corner),
                   D2 (LED cathode), L1 (polarity dot) and Y1
  Moisture         bake moisture-sensitive parts as their reel label requires
  Programming      none. With blank flash the RP2350 boots into its USB bootloader
  Inspection       X-ray of U1 and U5 recommended (QFN exposed pads)
