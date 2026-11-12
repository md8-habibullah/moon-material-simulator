# S008 source issues: Storozhuk et al. 2026, Polymers 18:2371 (doi 10.3390/polym18192371)

Page numbers are PDF page indices (1-based).

## Contradictions and errors inside the source

- p.18 4.2 (Internal Structure) | wrong figure reference | "The X-ray projection image of the composite containing 50 wt.% of the filler showed ... (Figure 6)" vs p.12 "Figure 7. Two-dimensional X-ray projection image of a hot-pressed LR simulant/PEI composite specimen containing 50 wt.%" | The X-ray projection is Figure 7. Figure 6 is the photo of the disks.
- p.22 4.4 | wrong citation | "comparable in magnitude to the compressive-strength levels of structural concrete classes used for terrestrial buildings [64]" vs p.27 ref 64 "Coarse-Grained Molecular Dynamics Modeling of a Branched Polyetherimide" | Ref [64] is a PEI modelling paper. The same claim on p.19 cites [80,81] (BS EN 771-1, Eurocode 2).
- p.21 4.3.3 | text contradicts text | "the CLTE of the composites decreased from 50–60 × 10−6 K−1 for neat polymers" vs p.16 3.6.2 "decreased from 61 × 10−6 K−1 for the neat polymer" | The neat PPSU CLTE of 61 (also Fig. 12b) falls outside the stated 50–60 range.
- p.1 Abstract vs p.23 Conclusions | inconsistent threshold | "At LR simulant contents of up to 60 wt.% for PPSU and 85 wt.% for PEI, dense, low-porosity (<10 vol.%) monolithic composites were formed" vs "binder deficiency at excessive filler loadings, corresponding to ≥70 wt.% for PPSU- and ≥85 wt.% for PEI-based composites, resulted in increased porosity" | 85 wt.% PEI is called both dense and binder-deficient. The data (Fig. 9b, about 9.1 vol.% at 85 wt.%) fit "<10 vol.%". p.13 also says porosity "increased more noticeably at 85 wt.%".
- p.11 3.3 vs p.8 2.4 | minor inconsistency | "a thickness of approximately 4–5 mm" vs "a disc approximately 4–6 mm thick" | The disk thickness is stated two ways.
- p.15 Figure 11a | typo in axis label | "Compressive strengh, MPa" | The axis label is misspelled. The CSV col_label copies it as printed.

## Values that can't be tied to one composition, or are incomplete

- p.22 Table 6 | ranges per composition band | "1.64– 1.75", "5.08– 5.23", "178–193", "7.2– 7.4", "0.38– 0.45", "27.5– 32.0", "7.8–8.5" (row 50–60) and "1.89– 2.02", "5.23– 13.11", "86–94", "30– 146", "3.2– 7.0", "0.49– 0.68", "11.5– 20.0" (row 70–90) | Range cells cover more than one composition. They are not used as values; they appear only in the notes of the matching rows. Only the single-valued cells are extracted: 96 (Shore D, 50–60), 0 (MFI, 70–90) and the whole 92.5 row. Table 6 covers PEI only, with no PPSU summary.
- p.22 Table 6 vs p.14 Figure 9b | small offset | Table 6 implies PEI porosity 13.11 % at 90 wt.% and 13.28 % at 92.5 wt.%, plus a 50–60 band of "5.08–5.23" | Fig. 9b plots 90 and 92.5 wt.% at the same height (about 13.3 vol.%), and 50/60 wt.% at about 5.2/5.4. These differences are only 0.15–0.25 vol.%, inside chart-reading tolerance, but the figure does not exactly match the table. p.18 gives "within 5.08–5.58% up to 80 wt.%" and "about 13.3% at 90–92.5 wt.%".
- p.16 3.7 | range only | "Tg (E′) remained within a relatively narrow range from 196.7 to 207.0 ◦ C over the investigated composition range" | The text gives no composition for these numbers. Fig. 13a shows the minimum at 0 wt.% and the maximum at 80 wt.%, so they were assigned to neat PPSU and 80 wt.% with confidence medium.
- p.16 3.7 | qualitative only | "reaching 222.6 ◦ C at 70 wt.% of the filler and remaining at a similar level at 80 wt.%" | No number for PEI Tg(E′) at 80 wt.%. Digitized from Fig. 13a (about 221.6 °C).
- p.11 3.3 / p.11 Table 4 vs p.14–17 Figures 9–14 | missing data | Table 4 lists a PPSU composite at 85 wt.% ("74.1" vol.%) and p.11 says PPSU composites of "50–90 wt.%" were obtained | PPSU 85 wt.% appears only in the porosity curve of Fig. 9a (about 34.5 vol.%). No density, hardness, compression, λ, CLTE, DMA or MFI point exists for it. Also, Fig. 9b has a PEI porosity point at 85 wt.% but no density point, and Fig. 9a likewise has no PPSU density point at 85 wt.%.
- p.17 Figure 14 | hidden markers | PPSU MFI markers at 80 and 90 wt.% sit at 0, completely behind the PEI markers | Only grey edge pixels are visible, and similar edges also appear at 92.5 wt.%, where no PPSU composite exists. These rows are recorded as 0 with confidence low, supported by p.17 "At higher LR simulant contents, no measurable melt flow was detected".
- p.14 Figure 9 | probably assumed value | the neat-polymer porosity markers are plotted at 0 vol.% (dashed segments) | This is probably not a micro-CT measurement. Recorded with confidence low.
- p.14 3.5.2 / p.23 Supplementary Materials | data not in the PDF | "shown in Figure 11 and Tables S1 and S2" | Compression results with scatter (Tables S1/S2) and DMA curves (Figures S5/S6) are only in the supplement. No std or error bars are given anywhere in the main PDF, so std is empty for all S008 rows. 60, 85 (PEI) and other intermediate compression values had to be digitized.
- p.1 Abstract | only location | "compared with 93 MPa/2.3 GPa and 150 MPa/3.3 GPa for neat polymers" | The neat-polymer compressive moduli (2.3 and 3.3 GPa) appear only in the abstract. They agree with the Fig. 11b neat points (digitized 2.29 and 3.30).

