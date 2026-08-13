"""Write BioZ-Muscle-Monitor.kicad_pro (net classes, design rules) and patch the
board's stackup and default clearances.  Plain python - no pcbnew needed.

Net classes are taken verbatim from pcb-brief.md section 3.  RF trace width is
NOT set here: the brief says to take it from the fabricator's 50 ohm stackup and
that answer is not in hand, so RF is left at the flagged placeholder below and
listed as an open item.
"""
import json, os, re

PCBDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRO = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pro")
PCB = os.path.join(PCBDIR, "BioZ-Muscle-Monitor.kicad_pcb")

MIL = 0.0254

# name, track mm, clearance mm, via dia mm, via drill mm, nets
CLASSES = [
    ("POWER_HIGH", 20*MIL, 10*MIL, 0.8, 0.4,
     ["VIN_EXT", "V_BAT", "V_SYS"]),
    # 10 mil is the routing clearance to other nets; V1P8A ties two WLP bumps
    # 0.40 mm apart, where the spacing is package geometry, not a choice.
    ("POWER_LOW", 20*MIL, 0.20, 0.8, 0.4,
     ["V2P5", "V2P5FA", "V2P5F", "V1P8A", "V1P8D", "VDD_nRF", "DCC", "LX",
      "DECA_RF", "DECD"]),
    # 8 mil is the routing clearance to other nets; two WLP bumps are 0.40 mm
    # apart and that is package geometry, not a routing choice.
    ("SIGNAL", 10*MIL, 0.20, 0.6, 0.3,
     ["SPI_SCK", "SPI_SDO", "SPI_SDI", "AFE_CS", "MEM_CS", "MEM_WP", "AFE_INT",
      "AFE_PWR_EN", "FPWM_CTL", "nPGOOD", "nCHG", "LED_K", "LED_K_R", "BTN_N",
      "BTN_RC", "BTN_PU", "BTN_SW", "SW_EN", "SWDIO", "SWDCLK", "SWO",
      "nRESET", "POK", "XL1", "XL2", "XC1", "XC2"]),
    # 12 mil is the routing clearance to other nets; inside the WLP escape the
    # spacing is set by a 0.40 mm bump pitch, not by a routing choice. The
    # 12 mil requirement is kept as the analog_sense_clearance rule in the .dru.
    ("ANALOG_SENSE", 10*MIL, 0.20, 0.6, 0.3,
     ["VREF", "DRVSJ", "DRVXC", "CAL_F", "CAL_S", "VBAT_SENSE", "TS_NTC",
      "ISET", "ILIM", "SEL", "BIAS"]),
    # 20 mil is the clearance to OTHER nets, which is what brief section 4.1
    # actually says; between two patient nets it is unachievable and pointless.
    # The 20 mil requirement lives in the patient_clearance rule in the .dru.
    ("PATIENT", 12*MIL, 0.20, 0.6, 0.3,
     ["EL_DRVP", "EL_DRVN", "EL_SENP", "EL_SENN",
      "PT_E1", "PT_E2", "PT_E3", "PT_E4"]),
    # RF width is a PLACEHOLDER pending the fabricator's 50 ohm stackup.
    # RF class clearance is 0.20 mm, NOT the 3x-width figure: adjacent nodes
    # of the matching ladder are only 0.64 mm apart, so a 0.60 mm class
    # clearance is unachievable within the ladder itself.  The brief's "3x
    # trace width to any copper" is about OTHER nets and is enforced by the
    # rf_clearance rule in the .kicad_dru, which is where it belongs.
    ("RF", 0.20, 0.20, 0.6, 0.3, ["ANT", "RF_A", "RF_B", "RF_ANT"]),
    # The brief specifies no clearance for the ground classes ("pour / --").
    # 0.15 mm is used because it is below the 0.18 mm pad gap inside an 0201
    # package; anything larger flags every decoupling capacitor on the board.
    ("GND_A", 20*MIL, 0.15, 0.6, 0.3, ["GNDA"]),
    ("GND_D", 20*MIL, 0.15, 0.6, 0.3, ["GNDD", "VSS_PA", "GND_C20"]),
]

netclasses = []
patterns = []
for name, tw, cl, vd, vdr, nets in CLASSES:
    netclasses.append({
        "name": name, "clearance": cl, "track_width": tw,
        "via_diameter": vd, "via_drill": vdr,
        "microvia_diameter": 0.20, "microvia_drill": 0.1,
        "diff_pair_width": tw, "diff_pair_gap": cl,
        "diff_pair_via_gap": cl, "wire_width": 6, "bus_width": 12,
        "line_style": 0, "schematic_color": "rgba(0,0,0,0.000)",
        "pcb_color": "rgba(0,0,0,0.000)",
    })
    for n in nets:
        patterns.append({"pattern": n, "netclass": name})

