"""Write the .kicad_pro with PCBWay-compatible design rules and net classes."""
import json, os
import design
HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, '..', 'boards', design.PROJECT)

def nc(name, clearance, track, via_d=0.6, via_dr=0.3, prio=0, dp_w=0.2, dp_g=0.15):
    return {"bus_width": 12, "clearance": clearance, "diff_pair_gap": dp_g, "diff_pair_via_gap": 0.25,
            "diff_pair_width": dp_w, "line_style": 0, "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "name": name, "pcb_color": "rgba(0, 0, 0, 0.000)", "priority": prio,
            "schematic_color": "rgba(0, 0, 0, 0.000)", "track_width": track, "via_diameter": via_d,
            "via_drill": via_dr, "wire_width": 6}

pro = {
  "meta": {"filename": design.PROJECT + ".kicad_pro", "version": 3},
  "board": {
    "design_settings": {
      "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "silk_line_width": 0.15,
                   "silk_text_size_h": 0.8, "silk_text_size_v": 0.8, "silk_text_thickness": 0.15,
                   "zones": {"min_clearance": 0.2}},
      "diff_pair_dimensions": [{"gap": 0.15, "via_gap": 0.25, "width": 0.25}],
      "drc_exclusions": [],
      "meta": {"version": 2},
      "rule_severities": {
        "silk_overlap": "warning", "silk_over_copper": "warning", "silk_edge_clearance": "warning",
        "lib_footprint_issues": "ignore", "lib_footprint_mismatch": "ignore",
        "text_height": "warning", "text_thickness": "warning",
        "courtyards_overlap": "error", "missing_courtyard": "ignore",
        "footprint_type_mismatch": "ignore", "via_dangling": "warning", "track_dangling": "warning",
        "isolated_copper": "warning", "starved_thermal": "warning",
        "solder_mask_bridge": "error"
      },
      "rules": {
        "max_error": 0.005, "min_clearance": 0.12, "min_connection": 0.15,
        "min_copper_edge_clearance": 0.25, "min_groove_width": 0.0, "min_hole_clearance": 0.15,
        "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2, "min_microvia_drill": 0.1,
        "min_resolved_spokes": 1, "min_silk_clearance": 0.0, "min_text_height": 0.6,
        "min_text_thickness": 0.1, "min_through_hole_diameter": 0.25, "min_track_width": 0.15,
        "min_via_annular_width": 0.15, "min_via_diameter": 0.55, "solder_mask_clearance": 0.0,
        "solder_mask_min_width": 0.0, "solder_mask_to_copper_clearance": 0.0,
        "use_height_for_length_calcs": True
      },
      "track_widths": [0.0, 0.15, 0.2, 0.3, 0.4, 0.5, 0.8],
      "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
      "zones_allow_external_fillets": False
    },
    "layer_presets": [], "viewports": []
  },
  "boards": [],
  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
  "net_settings": {
    "classes": [nc("Default", 0.15, 0.2, prio=2147483647),
                nc("Power", 0.15, 0.4, prio=1),
                nc("USB", 0.15, 0.25, prio=0, dp_w=0.25, dp_g=0.15)],
    "meta": {"version": 4},
    "net_colors": None,
    "netclass_assignments": None,
    "netclass_patterns": [
      {"netclass": "Power", "pattern": "VBUS"}, {"netclass": "Power", "pattern": "VSYS"},
      {"netclass": "Power", "pattern": "VBAT"}, {"netclass": "Power", "pattern": "+3V3"},
      {"netclass": "Power", "pattern": "GND"},
      {"netclass": "USB", "pattern": "USB_D*"}]
  },
  "pcbnew": {"page_layout_descr_file": ""},
  "schematic": {"page_layout_descr_file": "", "meta": {"version": 1}},
  "sheets": [[s, n] for s, n in [("" , "Root")]] and [],
  "text_variables": {}
}
json.dump(pro, open(os.path.join(B, design.PROJECT + '.kicad_pro'), 'w'), indent=2)
print('project written')
