"""Rebuild figure 2 of the layout dossier for the 62 x 44 mm shielded board."""
import io, os

P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "layout-figures.html")
s = io.open(P, encoding="utf-8").read()
i = s.find("<!-- FIG 2")
j = s.find("<!-- FIG 3")

fig2 = u"""<!-- FIG 2: zone map -->
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="700" viewBox="0 0 900 700" font-family="Segoe UI, Arial" font-size="13">
  <text x="20" y="26" font-size="18" font-weight="700">Zone map — 62.0 × 44.0 mm, split at X = 20.0 mm, WE-SHC frame over the power section</text>
  <g transform="translate(42,46) scale(12.9)">
    <rect x="0" y="0" width="62" height="44" rx="2" fill="#fafafa" stroke="#222" stroke-width="0.14"/>
    <rect x="0.3" y="0.3" width="19.3" height="43.4" fill="#dcecdc"/>
    <rect x="20.4" y="0.3" width="41.3" height="43.4" fill="#dde6f2"/>
    <rect x="25" y="0" width="37" height="6.82" fill="#ffffff" stroke="#b03030" stroke-width="0.2" stroke-dasharray="0.6,0.35"/>
    <rect x="19.6" y="0" width="0.8" height="24.4" fill="#ffffff"/>
    <rect x="19.9" y="24.4" width="0.2" height="3.2" fill="#ffffff"/>
    <rect x="19.6" y="27.6" width="0.8" height="16.4" fill="#ffffff"/>
    <rect x="35.2" y="7.2" width="26.5" height="26.5" fill="none" stroke="#7a5c00" stroke-width="0.55" opacity="0.85"/>
    <rect x="0.5" y="14" width="48" height="30" fill="none" stroke="#c07000" stroke-width="0.18" stroke-dasharray="1.0,0.7"/>
    <g fill="none" stroke="#555" stroke-width="0.12">
      <rect x="28.4" y="6.4" width="4.8" height="5.2"/>
      <rect x="27.3" y="11.7" width="6.6" height="6.6"/>
      <rect x="21.0" y="10.4" width="3.6" height="3.6"/>
      <rect x="21.0" y="16.6" width="3.6" height="3.6"/>
      <rect x="39.7" y="17.6" width="5.6" height="4.8"/>
      <rect x="51.6" y="12.6" width="4.8" height="4.8"/>
      <rect x="17.5" y="23.6" width="4.6" height="4.8"/>
      <rect x="24.4" y="25.4" width="2.8" height="2.8"/>
    </g>
    <g font-size="0.92" fill="#111">
      <text x="26.0" y="3.3">ANTENNA KEEPOUT — 6.82 mm, no copper on any layer</text>
      <text x="28.7" y="9.3">RF</text>
      <text x="27.7" y="15.3">U5</text>
      <text x="21.2" y="12.5">IC1</text>
      <text x="21.2" y="18.7">U2</text>
      <text x="40.0" y="20.4">U7</text>
      <text x="51.9" y="15.4">U8</text>
      <text x="17.7" y="26.4">U1</text>
      <text x="24.5" y="27.1">U14</text>
      <text x="2.5" y="25.6">ANALOG (GNDA)</text>
      <text x="2.5" y="27.2">U1 R7 R5 R6 C5 C6</text>
      <text x="2.5" y="28.8">U10 J1</text>
      <text x="36.6" y="4.6" fill="#7a5c00">shield frame land, 26.5 mm square</text>
      <text x="22.5" y="37.4">DIGITAL / POWER (GNDD)</text>
      <text x="21.6" y="42.6">P1</text>
      <text x="32.6" y="42.4">SW1 U9</text>
      <text x="39.6" y="42.4">J7</text>
      <text x="49.6" y="42.4">J8</text>
      <text x="1.4" y="42.8">J1 electrode exit</text>
    </g>
    <g font-size="0.82" fill="#c07000">
      <text x="13.5" y="40.6">battery cell, stacked underneath, X 0.5 to 48.5 mm</text>
    </g>
    <g font-size="0.88" fill="#b03030"><text x="15.0" y="21.6">R1 stitch</text></g>
    <circle cx="20" cy="26" r="0.45" fill="#b03030"/>
  </g>
  <g font-size="13" fill="#333">
    <text x="42" y="648">Green = GNDA, blue = GNDD. The white channel is the single split, necking to 0.2 mm under U1. Brown = the WE-SHC solder ring.</text>
    <text x="42" y="670">Y is the binding dimension: keepout 6.82 + frame 26.50 + connector row 10.28 = 43.60 of 44.00 mm, leaving 0.40 mm of slack in total.</text>
  </g>
</svg>

"""

s = s[:i] + fig2 + s[j:]
s = s.replace(u"6.82 mm of ground clearance from the board edge, over a",
              u"6.82 mm of ground clearance from the board edge, over a 37 mm span. On a")
s = s.replace(u"<text x=\"474\" y=\"112\">25 mm span. The figure is read off the Würth 74889302450</text>",
              u"<text x=\"474\" y=\"112\">37 mm span. The figure is read off the Würth 74889302450</text>")
io.open(P, "w", encoding="utf-8").write(s)
print("figure 2 rebuilt for the 62 x 44 mm board")

