# BioZ Muscle Monitor — Reverse-Engineered Hardware

A portable, battery-powered bioimpedance spectroscopy (BIS) device that measures
biceps muscle impedance during and after exercise, to track fatigue and fluid
shift. Tetrapolar (4-electrode) measurement, 20 frequencies swept once per
second, 2 hours of on-device logging, BLE offload, ~21 days between charges.

This project reverse-engineers the device described in an unpublished 2026
undergraduate thesis from a Hungarian technical university's electrical
engineering programme (cited without naming the student, supervisors, or
institution, out of respect for their privacy — see
[`00-context-reverse-engineered.md`](00-context-reverse-engineered.md) for the
full extracted specification). It is a *corrected* reproduction, not a
transcription: every part number is verified against its real datasheet, and
every defect found in the source design — swapped connections, missing
decoupling, wrong ground references — is called out and fixed rather than
copied forward.

Built as a working test of an automated hardware-design pipeline: schematic →
PCB layout → 3D-printable enclosure, each stage driven by an agent that reads
real datasheets, verifies its own work against real design-rule checks and the
manufacturer's own documentation, and refuses to silently relax a constraint or
claim something is finished when it isn't.

## Status — read this before trusting any file in here as final

**Schematic: done.** Verified against manufacturer datasheets, 8 defects found
in the source design fixed and documented, KiCad-ready net list.

**PCB layout: in progress, not fab-ready.** The board routes and passes DRC
against its real custom design rules (fixed this session — see below), but
still has open items: unconnected nets remaining, and several trace-width
categories still need widening/re-routing. See
[`pcb/CHECKPOINT.md`](pcb/CHECKPOINT.md) for the exact, currently-accurate
state — it is updated continuously and is more current than this README.

**Enclosure: in progress.** A parametric two-part case exists in SOLIDWORKS
with STL exports, built to fit the current (grown) board size and a
side-by-side battery arrangement. Several dimensions (behind-panel depth for
the pushbutton, cutouts for the slide switch and magnetic connector) are still
provisional pending parts that could not be fully verified from public
datasheets. See [`case/CHECKPOINT.md`](case/CHECKPOINT.md).

### A finding worth knowing about before you trust a "0 errors" claim anywhere in this history

For a significant part of this project, the PCB's custom design rules
(patient-electrode clearance, RF isolation, the ground-plane split integrity)
were **silently inactive** — one malformed rule voided the entire rules file,
and even fixed, rule ordering meant permissive defaults would have overridden
the strict ones. Every earlier "0 DRC errors" claim in this project's history
was checked against KiCad's generic defaults, not the actual project rules.
This has since been found, fixed, and verified with a controlled test (a
deliberately-bad track that must trigger a specific named rule) rather than
just re-running DRC and hoping. The real violations that were hiding behind it
— including patient-safety clearance and ground-split violations — are being
worked through; see the PCB checkpoint for the current count. This is
disclosed here deliberately: a device that will contact human skin should not
have its safety-relevant checks trusted just because a tool once reported zero.

## Layout

```
00-context-reverse-engineered.md   Extracted, datasheet-verified spec from the source thesis
pcb-brief.md                       Schematic -> PCB handoff: constraints, net classes, keepouts
schematic.html                     Schematic drawing source
docx-source.txt                    Design dossier source (OOXML builder markup)
BioZ-Muscle-Monitor-Design-Dossier-RevB.docx   Full schematic-stage design dossier
BioZ-Muscle-Monitor-Layout-RevB.docx           PCB layout dossier
img/                               Schematic sheet renders

pcb/
  BioZ-Muscle-Monitor.kicad_*      KiCad 10 project, board, net classes, custom DRC rules
  BioZ-Muscle-Monitor.pretty/      Custom footprints (0.4mm-pitch WLP, antenna, shield frame, etc.)
  CHECKPOINT.md                    Authoritative, continuously-updated layout status
  placement-plan.md, routing-order.md, pre-gerber-checklist.md
  scripts/                         Reproducible pcbnew/KiCad automation used to build and verify the board
  img-layout/, img-3d/             Rendered plots and 3D views

case/
  CHECKPOINT.md                    Authoritative, continuously-updated enclosure status
  cad/                             SOLIDWORKS parts + the Python build scripts that generate them
  stl/                             Print-ready STL exports
```

## Tooling

KiCad 10.0.5, Freerouting 2.3.0 (Java 25 JRE), SOLIDWORKS 2026 SP03 via its COM
API, and a dependency-free OOXML `.docx` builder — no Python required for the
schematic or PCB documentation stages. See each `CHECKPOINT.md` for the
specific hard-won API/tooling traps found and fixed along the way.

## What this is not

Not a certified medical device. Not reviewed against IEC 60601-1 patient
auxiliary current limits (an open item, flagged as blocking any human use in
the design dossier). Not fabricated or assembled — this is a verified design,
not a built and tested unit.
