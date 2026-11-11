#!/usr/bin/env python3
"""Write the .kicad_pro (design rules, net classes) and .backplane.json."""
import os, json
import design as D
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'boards', D.NAME)
def nc(name, clearance, track, via_d=0.6, via_h=0.3, prio=0):
    return {"name": name, "clearance": clearance, "track_width": track, "via_diameter": via_d, "via_drill": via_h,
            "microvia_diameter": 0.3, "microvia_drill": 0.1, "diff_pair_width": 0.2, "diff_pair_gap": 0.15,
            "diff_pair_via_gap": 0.25, "bus_width": 12, "wire_width": 6, "line_style": 0,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": prio,
            "tuning_profile": ""}
pro = {
  "board": {"design_settings": {
      "defaults": {"zones": {"min_clearance": 0.2}},
      "diff_pair_dimensions": [], "drc_exclusions": [],
      "rules": {
          "max_error": 0.005, "min_clearance": 0.127, "min_connection": 0.0, "min_copper_edge_clearance": 0.3,
          "min_groove_width": 0.0, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2,
          "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0, "min_text_height": 0.6,
          "min_text_thickness": 0.08, "min_through_hole_diameter": 0.3, "min_track_width": 0.127,
          "min_via_annular_width": 0.1, "min_via_diameter": 0.5, "solder_mask_to_copper_clearance": 0.0,
          "use_height_for_length_calcs": True},
      "rule_severities": {"lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
                          "silk_over_copper": "ignore", "silk_overlap": "ignore", "silk_edge_clearance": "ignore",
                          "text_height": "ignore", "text_thickness": "ignore"},
      "track_widths": [0.0, 0.15, 0.2, 0.3, 0.5], "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                                                                    {"diameter": 0.6, "drill": 0.3}],
      "zones_allow_external_fillets": False}},
  "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "meta": {"filename": D.NAME + ".kicad_pro", "version": 3},
  "net_settings": {
      "classes": [nc("Default", 0.15, 0.15), nc("Power", 0.15, 0.4, prio=1)],
      "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None,
      "netclass_patterns": [{"netclass": "Power", "pattern": n} for n in
                            ("GND", "+3V3", "+1V1", "VBUS", "VBAT", "VSYS", "/VREG_LX", "/VREG_AVDD")]},
  "pcbnew": {"page_layout_descr_file": ""}, "sheets": [], "text_variables": {}}
json.dump(pro, open(os.path.join(OUT, D.NAME + '.kicad_pro'), 'w'), indent=2)
bp = os.path.join(ROOT, '.backplane.json')
cur = json.load(open(bp)) if os.path.exists(bp) else {}
cur['project'] = 'boards/%s/%s.kicad_pro' % (D.NAME, D.NAME)
json.dump(cur, open(bp, 'w'), indent=2)
print('project written')
