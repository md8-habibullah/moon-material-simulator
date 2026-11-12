# S012 source issues

NASA KSC slide deck, "Selection, Production and Properties of Regolith Polymer Composite for Lunar Construction" (2024 ASCE Earth and Space, NTRS 20240004186). It is the companion to S003. Page numbers are PDF page indices, which equal the slide numbers.

## Wrong or inconsistent units

- p.11 Results Summary | unit GPa vs MPa | "Typical unreinforced concrete: – Flexural strength 3-5 GPa." vs "Flexural strength of 4-8 Mpa" (lumber, same slide) | The concrete flexural strength should be about 3-5 MPa. S003 p.11 and p.18 have the same error.
- p.11 Results Summary | unit spelling | "Flexural Modulus = 5.3 Gpa @ 0°", "Flexural strength of 4-8 Mpa" | Inconsistent capitalization (GPa, MPa). The values themselves are unambiguous.
- p.10 Beta Test Sample Construction vs p.7 vacuum chart | magnitude | "Vacuum pressure started at ~10-3 torr ends at ~0.8 torr" vs the p.7 "Vacuum Chamber Pressure (torr)" chart, whose axis tops out at 1.00E-01 and whose curve ends near 8.8E-02 | ~0.8 torr should be ~0.08 torr. S003 p.4 has the same error.

## Inconsistent statements

- p.9 Alpha Initial Feasibility Tests | inconsistent conditions | "printing in vacuum (~10^-3 torr)" and "Samples were printed under vacuum (10^-3 torr)" vs "RPC is printed at 0.250 torr on a heated build plate" | The same slide gives two different vacuum levels for the Alpha prints. This does not affect any extracted value.
- p.4 Goals and Objectives vs S003 p.1 | process terminology (cross-source) | "Fused Granular Fabrication (FGF) additive process" vs S003 "A Fused Filament Fabrication (FFF) construction process" | The same pellet-fed process is named differently. The CSV codes it as pellet_AM.

## Values that can't be tied to a specific composition

- p.11 Results Summary table | composition and method not stated | "ISRU Weight Percent 75% (Targeted 80%)" | The table describes the sub-scale LINA construction but names neither the formulation nor how the 75% was measured. 80:20 LHS-1:PLA is inferred from the adjacent bullet and from S003 (and noted in the CSV).
- p.11 bar chart "Mechanical Testing by Independent Lab" | values only in an image | The chart has no printed numbers except the flexural 0° bullet (24 MPa). The digitized compressive 0º bar (~49.4 MPa) agrees with S003's text (49.22 MPa) rather than S003 Table 4 (50 MPa). All digitized bars duplicate S003 Table 4 and are marked as duplicates in S012.csv.
