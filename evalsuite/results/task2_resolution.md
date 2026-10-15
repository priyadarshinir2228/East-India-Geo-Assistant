## Task 2: school linking threshold

| Threshold | Correct | Wrong link | No link (missed) | Accuracy |
|---|---|---|---|---|
| 70 | 59 | 4 | 1 | 0.92 |
| 75 | 59 | 4 | 1 | 0.92 |
| 80 | 60 | 3 | 1 | 0.94 |
| 85 | 61 | 1 | 2 | 0.95 |
| 88 | 61 | 1 | 2 | 0.95 |
| 90 | 61 | 1 | 2 | 0.95 |
| 95 | 60 | 1 | 3 | 0.94 |

**Fix: initials rule (before / after)**

| Initials rule | 'K.K. Hindu Academy' links to | Score |
|---|---|---|
| off | not linked | 66.7 |
| on | Dum Dum Krishna Kumar Hindu Academy | 95.0 |

64 name variants (2 of them should stay unlinked). Best threshold here: 85.

**Merged variants (same GeoServer school)**

- Loretto Convent: Loreto Convent, Loretto Convent
- St. Pauls School: St. Paul's School, St. Pauls School
- Mount Hermon School: Mount Hermon School, Mt. Hermon School
- Maharani Girls' High School: Maharani Girls High School, Maharani Girls' High School
- Baranagar Ramakrishna Mission Ashrama High School: Baranagar RKM High School, Baranagar Ramakrishna Mission Ashrama High School
- BE College Model School: B.E. College Model School, BE College Model School
- Dinabandhu Institution Main: Dinabandhu Institution, Dinabandhu Institution Main
- Delhi Public School: DPS Rajarhat, Delhi Public School
- Saint Xavier's Collegiate School: SXCS, Saint Xavier's Collegiate School, St Xaviers Collegiate, St. Xavier's Collegiate School (Primary Section)
- Dum Dum Krishna Kumar Hindu Academy: Dum Dum Krishna Kumar Hindu Academy, K.K. Hindu Academy
- Dum Dum Subhas Nagar High School: Dum Dum Subhas Nagar High School, Subhas Nagar High School
- Auxilium Convent School: Auxilium Convent, Auxilium Convent School
- middle school(Dariyapur): Middle School, middle school(Dariyapur)
- New Barrackpore Colony Boys' High School (H.S.): New Barrackpore Colony Boys' High School, New Barrackpore Colony Boys' High School (H.S.)
- ST Xaviers School: ST Xaviers School, Saint Xavier's School
- Saraswati Vidya Mandir (boys), puraniganj,Munger: Saraswati Vidya Mandir (boys), puraniganj,Munger, Saraswati Vidya Mandir(girls), puraniganj,Munger
- St. Paul's School: St. Paul's School, St. Pauls School
- PVSS DAV Public School: PVSS DAV PUBLIC School, PVSS DAV Public School
- Dakshin Gangadharpur F. P. School: Dakshin Gangadharpur F. P. School, P. School
- HVI(Boro Bari): HVI (Auditorium), HVI(Boro Bari), HVI(Choto Bari)
- Primary School: Primary School, primary school(private)
- Darbhanga Public School: Darbhanga Public School, Public School Darbhanga
- Rehoboth Mission School: Rehoboth Mission School, Rehoboth Mission school

**Schools that could not be linked to GeoServer**

- C.R. Boys High School
- Sunrise Public School
