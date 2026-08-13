"""Generate the custom footprints this design needs and KiCad does not ship.

Every dimension here is traceable:
  MAX30009 WLP-25 : body/pitch from the MAX30009 datasheet (2.03 x 2.03 mm,
                    5x5 bumps, 0.40 mm pitch). Pad diameter is the ADI generic
                    0.4 mm-WLP NSMD recommendation. ** LAND PATTERN UNVERIFIED **
                    -- ADI AN-1891 could not be fetched (analog.com timed out).
  WE-MCA AE1      : land pattern read from the Wurth 74889302450 datasheet
                    p.1 "Recommended Land Pattern" -> 4.2 outer / 2.6 gap /
                    1.6 wide  =>  two 0.8 x 1.6 pads on 3.4 mm centres.
                    Pad 1 = Feeding Point, pad 2 = NC (datasheet p.2).
  CY15V108QI      : body 3.23 x 3.28 mm from the Infineon product page.
                    ** PAD GEOMETRY UNVERIFIED ** -- placeholder, must be taken
                    from Infineon doc 002-18131 before fabrication.
"""
import os, uuid, math

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "BioZ-Muscle-Monitor.pretty")
os.makedirs(OUT, exist_ok=True)


def u():
    return str(uuid.uuid4())


def head(name, descr, tags):
    return f'''(footprint "{name}"
\t(version 20240108)
\t(generator "bioz-pcb-agent")
\t(layer "F.Cu")
\t(descr "{descr}")
\t(tags "{tags}")
\t(attr smd)
\t(property "Reference" "REF**" (at 0 -2.6 0) (layer "F.SilkS") (uuid "{u()}")
\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))
\t(property "Value" "{name}" (at 0 2.6 0) (layer "F.Fab") (uuid "{u()}")
\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))
\t(property "Datasheet" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{u()}")
\t\t(effects (font (size 1 1) (thickness 0.15))))
\t(property "Description" "" (at 0 0 0) (layer "F.Fab") (hide yes) (uuid "{u()}")
\t\t(effects (font (size 1 1) (thickness 0.15))))
'''


def rect(layer, x1, y1, x2, y2, w):
    s = ""
    pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    for i in range(4):
        s += (f'\t(fp_line (start {pts[i][0]:.4f} {pts[i][1]:.4f}) '
              f'(end {pts[i+1][0]:.4f} {pts[i+1][1]:.4f}) '
              f'(stroke (width {w}) (type solid)) (layer "{layer}") (uuid "{u()}"))\n')
    return s


def circ_pad(n, x, y, d):
    return (f'\t(pad "{n}" smd circle (at {x:.4f} {y:.4f}) (size {d} {d}) '
            f'(layers "F.Cu" "F.Mask" "F.Paste") (uuid "{u()}"))\n')


def rect_pad(n, x, y, w, h):
    return (f'\t(pad "{n}" smd rect (at {x:.4f} {y:.4f}) (size {w} {h}) '
            f'(layers "F.Cu" "F.Mask" "F.Paste") (uuid "{u()}"))\n')


# ---------------------------------------------------------------- MAX30009 WLP
# Rows A..E run along +X, columns 1..5 run along +Y.  This orientation is
# deliberate: it puts the analog rows (A,B,C) on the -X side and the digital
# rows (D,E) on the +X side, so the GNDA/GNDD split can pass straight through
# the package between row C and row D.
PITCH = 0.40
PAD_D = 0.25          # NSMD copper pad, 0.4 mm pitch WLP
BODY = 2.03
s = head("MAX30009ENA_WLP25_2.03x2.03_P0.4mm",
         "MAX30009 BioZ AFE, 25-bump WLP 2.03x2.03mm 0.40mm pitch, NSMD pads. "
         "LAND PATTERN NOT VERIFIED AGAINST ADI AN-1891.",
         "WLP CSP BGA MAX30009")
s += rect("F.Fab", -BODY / 2, -BODY / 2, BODY / 2, BODY / 2, 0.1)
s += rect("F.CrtYd", -1.4, -1.4, 1.4, 1.4, 0.05)
# pin-1 (A1) marker
s += (f'\t(fp_circle (center -1.25 -1.25) (end -1.15 -1.25) '
      f'(stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS") (uuid "{u()}"))\n')
