"""Synthetic facts for the PoC (disclosed as synthetic in the PROJECT DOCUMENT).

School names, osm_ids and locations are real OpenStreetMap features from schools.gpkg.
Boards, seats, cut-off marks, circulars, rules, localities' centres and road geometries
are invented for the assessment.
"""

BOARDS = {
    "BRD-WBBSE": dict(name="West Bengal Board of Secondary Education", short="WBBSE",
                      aliases=["West Bengal Board", "Madhyamik board"]),
    "BRD-WBCHSE": dict(name="West Bengal Council of Higher Secondary Education", short="WBCHSE",
                       aliases=["Higher Secondary Council"]),
    "BRD-CBSE": dict(name="Central Board of Secondary Education", short="CBSE", aliases=["Central Board"]),
    "BRD-CISCE": dict(name="Council for the Indian School Certificate Examinations", short="CISCE",
                      aliases=["ICSE board"]),
}

# id: (name, lon, lat, town)
LOCALITIES = {
    "LOC-shibpur": ("Shibpur", 88.312, 22.560, "Kolkata"),
    "LOC-college-street": ("College Street", 88.364, 22.578, "Kolkata"),
    "LOC-park-street": ("Park Street", 88.362, 22.548, "Kolkata"),
    "LOC-ballygunge": ("Ballygunge", 88.368, 22.518, "Kolkata"),
    "LOC-behala": ("Behala", 88.318, 22.488, "Kolkata"),
    "LOC-garia": ("Garia", 88.392, 22.468, "Kolkata"),
    "LOC-dum-dum": ("Dum Dum", 88.418, 22.640, "Kolkata"),
    "LOC-baranagar": ("Baranagar", 88.378, 22.628, "Kolkata"),
    "LOC-rajarhat": ("Rajarhat", 88.482, 22.612, "Kolkata"),
    "LOC-new-barrackpore": ("New Barrackpore", 88.448, 22.690, "Kolkata"),
    "LOC-chowrasta": ("Chowrasta", 88.263, 27.039, "Darjeeling"),
    "LOC-north-point": ("North Point", 88.252, 27.063, "Darjeeling"),
}

# id: (name, aliases, [(lon, lat), ...]) -- schematic alignments, not surveyed geometry
ROADS = {
    "RD-jessore-road": ("Jessore Road", ["Jessore Rd"], [(88.4090, 22.6200), (88.4150, 22.6330), (88.4240, 22.6420), (88.4330, 22.6560)]),
    "RD-bt-road": ("B.T. Road", ["Barrackpore Trunk Road", "BT Road"], [(88.3700, 22.6020), (88.3740, 22.6200), (88.3735, 22.6400)]),
    "RD-college-street": ("College Street", ["College St"], [(88.3625, 22.5700), (88.3640, 22.5780), (88.3665, 22.5880)]),
    "RD-park-street": ("Park Street", ["Mother Teresa Sarani"], [(88.3480, 22.5530), (88.3580, 22.5500), (88.3680, 22.5470), (88.3760, 22.5440)]),
    "RD-rashbehari-avenue": ("Rashbehari Avenue", ["Rash Behari Avenue"], [(88.3450, 22.5160), (88.3600, 22.5175), (88.3790, 22.5180)]),
    "RD-diamond-harbour-road": ("Diamond Harbour Road", ["DH Road"], [(88.3240, 22.5050), (88.3170, 22.4900), (88.3110, 22.4750)]),
    "RD-andul-road": ("Andul Road", [], [(88.2950, 22.5560), (88.3080, 22.5600), (88.3200, 22.5640)]),
    "RD-vip-road": ("VIP Road", ["Biju Patnaik Road"], [(88.4400, 22.6300), (88.4650, 22.6250), (88.4900, 22.6260)]),
    "RD-hill-cart-road": ("Hill Cart Road", ["Tenzing Norgay Road"], [(88.2590, 27.0300), (88.2620, 27.0360), (88.2640, 27.0410)]),
    "RD-lebong-cart-road": ("Lebong Cart Road", [], [(88.2560, 27.0580), (88.2525, 27.0630), (88.2500, 27.0680)]),
}

