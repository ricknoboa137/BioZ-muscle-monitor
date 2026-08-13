"""Bring the three plan files and the dossier source up to the final state."""
import io, os

D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BLOCK = u"""
# 14. The five bumps that cannot be routed on four layers

U1 is 5 x 5 on 0.40 mm pitch with 0.25 mm NSMD pads, so the clear gap between
two adjacent pads is 0.150 mm. At the 3/3 mil class the brief specifies for the
escape region, a track needs trace + 2 x space = 0.075 + 0.150 = 0.225 mm. It
does not fit. It would need 2/2 mil.

! CONSEQUENCE: the 16 outer-ring bumps escape on F.Cu and are routed. The eight second-ring bumps and the centre cannot, and take a via in pad. Two of those nine are grounds and land straight on their own plane. The remaining FIVE are signals with nowhere to go on a four-layer stack, because the layer directly beneath is the ground plane.

|# Bump | Net | Why it matters
| B3 | EL_SENN | HALF THE SENSE PAIR. Without it there is no differential measurement. This is the most important unrouted net on the board.
| B4 | CAL_S second leg | The four-wire Kelvin degrades to three wires. CAL_S still reaches R7 through B5, so calibration works, but not as a true four-wire.
| C2 | VREF | The ADC reference buffer capacitor C1 cannot be connected.
| C4 | DRVSJ | The drive amplifier summing junction. C7 reaches DRVXC but not DRVSJ.
| D2 | AFE_CS | No chip select, so no SPI transactions.

Three ways out, in increasing cost:

N Get ADI Application Note 1891 and use the land pattern it specifies. If ADI recommends a pad smaller than 0.25 mm, the gap widens and a 2/2 mil escape may become legal. This is the cheapest route and it is blocked only by the datasheet being unreachable.
N Ask the fabricator for a 2/2 mil escape region. Several HDI houses will quote it. The brief's 3/3 mil is a stated assumption, not a measured limit.
N Go to six layers, with L2 as ground and L3 as a signal escape layer. This removes the problem entirely and is what most 0.4 mm WLP designs on this bump count actually do.

B Until one of those is settled, the board cannot be fabricated as a working instrument. Everything else on it is complete.
"""

# ---- dossier source -------------------------------------------------------
p = os.path.join(D, "docx-source.txt")
s = io.open(p, encoding="utf-8").read()
s = s.replace(
    u"! STATE OF THIS BOARD: placed, poured, shielded and PARTIALLY ROUTED at "
    u"ZERO DRC errors. 30 tracks and 25 vias are down - the RF chain, both "
    u"special RF grounds, the switching loop, OUTS, VBAT_SENSE and every "
    u"thermal via array. 127 unconnected items remain: U1’s WLP escape, the "
    u"patient bundle, the CAL Kelvin, and all of categories 3 and 4. Do not "
    u"read the renders as a finished board.",
    u"! STATE OF THIS BOARD: 62.0 x 44.0 mm, shielded, placed, poured and ROUTED THROUGH THE WHOLE OF BRIEF SECTION 11 THAT IS PHYSICALLY ROUTABLE, at ZERO DRC errors. The RF chain, both special RF grounds, the switching loop, OUTS, VBAT_SENSE, the thermal via arrays, U1's outer-ring escape, the patient bundle to J1 and the CAL Kelvin are all drawn. Five second-ring WLP bumps cannot be routed on four layers - see section 14. Categories 3 and 4 are not autorouted.")
s = s.replace(u"| Routing, categories 1 and 2 | PARTLY DONE - 30 tracks, 25 vias, 0 DRC errors",
              u"| Routing, brief section 11 | DONE except five trapped WLP bumps - 0 DRC errors")
s = s.replace(u"| Routing, U1 escape / patient bundle / CAL Kelvin | NOT DRAWN - specified net by net in routing-order.md",
              u"| U1 escape, patient bundle, CAL Kelvin | DRAWN. Outer ring on F.Cu, grounds on microvias in pad")
if u"# 14. The five bumps" not in s:
    s = s.replace(u"E This board is set up so that routing", BLOCK + u"\nE This board is set up so that routing")
s = s.replace(u"E This board is set up so that routing is possible and checkable, and so that the two things most likely to be got wrong — the single ground stitch and the antenna keepout — are verified automatically rather than by eye. Route categories 1 and 2 by hand, lock them, autoroute the rest, then re-run scripts/verify_board.py. If either check goes from PASS to FAIL, the routing broke it, and you will know exactly which layer.",
              u"E The board is shielded, placed, poured and routed through everything in brief section 11 that four layers allow, at zero DRC errors, with the single ground stitch and the antenna keepout both verified automatically rather than by eye. What remains is one question with three known answers: how to escape five trapped bumps on a 0.4 mm WLP. Answer that and the board is finished.")
io.open(p, "w", encoding="utf-8").write(s)

# ---- checklist ------------------------------------------------------------
p = os.path.join(D, "pre-gerber-checklist.md")
s = io.open(p, encoding="utf-8").read()
add = u"""
## A0. Blocking, found during routing

- [ ] **[OPEN] Five WLP bumps have no route on a four-layer stack.**
      B3 (EL_SENN), B4 (CAL_S 2nd leg), C2 (VREF), C4 (DRVSJ), D2 (AFE_CS).
      A 0.40 mm pitch with 0.25 mm pads leaves a 0.150 mm gap; a 3/3 mil track
      needs 0.225 mm. The outer ring escapes on F.Cu and is routed; the second
      ring needs via-in-pad, and beneath it is the ground plane.
      **EL_SENN is half the sense pair — without it there is no measurement.**
      Resolve by (a) obtaining AN-1891 and using ADI's pad size, (b) buying a
      2/2 mil escape region from the fabricator, or (c) going to six layers.
- [ ] **[OPEN] Y-axis manufacturing tolerance.** The board height is fully
      committed: antenna keepout 6.82 + shield frame land 26.50 + connector
      row 10.28 = 43.60 mm of 44.00 mm, leaving **0.40 mm of slack in total**.
      There is no room for accumulated tolerance between the fabricated
      outline, the frame land and the enclosure rails. **Measure the first
      fabricated board and the actual enclosure cavity before committing to
      assembly**, and confirm the frame seats without fouling the connector
      row or the keepout.
"""
if "## A0." not in s:
    s = s.replace(u"## A. Blocking", add + u"\n## A. Blocking")
s = s.replace(u"      FINAL STATE on the 62 x 44 mm shielded board: **0 DRC errors.**\n      30 tracks and 25 vias placed",
              u"      FINAL STATE on the 62 x 44 mm shielded board: **0 DRC errors.**\n      All of brief section 11 that four layers permit is routed")
io.open(p, "w", encoding="utf-8").write(s)

# ---- routing order --------------------------------------------------------
p = os.path.join(D, "routing-order.md")
s = io.open(p, encoding="utf-8").read()
s = s.replace(u"**State: 62.0 x 44.0 mm, shielded, placed, poured, partially hand-routed at\n0 DRC errors.** 30 tracks and 25 vias are down; 127 unconnected items remain",
              u"**State: 62.0 x 44.0 mm, shielded, placed, poured and hand-routed through all\nof section 11 that four layers permit, at 0 DRC errors.** 113 unconnected\nitems remain: five trapped WLP bumps (see below) and all of categories 3-4")
io.open(p, "w", encoding="utf-8").write(s)
print("docs updated")