for ri, r in enumerate("ABCDE"):
    for ci in range(5):
        s += circ_pad(f"{r}{ci+1}", (ri - 2) * PITCH, (ci - 2) * PITCH, PAD_D)
s += f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u()}")\n' \
     f'\t\t(effects (font (size 0.4 0.4) (thickness 0.06))))\n)\n'
open(os.path.join(OUT, "MAX30009ENA_WLP25_2.03x2.03_P0.4mm.kicad_mod"), "w").write(s)

# ------------------------------------------------------------------- WE-MCA
s = head("Wurth_WE-MCA_74889302450",
         "Wurth WE-MCA 2400-2500MHz multilayer chip antenna, 3.2x1.6mm. "
         "Land pattern from datasheet 74889302450 rev 002.000 p.1. "
         "Pad 1 = Feeding Point, pad 2 = NC.",
         "antenna 2.4GHz chip WE-MCA")
s += rect("F.Fab", -1.6, -0.8, 1.6, 0.8, 0.1)
s += rect("F.CrtYd", -2.35, -1.05, 2.35, 1.05, 0.05)
s += rect_pad("1", -1.70, 0.0, 0.8, 1.6)
s += rect_pad("2", 1.70, 0.0, 0.8, 1.6)
s += (f'\t(fp_line (start -2.2 -1.0) (end -2.2 1.0) '
      f'(stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u()}"))\n')
s += f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u()}")\n' \
     f'\t\t(effects (font (size 0.6 0.6) (thickness 0.1))))\n)\n'
open(os.path.join(OUT, "Wurth_WE-MCA_74889302450.kicad_mod"), "w").write(s)

# ------------------------------------------------------------------ CY15V108QI
# 8-GQFN, body 3.23 x 3.28 mm.  Pads placed 4-per-long-side on a 0.80 mm pitch.
# THIS GEOMETRY IS A PLACEHOLDER -- see module docstring.
s = head("Infineon_GQFN-8_3.23x3.28mm",
         "CY15V108QI 8-GQFN 3.23x3.28mm. PAD GEOMETRY IS A PLACEHOLDER, "
         "take from Infineon 002-18131 before fabrication.",
         "GQFN FRAM PLACEHOLDER")
s += rect("F.Fab", -1.615, -1.64, 1.615, 1.64, 0.1)
s += rect("F.CrtYd", -1.95, -1.95, 1.95, 1.95, 0.05)
for i in range(4):                      # pins 1..4 down the -X side
    s += rect_pad(str(i + 1), -1.4, -1.2 + i * 0.8, 0.7, 0.4)
for i in range(4):                      # pins 5..8 up the +X side
    s += rect_pad(str(i + 5), 1.4, 1.2 - i * 0.8, 0.7, 0.4)
s += (f'\t(fp_circle (center -1.75 -1.45) (end -1.65 -1.45) '
      f'(stroke (width 0.12) (type solid)) (fill solid) (layer "F.SilkS") (uuid "{u()}"))\n')
s += f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u()}")\n' \
     f'\t\t(effects (font (size 0.6 0.6) (thickness 0.1))))\n)\n'
open(os.path.join(OUT, "Infineon_GQFN-8_3.23x3.28mm.kicad_mod"), "w").write(s)

# -------------------------------------------------- edge pad row (inverted-U)
# 1.6 mm pitch castellation-style edge pads for the two auxiliary PCBs.
for n, count in (("EdgePads_1x6_P1.6mm", 6),):
    s = head(n, "Edge solder pads for the inverted-U auxiliary PCB, 1.6 mm pitch. "
                "Pad geometry and mechanical load path NOT specified in the source "
                "material -- confirm with mechanical (brief open question 3).",
             "edge pad mechanical")
    span = (count - 1) * 1.6
    for i in range(count):
        s += rect_pad(str(i + 1), 0.0, -span / 2 + i * 1.6, 1.6, 1.0)
    s += rect("F.CrtYd", -0.9, -span / 2 - 0.7, 0.9, span / 2 + 0.7, 0.05)
    s += f'\t(fp_text user "${{REFERENCE}}" (at 0 0 90) (layer "F.Fab") (uuid "{u()}")\n' \
         f'\t\t(effects (font (size 0.6 0.6) (thickness 0.1))))\n)\n'
    open(os.path.join(OUT, n + ".kicad_mod"), "w").write(s)