# Schools: id -> dict. osm_ids are the building features in the GeoServer layer.
# board / seats / cutoff / min_age are synthetic.
S = dict
SCHOOLS = {
    "SCH-360501161": S(name="Hare School", osm=["360501161"], loc="LOC-college-street", board="BRD-WBBSE", seats=120, cutoff=85, aliases=["Hare School Kolkata"]),
    "SCH-1436404186": S(name="Bethune Collegiate School", osm=["1436404186"], loc="LOC-college-street", board="BRD-WBBSE", seats=100, cutoff=82, aliases=["Bethune School"]),
    "SCH-637073212": S(name="St. Xavier's Collegiate School", osm=["637073212", "358873090"], loc="LOC-park-street", board="BRD-CISCE", seats=150, cutoff=90, aliases=["Saint Xavier's Collegiate School", "St Xaviers Collegiate", "SXCS"]),
    "SCH-359096852": S(name="Albany Hall School", osm=["359096852"], loc="LOC-park-street", board="BRD-CBSE", seats=60, cutoff=70, aliases=["Albany Hall"]),
    "SCH-359684982": S(name="Don Bosco School", osm=["359684982"], loc="LOC-park-street", board="BRD-CISCE", seats=140, cutoff=88, aliases=["Don Bosco Park Circus"]),
    "SCH-359039082": S(name="Holy Cross School", osm=["359039082"], loc="LOC-park-street", board="BRD-CISCE", seats=80, cutoff=75, aliases=[]),
    "SCH-359329404": S(name="Chittaranjan Boys High School", osm=["359329404"], loc="LOC-ballygunge", board="BRD-WBBSE", seats=110, cutoff=65, aliases=["C.R. Boys High School"]),
    "SCH-359329018": S(name="Chittaranjan Girls High School", osm=["359329018"], loc="LOC-ballygunge", board="BRD-WBBSE", seats=100, cutoff=66, aliases=[]),
    "SCH-360006273": S(name="Kamala Chatterjee Girls School", osm=["360006273"], loc="LOC-ballygunge", board="BRD-WBBSE", seats=90, cutoff=72, aliases=["Kamala Chatterjee School"]),
    "SCH-1469812433": S(name="Nava Nalanda Group of Schools", osm=["1469812433"], loc="LOC-ballygunge", board="BRD-CBSE", seats=130, cutoff=80, aliases=["Nava Nalanda"]),
    "SCH-359503327": S(name="Barisha Sashibhusan Janakalyan Vidyapith", osm=["359503327"], loc="LOC-behala", board="BRD-WBBSE", seats=160, cutoff=55, aliases=["Barisha Janakalyan Vidyapith"]),
    "SCH-359529812": S(name="Shri Ritam Vidyapith", osm=["359529812"], loc="LOC-behala", board="BRD-CBSE", seats=70, cutoff=68, aliases=["Sri Ritam Vidyapith"]),
    "SCH-517920587": S(name="BE College Model School", osm=["517920587"], loc="LOC-shibpur", board="BRD-WBBSE", seats=120, cutoff=78, aliases=["B.E. College Model School"]),
    "SCH-636399655": S(name="Vivekananda School", osm=["636399655"], loc="LOC-shibpur", board="BRD-CBSE", seats=80, cutoff=60, aliases=[]),
    "SCH-384851268": S(name="Dinabandhu Institution", osm=["384851268"], loc="LOC-shibpur", board="BRD-WBBSE", seats=140, cutoff=58, aliases=["Dinabandhu Institution Main"]),
    "SCH-1035913079": S(name="Dum Dum Krishna Kumar Hindu Academy", osm=["1035913079"], loc="LOC-dum-dum", board="BRD-WBBSE", seats=150, cutoff=62, aliases=["K.K. Hindu Academy"]),
    "SCH-358339970": S(name="Dum Dum Subhas Nagar High School", osm=["358339970"], loc="LOC-dum-dum", board="BRD-WBBSE", seats=100, cutoff=50, aliases=["Subhas Nagar High School"]),
    "SCH-358021840": S(name="Saroj Basu Smriti Balika Vidyamandir", osm=["358021840"], loc="LOC-dum-dum", board="BRD-WBBSE", seats=90, cutoff=52, aliases=[]),
    "SCH-1035930697": S(name="Auxilium Convent School", osm=["1035930697"], loc="LOC-dum-dum", board="BRD-CISCE", seats=70, cutoff=74, aliases=["Auxilium Convent"]),
    "SCH-284535702": S(name="Baranagar Ramakrishna Mission Ashrama High School", osm=["284535702"], loc="LOC-baranagar", board="BRD-WBBSE", seats=160, cutoff=80, aliases=["Baranagar RKM High School"]),
    "SCH-301561695": S(name="Janata Hindi School", osm=["301561695"], loc="LOC-baranagar", board="BRD-WBBSE", seats=80, cutoff=45, aliases=[]),
    "SCH-360666537": S(name="Birati High School", osm=["360666537", "1147811143"], loc="LOC-dum-dum", board="BRD-WBBSE", seats=120, cutoff=48, aliases=[]),
    "SCH-5341865": S(name="Delhi Public School", osm=["5341865"], loc="LOC-rajarhat", board="BRD-CBSE", seats=200, cutoff=85, aliases=["DPS Rajarhat"]),
    "SCH-358071877": S(name="Rajarhat Shiksha Niketan High School for Boys", osm=["358071877"], loc="LOC-rajarhat", board="BRD-WBBSE", seats=130, cutoff=50, aliases=["Rajarhat Shiksha Niketan"]),
    "SCH-1095713427": S(name="New Barrackpore Colony Boys' High School", osm=["1095713427"], loc="LOC-new-barrackpore", board="BRD-WBCHSE", seats=100, cutoff=60, aliases=["New Barrackpore Colony Boys High School"]),
    "SCH-5341672": S(name="Nafar Chandra Balika Vidyalaya", osm=["5341672"], loc="LOC-garia", board="BRD-WBBSE", seats=80, cutoff=47, aliases=[]),
    "SCH-789229285": S(name="Panchsayar Siksha Niketan", osm=["789229285"], loc="LOC-garia", board="BRD-WBBSE", seats=100, cutoff=52, aliases=[]),
    "SCH-348961773": S(name="Government Boys High School", osm=["348961773", "348962311"], loc="LOC-chowrasta", board="BRD-WBBSE", seats=90, cutoff=55, aliases=["Govt. Boys High School Darjeeling"]),
    "SCH-350304682": S(name="Maharani Girls' High School", osm=["350304682", "350304683", "350304684"], loc="LOC-chowrasta", board="BRD-WBBSE", seats=100, cutoff=58, aliases=["Maharani Girls High School"]),
    "SCH-348890269": S(name="Loretto Convent", osm=["348890269"], loc="LOC-chowrasta", board="BRD-CISCE", seats=80, cutoff=76, aliases=["Loreto Convent Darjeeling"]),
    "SCH-348917732": S(name="Mount Hermon School", osm=["348917732"], loc="LOC-north-point", board="BRD-CISCE", seats=70, cutoff=72, aliases=["Mt. Hermon School"]),
    "SCH-348915893": S(name="St. Michael's School", osm=["348915893"], loc="LOC-north-point", board="BRD-CISCE", seats=90, cutoff=70, aliases=["St Michaels School"]),
    "SCH-348884264": S(name="St. Paul's School", osm=["348884264", "348884497"], loc="LOC-chowrasta", board="BRD-CISCE", seats=60, cutoff=82, aliases=["St. Pauls School"]),
    "SCH-350289302": S(name="Turnbull Boys High School", osm=["350289302"], loc="LOC-chowrasta", board="BRD-WBBSE", seats=80, cutoff=45, aliases=[]),
    "SCH-350293526": S(name="Nepali Girls High School", osm=["350293526", "348924155"], loc="LOC-chowrasta", board="BRD-WBBSE", seats=90, cutoff=50, aliases=[]),
}