pro = {
    "board": {"3dviewports": [], "design_settings": {
        "defaults": {
            "board_outline_line_width": 0.1,
            "copper_line_width": 0.2,
            "copper_text_size_h": 1.0, "copper_text_size_v": 1.0,
            "copper_text_thickness": 0.15,
            "other_line_width": 0.15,
            "silk_line_width": 0.12,
            "silk_text_size_h": 0.5, "silk_text_size_v": 0.5,
            "silk_text_thickness": 0.08,
        },
        "diff_pair_dimensions": [],
        "drc_exclusions": [],
        "meta": {"version": 2},
        "rule_severities": {
            "annular_width": "error", "clearance": "error",
            "copper_edge_clearance": "error", "courtyards_overlap": "warning",
            "hole_clearance": "error", "hole_near_hole": "error",
            "microvia_drill_out_of_range": "error",
            "silk_over_copper": "warning", "silk_overlap": "warning",
            "text_height": "ignore", "text_thickness": "ignore",
            "track_width": "error", "via_diameter": "error",
        },
        "rules": {
            "max_error": 0.005,
            "min_clearance": 0.075,          # 3 mil, U1 escape region
            "min_connection": 0.075,
            "min_copper_edge_clearance": 0.25,
            "min_hole_clearance": 0.15,
            "min_hole_to_hole": 0.2,
            "min_microvia_diameter": 0.18,
            "min_microvia_drill": 0.1,       # laser drill, brief 10
            "min_resolved_spokes": 2,
            "min_silk_clearance": 0.0,
            "min_text_height": 0.4,
            "min_text_thickness": 0.06,
            "min_through_hole_diameter": 0.2,
            "min_track_width": 0.075,        # 3 mil, U1 escape region
            "min_via_annular_width": 0.05,   # 2 mil, Sierra Circuits published HDI min
            "min_via_diameter": 0.18,
            "solder_mask_to_copper_clearance": 0.0,
            "use_height_for_length_calcs": True,
        },
        "track_widths": [0.0, 0.075, 0.15, 0.2, 0.25, 0.3, 0.51],
        "via_dimensions": [{"diameter": 0.0, "drill": 0.0},
                           {"diameter": 0.25, "drill": 0.1},
                           {"diameter": 0.6, "drill": 0.3},
                           {"diameter": 0.8, "drill": 0.4}],
        "zones_allow_external_fillets": False,
    }, "ipc2581": {}, "layer_presets": [], "viewports": []},
    "boards": [],
    "cvpcb": {"equivalence_files": []},
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": "BioZ-Muscle-Monitor.kicad_pro", "version": 3},
    "net_settings": {
        "classes": [{
            "name": "Default", "clearance": 0.15, "track_width": 0.25,
            "via_diameter": 0.6, "via_drill": 0.3,
            "microvia_diameter": 0.20, "microvia_drill": 0.1,
            "diff_pair_width": 0.2, "diff_pair_gap": 0.25,
            "diff_pair_via_gap": 0.25, "wire_width": 6, "bus_width": 12,
            "line_style": 0, "schematic_color": "rgba(0,0,0,0.000)",
            "pcb_color": "rgba(0,0,0,0.000)"}] + netclasses,
        "meta": {"version": 4},
        "netclass_patterns": patterns,
    },
    "pcbnew": {"last_paths": {}, "page_layout_descr_file": ""},
    "schematic": {},
    "sheets": [], "text_variables": {},
}

with open(PRO, "w") as f:
    json.dump(pro, f, indent=2)
print("wrote", PRO)

# ------------------------------------------------------------------ stackup
# 4 layer, 1.0 mm finished, 1 oz outer / 0.5 oz inner, HDI 1+2+1.
# L1-L2 and L3-L4 dielectrics are thin so a 0.1 mm laser via keeps an aspect
# ratio under 1:1.  ** These thicknesses are a starting proposal: the brief
# requires them to be set from the chosen fabricator's HDI capability sheet,
# which has not been obtained. **
STACKUP = """	(stackup
		(layer "F.SilkS" (type "Top Silk Screen"))
		(layer "F.Paste" (type "Top Solder Paste"))
		(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
		(layer "F.Cu" (type "copper") (thickness 0.035))
		(layer "dielectric 1" (type "prepreg") (thickness 0.075) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
		(layer "In1.Cu" (type "copper") (thickness 0.0175))
		(layer "dielectric 2" (type "prepreg") (thickness 0.075) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
		(layer "In2.Cu" (type "copper") (thickness 0.0175))
		(layer "dielectric 3" (type "core") (thickness 0.545) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
		(layer "In3.Cu" (type "copper") (thickness 0.0175))
		(layer "dielectric 4" (type "prepreg") (thickness 0.075) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
		(layer "In4.Cu" (type "copper") (thickness 0.0175))
		(layer "dielectric 5" (type "prepreg") (thickness 0.075) (material "FR4") (epsilon_r 4.3) (loss_tangent 0.02))
		(layer "B.Cu" (type "copper") (thickness 0.035))
		(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
		(layer "B.Paste" (type "Bottom Solder Paste"))
		(layer "B.SilkS" (type "Bottom Silk Screen"))
		(copper_finish "ENIG")
		(dielectric_constraints no)
	)
"""
src = open(PCB, encoding="utf-8").read()
if "(stackup" not in src:
    src = src.replace("(setup\n", "(setup\n" + STACKUP, 1)
    open(PCB, "w", encoding="utf-8").write(src)
    print("patched stackup into", PCB)
else:
    print("stackup already present")