## Data caveats (not contradictions, but relevant to use)

- p.5 Table 1 vs p.2 Introduction | simulant representativeness | VI-75 "SiO2 68.2", "CaO 14.43", "FeO 3.63" wt.% vs "SiO2 typically representing the most abundant component and accounting for approximately 40–50 wt.%" | The simulant (coal ash + metallurgical slag + quartz sand) is much richer in silica than the lunar regolith the paper itself describes. The paper calls it only "similar to LR in terms of its general chemical nature". The listed Table 1 components add up to 98.64 wt.%, and no remainder or LOI is given.
- p.10 Table 2 / p.5 | no d50 | The particle-size distribution is given only as sieve fractions (49.8 wt.% in 0.05–0.01 mm, 39.0 wt.% in 0.1–0.05 mm) for the unsieved powder (">0.1" = 0.3). The composites used the <100 µm sieved fraction. No d50 is stated, so d50_um is left empty.
- p.11 Table 4 | calculated, not measured | "Residual porosity formed during hot pressing was not included in this calculation." | The regolith_vol values are nominal values computed from the target wt.% (they check out: 2.56 g/cm3 particle density with 1.29/1.31 g/cm3 polymer density reproduces Table 4).
- p.17 3.8 | 0 = not measurable | MFI "0" in Table 6 and the zero markers in Fig. 14 mean "no measurable melt flow was detected under the test conditions", not a measured zero.
- p.9 2.5.8 | MFI sample form not stated | It is not said whether composite MFI was measured on powder blends or on pressed and crushed material.
- p.10 Table 3 vs p.16 3.7 | method difference | For neat PPSU, DSC Tg is 219.1 °C but DMA tanδ Tg is 210.4 °C, which is below the DSC value. For PEI, DMA tanδ (248.2) is above DSC (247.1). Different methods; both are recorded and labelled in the notes.

## Abstract / conclusions cross-check against tables, text and figures

Every number in the abstract and conclusions matches the body:
- Tg 219.1 / 247.1 °C = Table 3.
- Shore D 75→88 (PPSU) and 86→96 (PEI) = p.14 text and Fig. 10 (neat 75.0/86.0, max 88.0/96.0 digitized).
- Max σc/Ec 122 MPa/6.3 GPa (PPSU) and 193 MPa/7.4 GPa (PEI) = p.14/p.15 text and Fig. 11 (digitized 121.7 / 6.30 / 193.0 / 7.41).
- Neat 93 MPa/2.3 GPa and 150 MPa/3.3 GPa = Fig. 11 (digitized 93.0 / 2.29 / 150.0 / 3.30).
- λ 0.64 / 0.72 W/(m·K) = p.15 text, Table 6 and Fig. 12a.
- CLTE 14.2 / 10.1 × 10−6 K−1 = p.16 text, Table 6 and Fig. 12b (digitized 14.16 / 10.10).
- "<10 vol.% up to 60 wt.% PPSU / 85 wt.% PEI" = Fig. 9 (PPSU 60 wt.% about 9.4; PEI 85 wt.% about 9.1). See the threshold inconsistency above.
- Melt flow retained at 50–60 wt.% = p.17 and Fig. 14.
- Conclusions "PEI 70–90 wt.% ... compressive strength of ≥30 MPa" = Table 6 "30–146" and p.22 "30 MPa at ... 90 wt.%".

The only mismatch found is the "≥85 wt.%" binder-deficiency threshold in the conclusions versus the abstract (listed above).
