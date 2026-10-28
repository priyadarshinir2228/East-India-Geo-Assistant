## Task 4: graph measures

| Measure | Value |
|---|---|
| nodes | 100 |
| edges | 203 |
| connected components (undirected) | 1 |
| degree #1 | West Bengal Board of Secondary Education (BRD-WBBSE): 39 |
| degree #2 | Council for the Indian School Certificate Examinations (BRD-CISCE): 17 |
| degree #3 | Central Board of Secondary Education (BRD-CBSE): 12 |
| degree #4 | DEO/KOL/2026/018 (CIR-DEO-KOL-2026-018): 10 |
| degree #5 | Chowrasta (LOC-chowrasta): 9 |
| PageRank #1 | West Bengal Board of Secondary Education: 0.0851 |
| PageRank #2 | Council for the Indian School Certificate Examinations: 0.0347 |
| PageRank #3 | Central Board of Secondary Education: 0.0257 |
| PageRank #4 | Chowrasta: 0.0225 |
| PageRank #5 | DEO/KOL/2026/018: 0.0222 |
| edges of type affiliated_with | 36 |
| edges of type applies_to | 37 |
| edges of type located_in | 52 |
| edges of type mentions | 26 |
| edges of type near | 37 |
| edges of type states | 13 |
| edges of type supersedes | 2 |

**Traversal from Hare School (2 hops, max 25 nodes expanded per step)**

- hop 0, weight 1.00: Hare School via (start)
- hop 1, weight 1.00: West Bengal Board of Secondary Education via Hare School [affiliated_with] West Bengal Board of Secondary Education
- hop 1, weight 1.00: College Street via Hare School [located_in] College Street
- hop 1, weight 1.00: College Street via Hare School [near] College Street
- hop 1, weight 0.90: DEO/KOL/2026/018 via DEO/KOL/2026/018 [mentions] Hare School
- hop 1, weight 0.90: DEO/KOL/2025/031 via DEO/KOL/2025/031 [mentions] Hare School
- hop 2, weight 1.00: Tantia High School via Hare School [located_in] College Street -> Tantia High School [located_in] College Street
- hop 2, weight 1.00: Taki House, Govt Sponsored Multipurpose School for Boys via Hare School [located_in] College Street -> Taki House, Govt Sponsored Multipurpose School for Boys [located_in] College Street
- hop 2, weight 0.85: West Bengal Council of Higher Secondary Education via DEO/KOL/2025/031 [mentions] Hare School -> DEO/KOL/2025/031 [applies_to] West Bengal Council of Higher Secondary Education
- hop 2, weight 0.50: Barisha Sashibhusan Janakalyan Vidyapith via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Barisha Sashibhusan Janakalyan Vidyapith [affiliated_with] West Bengal Board of Secondary Education
- hop 2, weight 0.50: Rajarhat Shiksha Niketan High School for Boys via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Rajarhat Shiksha Niketan High School for Boys [affiliated_with] West Bengal Board of Secondary Education
- hop 2, weight 0.50: Nepali Girls High School via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Nepali Girls High School [affiliated_with] West Bengal Board of Secondary Education
- hop 2, weight 0.50: Chittaranjan Girls High School via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Chittaranjan Girls High School [affiliated_with] West Bengal Board of Secondary Education
- hop 2, weight 0.50: Panchsayar Siksha Niketan via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Panchsayar Siksha Niketan [affiliated_with] West Bengal Board of Secondary Education
- hop 2, weight 0.50: Turnbull Boys High School via Hare School [affiliated_with] West Bengal Board of Secondary Education -> Turnbull Boys High School [affiliated_with] West Bengal Board of Secondary Education

**Benefit: Which circulars apply to the board of Hare School?**

- relevant in hybrid top-10: 5 ['circ-kol-2025-031:0-602', 'circ-kol-2026-014:0-508', 'circ-kol-2026-018:0-684', 'note-sch-360501161:0-250', 'circ-kol-2026-007:0-466']
- relevant in graph-expanded top-10: 6 ['circ-kol-2025-031:0-602', 'circ-kol-2026-014:0-508', 'circ-kol-2026-018:0-684', 'note-sch-360501161:0-250', 'circ-kol-2026-007:0-466', 'circ-kol-2026-004:0-549']
- only found with the graph: ['circ-kol-2026-004:0-549']
- added by the graph but not relevant: ['dir-kolkata:1729-2410']

**Noise: What is the cut-off at Hare School?**

- relevant in hybrid top-10: 2 ['note-sch-360501161:0-250', 'circ-kol-2026-018:0-684']
- relevant in graph-expanded top-10: 2 ['circ-kol-2026-018:0-684', 'note-sch-360501161:0-250']
- only found with the graph: []
- added by the graph but not relevant: ['circ-djl-2026-002:0-439', 'circ-kol-2025-031:0-602', 'note-sch-284535702:0-238', 'note-sch-359503327:0-237', 'note-sch-517920587:0-267']

Noise control: path weight is the product of edge weights; paths through hubs (degree > 20, e.g. a board linked to dozens of schools) keep only 0.5 of their weight; paths under 0.3 are dropped; at most 25 nodes are expanded per hop; and the graph list enters RRF with weight 0.5, so it can lift but rarely outvote the text evidence.