# ------------------------------------------------- wire solder pads (2 way)
s = head("WirePads_1x2_P2.54mm",
         "Two 1.6 x 2.2 mm solder pads for a hand-soldered flying lead. Used for "
         "the panel-mounted pushbutton SW1 and the cell-mounted NTC U9, neither "
         "of which is board mounted.",
         "wire pad flying lead")
s += rect_pad("1", -1.27, 0.0, 1.6, 2.2)
s += rect_pad("2", 1.27, 0.0, 1.6, 2.2)
s += rect("F.CrtYd", -2.3, -1.35, 2.3, 1.35, 0.05)
s += f'\t(fp_text user "${{REFERENCE}}" (at 0 -1.9 0) (layer "F.SilkS") (uuid "{u()}")\n' \
     f'\t\t(effects (font (size 0.6 0.6) (thickness 0.1))))\n)\n'
open(os.path.join(OUT, "WirePads_1x2_P2.54mm.kicad_mod"), "w").write(s)

# ---------------------------------------------- mini net tie for VSS_PA
# The gap between nRF54L15 pin 32 and the die pad is 0.65 mm, and the
# neighbouring pins are 0.40 mm away.  KiCad's stock net ties are far too big
# for that.  Two 0.25 mm pads on a 0.65 mm pitch fit exactly.
s = head("NetTie-2_0.25mm_P0.65mm",
         "Two 0.25 mm pads on 0.65 mm pitch. Bridges nRF54L15 pin 32 (VSS_PA) "
         "to the die pad, which is the ONLY place VSS_PA may reach ground.",
         "net tie VSS_PA")
s += circ_pad("1", 0.0, -0.325, 0.25)
s += circ_pad("2", 0.0, 0.325, 0.25)
s += rect("F.CrtYd", -0.16, -0.49, 0.16, 0.49, 0.05)
s += ")\n"
open(os.path.join(OUT, "NetTie-2_0.25mm_P0.65mm.kicad_mod"), "w").write(s)

# ------------------------------------------------- WE-SHC shield frame
# Wurth 36103255, 26 x 26 x 3 mm two-piece SMD frame.  Recommended land
# pattern from the datasheet rev 003.004 p.1: 26.5 x 26.5 mm outer with a
# 1.0 mm wide continuous solder ring.  Modelled as four overlapping
# rectangular pads on one pad number, so the ring is electrically unbroken.
s = head("Wurth_WE-SHC_36103255_26x26mm",
         "Wurth WE-SHC 26x26x3mm two-piece SMD shielding frame. Land pattern "
         "from datasheet 36103255 rev 003.004 p.1: 26.5 mm outer, 1.0 mm ring. "
         "Frame 3.0 mm high, 3.5 mm with the cover fitted.",
         "shield frame EMI WE-SHC")
O_, RW = 26.5, 1.0
_h = O_ / 2.0
_i = O_ / 2.0 - RW / 2.0
s += rect_pad("1", 0.0, -_i, O_, RW)
s += rect_pad("1", 0.0, _i, O_, RW)
s += rect_pad("1", -_i, 0.0, RW, O_)
s += rect_pad("1", _i, 0.0, RW, O_)
s += rect("F.CrtYd", -_h - 0.25, -_h - 0.25, _h + 0.25, _h + 0.25, 0.05)
s += rect("F.Fab", -13.0, -13.0, 13.0, 13.0, 0.1)
s += ('\t(fp_text user "${REFERENCE}" (at 0 %.2f 0) (layer "F.SilkS") '
      '(uuid "%s")\n\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))\n)\n'
      % (-(_h + 0.9), u()))
open(os.path.join(OUT, "Wurth_WE-SHC_36103255_26x26mm.kicad_mod"), "w").write(s)

print("wrote footprints to", OUT)
for f in sorted(os.listdir(OUT)):
    print("  ", f)