# Schools named in documents that do NOT exist in the GeoServer layer (expected unlinked).
UNLINKED_SCHOOLS = {
    "SCH-X-sunrise": S(name="Sunrise Public School", loc="LOC-behala", board="BRD-CBSE"),
    "SCH-X-kv-saltlake": S(name="Kendriya Vidyalaya Salt Lake", loc=None, board="BRD-CBSE"),
}

CIRCULARS = {
    "CIR-DEO-KOL-2025-031": dict(no="DEO/KOL/2025/031", date="2025-11-10", subject="Class XI admission schedule 2026"),
    "CIR-DEO-KOL-2026-004": dict(no="DEO/KOL/2026/004", date="2026-01-15", subject="Class I admission age limits"),
    "CIR-DEO-KOL-2026-007": dict(no="DEO/KOL/2026/007", date="2026-01-28", subject="Documents required for admission"),
    "CIR-DEO-KOL-2026-012": dict(no="DEO/KOL/2026/012", date="2026-02-20", subject="Lottery and EWS reservation in CBSE and CISCE schools"),
    "CIR-DEO-KOL-2026-014": dict(no="DEO/KOL/2026/014", date="2026-03-05", subject="Revised Class XI admission schedule 2026"),
    "CIR-DEO-KOL-2026-018": dict(no="DEO/KOL/2026/018", date="2026-04-02", subject="Class XI science cut-off marks"),
    "CIR-DEO-KOL-2026-021": dict(no="DEO/KOL/2026/021", date="2026-04-20", subject="Jessore Road closure and school transport"),
    "CIR-DEO-DJL-2026-002": dict(no="DEO/DJL/2026/002", date="2026-01-25", subject="Hill schools admission dates"),
    "CIR-DEO-DJL-2026-005": dict(no="DEO/DJL/2026/005", date="2026-03-12", subject="Revised hill schools admission dates"),
}
