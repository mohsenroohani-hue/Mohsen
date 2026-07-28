"""
geo.py
======
Geographical resolution for the review.

Two *distinct* geographies are resolved and never conflated:

  (a) AFFILIATION GEOGRAPHY  - where knowledge is produced.
      Parsed from the Scopus `Affiliations` field. Scopus writes each
      affiliation as "<unit>, <institution>, <city>, <postcode>, <country>",
      with multiple affiliations separated by ";". The country is therefore
      the terminal comma-delimited token of each ";"-chunk.

  (b) CASE-STUDY GEOGRAPHY   - where the empirical problem is located.
      Detected from Title + Abstract using a gazetteer of country names,
      adjectival/demonymic forms, and ~300 major cities and administrative
      regions, with explicit disambiguation of polysemous toponyms.

The gap between (a) and (b) is the empirical basis for the "knowledge-
production asymmetry" analysis in the manuscript.
"""

import re
import unicodedata

import pycountry

# ---------------------------------------------------------------------------
# Canonical country handling
# ---------------------------------------------------------------------------

# Scopus / author spellings -> ISO alpha-3
COUNTRY_ALIASES = {
    "usa": "USA", "u.s.a.": "USA", "u.s.": "USA", "us": "USA",
    "united states": "USA", "united states of america": "USA",
    "uk": "GBR", "u.k.": "GBR", "united kingdom": "GBR",
    "england": "GBR", "scotland": "GBR", "wales": "GBR",
    "northern ireland": "GBR", "great britain": "GBR",
    "russian federation": "RUS", "russia": "RUS",
    "south korea": "KOR", "korea": "KOR", "republic of korea": "KOR",
    "korea, republic of": "KOR", "south-korea": "KOR",
    "north korea": "PRK", "democratic people's republic of korea": "PRK",
    "iran": "IRN", "islamic republic of iran": "IRN", "iran, islamic republic of": "IRN",
    "vietnam": "VNM", "viet nam": "VNM",
    "taiwan": "TWN", "chinese taipei": "TWN",
    "hong kong": "HKG", "hong kong sar": "HKG", "hong-kong": "HKG",
    "macao": "MAC", "macau": "MAC",
    "czech republic": "CZE", "czechia": "CZE",
    "slovak republic": "SVK", "slovakia": "SVK",
    "turkey": "TUR", "türkiye": "TUR", "turkiye": "TUR",
    "china": "CHN", "peoples republic of china": "CHN",
    "people's republic of china": "CHN", "pr china": "CHN", "p.r. china": "CHN",
    "netherlands": "NLD", "the netherlands": "NLD", "holland": "NLD",
    "bolivia": "BOL", "venezuela": "VEN", "tanzania": "TZA",
    "united republic of tanzania": "TZA",
    "syria": "SYR", "syrian arab republic": "SYR",
    "laos": "LAO", "lao pdr": "LAO", "lao people's democratic republic": "LAO",
    "moldova": "MDA", "republic of moldova": "MDA",
    "macedonia": "MKD", "north macedonia": "MKD",
    "ivory coast": "CIV", "cote d'ivoire": "CIV", "côte d'ivoire": "CIV",
    "cape verde": "CPV", "cabo verde": "CPV",
    "democratic republic of the congo": "COD", "dr congo": "COD",
    "drc": "COD", "congo, democratic republic": "COD", "zaire": "COD",
    "republic of the congo": "COG", "congo": "COG", "congo-brazzaville": "COG",
    "brunei": "BRN", "brunei darussalam": "BRN",
    "myanmar": "MMR", "burma": "MMR",
    "east timor": "TLS", "timor-leste": "TLS",
    "swaziland": "SWZ", "eswatini": "SWZ",
    "palestine": "PSE", "palestinian territory": "PSE",
    "state of palestine": "PSE", "west bank": "PSE", "gaza": "PSE",
    "gaza strip": "PSE",
    "bosnia": "BIH", "bosnia and herzegovina": "BIH",
    "united arab emirates": "ARE", "uae": "ARE",
    "saudi arabia": "SAU", "ksa": "SAU",
    "new zealand": "NZL", "papua new guinea": "PNG",
    "south africa": "ZAF", "sri lanka": "LKA",
    "costa rica": "CRI", "puerto rico": "PRI",
    "dominican republic": "DOM", "el salvador": "SLV",
    "trinidad and tobago": "TTO", "burkina faso": "BFA",
    "sierra leone": "SLE", "south sudan": "SSD",
    "equatorial guinea": "GNQ", "guinea-bissau": "GNB", "guinea bissau": "GNB",
    "central african republic": "CAF",
    "antigua and barbuda": "ATG", "saint lucia": "LCA",
    "reunion": "REU", "réunion": "REU", "french guiana": "GUF",
    "guadeloupe": "GLP", "martinique": "MTQ", "new caledonia": "NCL",
    "french polynesia": "PYF", "greenland": "GRL", "faroe islands": "FRO",
    "kosovo": "XKX", "serbia": "SRB", "montenegro": "MNE",
    "libyan arab jamahiriya": "LBY", "libya": "LBY",
    "cyprus": "CYP", "malta": "MLT", "iceland": "ISL",
    "luxembourg": "LUX", "monaco": "MCO", "liechtenstein": "LIE",
    "andorra": "AND", "san marino": "SMR", "vatican city": "VAT",
    "bahamas": "BHS", "the bahamas": "BHS", "gambia": "GMB",
    "the gambia": "GMB", "philippines": "PHL", "the philippines": "PHL",
    "maldives": "MDV", "seychelles": "SYC", "mauritius": "MUS",
    "fiji": "FJI", "samoa": "WSM", "tonga": "TON", "vanuatu": "VUT",
    "solomon islands": "SLB", "micronesia": "FSM", "kiribati": "KIR",
    "marshall islands": "MHL", "palau": "PLW", "nauru": "NRU", "tuvalu": "TUV",
}


def _norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _build_name_index():
    idx = {}
    for c in pycountry.countries:
        a3 = c.alpha_3
        for attr in ("name", "official_name", "common_name"):
            v = getattr(c, attr, None)
            if v:
                idx[_norm(v)] = a3
                # strip parenthetical/comma qualifiers: "Bolivia, Plurinational State of"
                idx[_norm(v.split(",")[0])] = a3
    idx.update({_norm(k): v for k, v in COUNTRY_ALIASES.items()})
    return idx


NAME_TO_ISO3 = _build_name_index()

ISO3_TO_NAME = {}
for _c in pycountry.countries:
    ISO3_TO_NAME[_c.alpha_3] = getattr(_c, "common_name", None) or _c.name.split(",")[0]
ISO3_TO_NAME.update({
    "USA": "United States", "GBR": "United Kingdom", "KOR": "South Korea",
    "PRK": "North Korea", "IRN": "Iran", "RUS": "Russia", "VNM": "Vietnam",
    "TWN": "Taiwan", "HKG": "Hong Kong SAR", "MAC": "Macao SAR",
    "CZE": "Czechia", "TUR": "Türkiye", "SYR": "Syria", "LAO": "Laos",
    "MDA": "Moldova", "MKD": "North Macedonia", "CIV": "Côte d'Ivoire",
    "COD": "DR Congo", "COG": "Congo (Rep.)", "TZA": "Tanzania",
    "BOL": "Bolivia", "VEN": "Venezuela", "PSE": "Palestine",
    "BIH": "Bosnia & Herzegovina", "XKX": "Kosovo", "SWZ": "Eswatini",
    "TLS": "Timor-Leste", "MMR": "Myanmar", "BRN": "Brunei",
    "NLD": "Netherlands", "ARE": "United Arab Emirates",
})

# ---------------------------------------------------------------------------
# Demonyms / adjectival forms used in titles and abstracts
# ---------------------------------------------------------------------------
DEMONYMS = {
    "chinese": "CHN", "american": "USA", "u.s.": "USA", "british": "GBR",
    "german": "DEU", "french": "FRA", "italian": "ITA", "spanish": "ESP",
    "portuguese": "PRT", "dutch": "NLD", "belgian": "BEL", "swiss": "CHE",
    "austrian": "AUT", "swedish": "SWE", "norwegian": "NOR", "danish": "DNK",
    "finnish": "FIN", "polish": "POL", "czech": "CZE", "hungarian": "HUN",
    "romanian": "ROU", "bulgarian": "BGR", "greek": "GRC", "turkish": "TUR",
    "russian": "RUS", "ukrainian": "UKR", "japanese": "JPN", "korean": "KOR",
    "indian": "IND", "pakistani": "PAK", "bangladeshi": "BGD",
    "iranian": "IRN", "iraqi": "IRQ", "israeli": "ISR", "saudi": "SAU",
    "egyptian": "EGY", "nigerian": "NGA", "kenyan": "KEN", "ghanaian": "GHA",
    "ethiopian": "ETH", "tanzanian": "TZA", "ugandan": "UGA",
    "moroccan": "MAR", "tunisian": "TUN", "algerian": "DZA",
    "brazilian": "BRA", "argentine": "ARG", "argentinian": "ARG",
    "chilean": "CHL", "colombian": "COL", "peruvian": "PER",
    "mexican": "MEX", "canadian": "CAN", "australian": "AUS",
    "indonesian": "IDN", "malaysian": "MYS", "thai": "THA",
    "vietnamese": "VNM", "filipino": "PHL", "philippine": "PHL",
    "nepalese": "NPL", "nepali": "NPL", "sri lankan": "LKA",
    "taiwanese": "TWN", "singaporean": "SGP", "new zealand": "NZL",
    "irish": "IRL", "scottish": "GBR", "welsh": "GBR", "english": None,
    "croatian": "HRV", "serbian": "SRB", "slovenian": "SVN",
    "slovak": "SVK", "lithuanian": "LTU", "latvian": "LVA",
    "estonian": "EST", "icelandic": "ISL", "cypriot": "CYP",
    "kazakh": "KAZ", "uzbek": "UZB", "mongolian": "MNG",
    "south african": "ZAF", "zimbabwean": "ZWE", "zambian": "ZMB",
    "botswanan": "BWA", "namibian": "NAM", "malawian": "MWI",
    "mozambican": "MOZ", "rwandan": "RWA", "senegalese": "SEN",
    "ivorian": "CIV", "cameroonian": "CMR", "sudanese": "SDN",
    "jordanian": "JOR", "lebanese": "LBN", "syrian": "SYR",
    "omani": "OMN", "qatari": "QAT", "kuwaiti": "KWT", "emirati": "ARE",
    "yemeni": "YEM", "afghan": "AFG", "cuban": "CUB", "jamaican": "JAM",
    "haitian": "HTI", "bolivian": "BOL", "ecuadorian": "ECU",
    "uruguayan": "URY", "paraguayan": "PRY", "venezuelan": "VEN",
    "costa rican": "CRI", "panamanian": "PAN", "guatemalan": "GTM",
    "honduran": "HND", "nicaraguan": "NIC", "salvadoran": "SLV",
}

# ---------------------------------------------------------------------------
# Major-city and sub-national gazetteer (case-study detection)
# ---------------------------------------------------------------------------
CITY_TO_ISO3 = {
    # China
    "beijing": "CHN", "shanghai": "CHN", "guangzhou": "CHN", "shenzhen": "CHN",
    "wuhan": "CHN", "chengdu": "CHN", "hangzhou": "CHN", "nanjing": "CHN",
    "xi'an": "CHN", "xian city": "CHN", "tianjin": "CHN", "chongqing": "CHN",
    "shenyang": "CHN", "harbin": "CHN", "qingdao": "CHN", "dalian": "CHN",
    "suzhou": "CHN", "zhengzhou": "CHN", "changsha": "CHN", "kunming": "CHN",
    "xiamen": "CHN", "ningbo": "CHN", "jinan": "CHN", "hefei": "CHN",
    "nanchang": "CHN", "fuzhou": "CHN", "guiyang": "CHN", "lanzhou": "CHN",
    "urumqi": "CHN", "lhasa": "CHN", "yangtze": "CHN", "pearl river delta": "CHN",
    "yellow river": "CHN", "loess plateau": "CHN", "tibetan plateau": "CHN",
    "inner mongolia": "CHN", "xinjiang": "CHN", "guangdong": "CHN",
    "zhejiang": "CHN", "jiangsu": "CHN", "shandong": "CHN", "sichuan": "CHN",
    "yunnan": "CHN", "hubei": "CHN", "hunan": "CHN", "fujian": "CHN",
    "heilongjiang": "CHN", "shaanxi": "CHN", "gansu": "CHN", "anhui": "CHN",
    "jiangxi": "CHN", "guangxi": "CHN", "hainan": "CHN", "qinghai": "CHN",
    "ningxia": "CHN", "shanxi": "CHN", "hebei": "CHN", "jilin": "CHN",
    "liaoning": "CHN", "henan": "CHN", "guizhou": "CHN",
    # USA
    "new york city": "USA", "new york state": "USA", "los angeles": "USA",
    "chicago": "USA", "houston": "USA", "philadelphia": "USA",
    "phoenix": "USA", "san antonio": "USA", "san diego": "USA",
    "dallas": "USA", "san francisco": "USA", "seattle": "USA",
    "boston": "USA", "detroit": "USA", "atlanta": "USA", "miami": "USA",
    "baltimore": "USA", "denver": "USA", "portland, oregon": "USA",
    "washington, dc": "USA", "washington d.c.": "USA", "new orleans": "USA",
    "minneapolis": "USA", "cleveland": "USA", "pittsburgh": "USA",
    "st. louis": "USA", "cincinnati": "USA", "milwaukee": "USA",
    "california": "USA", "texas": "USA", "florida": "USA", "illinois": "USA",
    "pennsylvania": "USA", "ohio": "USA", "michigan": "USA",
    "north carolina": "USA", "south carolina": "USA", "virginia": "USA",
    "massachusetts": "USA", "arizona": "USA", "colorado": "USA",
    "wisconsin": "USA", "minnesota": "USA", "missouri": "USA",
    "louisiana": "USA", "alabama": "USA", "kentucky": "USA",
    "oregon": "USA", "oklahoma": "USA", "connecticut": "USA",
    "iowa": "USA", "arkansas": "USA", "kansas": "USA", "utah": "USA",
    "nevada": "USA", "new mexico": "USA", "nebraska": "USA",
    "west virginia": "USA", "idaho": "USA", "montana": "USA",
    "wyoming": "USA", "alaska": "USA", "hawaii": "USA", "maine": "USA",
    "new hampshire": "USA", "vermont": "USA", "rhode island": "USA",
    "delaware": "USA", "new jersey": "USA", "maryland": "USA",
    "tennessee": "USA", "indiana": "USA", "mississippi": "USA",
    "north dakota": "USA", "south dakota": "USA",
    "great lakes": "USA", "gulf of mexico": "USA", "appalachian": "USA",
    # Europe
    "london": "GBR", "manchester": "GBR", "birmingham, uk": "GBR",
    "glasgow": "GBR", "edinburgh": "GBR", "liverpool": "GBR",
    "leeds": "GBR", "bristol": "GBR", "sheffield": "GBR", "cardiff": "GBR",
    "belfast": "GBR", "newcastle upon tyne": "GBR",
    "paris": "FRA", "lyon": "FRA", "marseille": "FRA", "toulouse": "FRA",
    "bordeaux": "FRA", "lille": "FRA", "nantes": "FRA", "strasbourg": "FRA",
    "berlin": "DEU", "munich": "DEU", "hamburg": "DEU", "cologne": "DEU",
    "frankfurt": "DEU", "stuttgart": "DEU", "dresden": "DEU",
    "leipzig": "DEU", "dortmund": "DEU", "ruhr": "DEU", "bavaria": "DEU",
    "madrid": "ESP", "barcelona": "ESP", "valencia": "ESP", "seville": "ESP",
    "zaragoza": "ESP", "bilbao": "ESP", "catalonia": "ESP", "andalusia": "ESP",
    "rome": "ITA", "milan": "ITA", "naples": "ITA", "turin": "ITA",
    "florence": "ITA", "bologna": "ITA", "venice": "ITA", "palermo": "ITA",
    "sicily": "ITA", "tuscany": "ITA", "lombardy": "ITA", "sardinia": "ITA",
    "lisbon": "PRT", "porto": "PRT", "amsterdam": "NLD", "rotterdam": "NLD",
    "utrecht": "NLD", "the hague": "NLD", "brussels": "BEL",
    "antwerp": "BEL", "ghent": "BEL", "flanders": "BEL",
    "vienna": "AUT", "zurich": "CHE", "geneva": "CHE", "basel": "CHE",
    "stockholm": "SWE", "gothenburg": "SWE", "oslo": "NOR", "bergen": "NOR",
    "copenhagen": "DNK", "aarhus": "DNK", "helsinki": "FIN",
    "warsaw": "POL", "krakow": "POL", "wroclaw": "POL", "poznan": "POL",
    "prague": "CZE", "brno": "CZE", "budapest": "HUN", "bucharest": "ROU",
    "sofia": "BGR", "athens": "GRC", "thessaloniki": "GRC",
    "istanbul": "TUR", "ankara": "TUR", "izmir": "TUR", "antalya": "TUR",
    "moscow": "RUS", "saint petersburg": "RUS", "siberia": "RUS",
    "kyiv": "UKR", "kiev": "UKR", "dublin": "IRL", "zagreb": "HRV",
    "belgrade": "SRB", "ljubljana": "SVN", "bratislava": "SVK",
    "vilnius": "LTU", "riga": "LVA", "tallinn": "EST", "reykjavik": "ISL",
    "mediterranean basin": None, "alps": None, "scandinavia": None,
    # Asia-Pacific
    "tokyo": "JPN", "osaka": "JPN", "kyoto": "JPN", "yokohama": "JPN",
    "nagoya": "JPN", "sapporo": "JPN", "fukuoka": "JPN", "hiroshima": "JPN",
    "sendai": "JPN", "kobe": "JPN", "okayama": "JPN", "hokkaido": "JPN",
    "seoul": "KOR", "busan": "KOR", "incheon": "KOR", "daegu": "KOR",
    "gwangju": "KOR", "daejeon": "KOR",
    "taipei": "TWN", "kaohsiung": "TWN", "taichung": "TWN", "tainan": "TWN",
    "delhi": "IND", "new delhi": "IND", "mumbai": "IND", "bangalore": "IND",
    "bengaluru": "IND", "chennai": "IND", "kolkata": "IND",
    "hyderabad, india": "IND", "pune": "IND", "ahmedabad": "IND",
    "jaipur": "IND", "lucknow": "IND", "kerala": "IND", "tamil nadu": "IND",
    "maharashtra": "IND", "karnataka": "IND", "west bengal": "IND",
    "uttar pradesh": "IND", "gujarat": "IND", "rajasthan": "IND",
    "punjab, india": "IND", "odisha": "IND", "assam": "IND", "bihar": "IND",
    "ganges": "IND", "himalaya": None,
    "karachi": "PAK", "lahore": "PAK", "islamabad": "PAK",
    "dhaka": "BGD", "chittagong": "BGD",
    "kathmandu": "NPL", "colombo": "LKA",
    "jakarta": "IDN", "surabaya": "IDN", "bandung": "IDN", "medan": "IDN",
    "java": "IDN", "sumatra": "IDN", "borneo": None, "kalimantan": "IDN",
    "sulawesi": "IDN", "bali": "IDN", "yogyakarta": "IDN", "malang": "IDN",
    "kuala lumpur": "MYS", "penang": "MYS", "johor": "MYS",
    "selangor": "MYS", "sabah": "MYS", "sarawak": "MYS",
    "bangkok": "THA", "chiang mai": "THA", "phuket": "THA",
    "hanoi": "VNM", "ho chi minh city": "VNM", "mekong delta": "VNM",
    "manila": "PHL", "metro manila": "PHL", "cebu": "PHL",
    "singapore": "SGP", "phnom penh": "KHM", "vientiane": "LAO",
    "yangon": "MMR", "ulaanbaatar": "MNG",
    "sydney": "AUS", "melbourne": "AUS", "brisbane": "AUS", "perth": "AUS",
    "adelaide": "AUS", "canberra": "AUS", "queensland": "AUS",
    "new south wales": "AUS", "victoria, australia": "AUS",
    "western australia": "AUS", "tasmania": "AUS", "great barrier reef": "AUS",
    "auckland": "NZL", "wellington": "NZL", "christchurch": "NZL",
    # Middle East / Central Asia
    "tehran": "IRN", "mashhad": "IRN", "isfahan": "IRN", "esfahan": "IRN",
    "shiraz": "IRN", "tabriz": "IRN", "ahvaz": "IRN", "karaj": "IRN",
    "qom": "IRN", "kermanshah": "IRN", "urmia": "IRN", "yazd": "IRN",
    "zagros": "IRN", "alborz": "IRN", "caspian sea": None,
    "baghdad": "IRQ", "basra": "IRQ", "erbil": "IRQ", "mosul": "IRQ",
    "riyadh": "SAU", "jeddah": "SAU", "mecca": "SAU", "medina": "SAU",
    "dubai": "ARE", "abu dhabi": "ARE", "sharjah": "ARE",
    "doha": "QAT", "kuwait city": "KWT", "muscat": "OMN", "manama": "BHR",
    "amman": "JOR", "beirut": "LBN", "damascus": "SYR", "sanaa": "YEM",
    "tel aviv": "ISR", "jerusalem": "ISR", "haifa": "ISR",
    "kabul": "AFG", "tashkent": "UZB", "almaty": "KAZ", "astana": "KAZ",
    "nur-sultan": "KAZ", "baku": "AZE", "tbilisi": "GEO", "yerevan": "ARM",
    "bishkek": "KGZ", "dushanbe": "TJK", "ashgabat": "TKM",
    "aral sea": None, "caucasus": None,
    # Africa
    "cairo": "EGY", "alexandria": "EGY", "nile delta": "EGY",
    "lagos": "NGA", "abuja": "NGA", "kano": "NGA", "ibadan": "NGA",
    "nairobi": "KEN", "mombasa": "KEN", "kisumu": "KEN",
    "addis ababa": "ETH", "dar es salaam": "TZA", "dodoma": "TZA",
    "kampala": "UGA", "kigali": "RWA", "lusaka": "ZMB", "harare": "ZWE",
    "lilongwe": "MWI", "maputo": "MOZ", "luanda": "AGO", "accra": "GHA",
    "kumasi": "GHA", "abidjan": "CIV", "dakar": "SEN", "bamako": "MLI",
    "ouagadougou": "BFA", "niamey": "NER", "n'djamena": "TCD",
    "khartoum": "SDN", "juba": "SSD", "mogadishu": "SOM",
    "johannesburg": "ZAF", "cape town": "ZAF", "durban": "ZAF",
    "pretoria": "ZAF", "gauteng": "ZAF", "kwazulu-natal": "ZAF",
    "western cape": "ZAF", "casablanca": "MAR", "rabat": "MAR",
    "marrakesh": "MAR", "tunis": "TUN", "algiers": "DZA",
    "tripoli, libya": "LBY", "kinshasa": "COD", "yaounde": "CMR",
    "douala": "CMR", "antananarivo": "MDG", "sahel": None, "sahara": None,
    "lake victoria": None, "congo basin": None,
    # Latin America
    "sao paulo": "BRA", "são paulo": "BRA", "rio de janeiro": "BRA",
    "brasilia": "BRA", "salvador, brazil": "BRA", "belo horizonte": "BRA",
    "fortaleza": "BRA", "manaus": "BRA", "curitiba": "BRA",
    "recife": "BRA", "porto alegre": "BRA", "belem": "BRA",
    "amazon": None, "amazonia": "BRA", "cerrado": "BRA",
    "minas gerais": "BRA", "bahia": "BRA", "parana": "BRA",
    "rio grande do sul": "BRA", "pernambuco": "BRA",
    "buenos aires": "ARG", "cordoba, argentina": "ARG", "rosario": "ARG",
    "patagonia": None, "pampas": "ARG",
    "santiago, chile": "CHL", "valparaiso": "CHL", "atacama": "CHL",
    "lima": "PER", "cusco": "PER", "bogota": "COL", "medellin": "COL",
    "cali": "COL", "caracas": "VEN", "quito": "ECU", "guayaquil": "ECU",
    "la paz": "BOL", "montevideo": "URY", "asuncion": "PRY",
    "mexico city": "MEX", "guadalajara": "MEX", "monterrey": "MEX",
    "puebla": "MEX", "tijuana": "MEX", "yucatan": "MEX",
    "havana": "CUB", "san juan, puerto rico": "PRI",
    "guatemala city": "GTM", "san jose, costa rica": "CRI",
    "panama city": "PAN", "kingston, jamaica": "JAM",
    "port-au-prince": "HTI", "santo domingo": "DOM",
    # Canada
    "toronto": "CAN", "montreal": "CAN", "vancouver": "CAN",
    "calgary": "CAN", "ottawa": "CAN", "edmonton": "CAN",
    "quebec": "CAN", "ontario": "CAN", "british columbia": "CAN",
    "alberta": "CAN", "manitoba": "CAN", "saskatchewan": "CAN",
    "nova scotia": "CAN", "newfoundland": "CAN",
}

# Polysemous toponyms requiring contextual confirmation.
# {token: (iso3, required_context_regex, blocking_regex)}
AMBIGUOUS_TOPONYMS = {
    "georgia": ("GEO", r"\btbilisi\b|\bcaucasus\b|\bgeorgian?\s+(?:government|republic|highland)|\brepublic of georgia\b|\bblack sea\b",
                r"\batlanta\b|\bunited states\b|\bU\.?S\.?A?\b|\bsoutheast(?:ern)? (?:us|united states)\b|\bsavannah\b|\bgeorgia,? (?:usa|us)\b"),
    "turkey": ("TUR", r"\bistanbul\b|\bankara\b|\bizmir\b|\banatolia\b|\bturkish\b|\bt(?:ü|u)rkiye\b|\bmarmara\b|\baegean\b",
               r"\bwild turkey\b|\bturkey vulture\b|\bturkey (?:production|farm|meat|poultry|breast)\b|\bmeleagris\b"),
    "jordan": ("JOR", r"\bamman\b|\bjordanian\b|\bjordan valley\b|\bdead sea\b|\bpetra\b|\bjordan river\b|\bhashemite\b", r"\bjordan,? [A-Z]\w+\b"),
    "chad": ("TCD", r"\blake chad\b|\bn'?djamena\b|\bchadian\b|\bsahel\b", r""),
    "guinea": ("GIN", r"\bconakry\b|\bguinean\b(?! pig)|\bwest africa\b", r"\bguinea pig|\bnew guinea\b|\bequatorial guinea\b|\bguinea-?bissau\b|\bguinea fowl\b|\bguinea worm\b"),
    "niger": ("NER", r"\bniamey\b|\bnigerien\b|\bsahel\b", r"\bnigeria\b|\bniger river\b|\bniger delta\b|\bniger state\b"),
    "mali": ("MLI", r"\bbamako\b|\bmalian\b|\bsahel\b|\btimbuktu\b|\bniger river\b", r"\bsomalia\b|\bmalawi\b"),
    "oman": ("OMN", r"\bmuscat\b|\bomani\b|\bgulf of oman\b|\barabian peninsula\b", r"\bromania\b|\bwoman\b|\botto?man\b"),
    "chile": ("CHL", r"\bsantiago\b|\bchilean\b|\bandes\b|\bvalpara(?:i|í)so\b|\batacama\b|\bpatagonia\b", r"\bchile pepper|\bchili\b"),
    "china": ("CHN", r"", r"\bchina clay\b|\bbone china\b"),
    "india": ("IND", r"", r"\bindiana\b|\bindian ocean\b(?!.\bindia\b)|\bwest indies\b|\bindian reservation\b"),
    "ireland": ("IRL", r"\bdublin\b|\birish\b|\brepublic of ireland\b|\bcork\b|\bgalway\b", r"\bnorthern ireland\b"),
    "congo": ("COD", r"\bkinshasa\b|\bdemocratic republic\b|\bcongo basin\b|\bdrc\b", r"\bbrazzaville\b"),
    "samoa": ("WSM", r"\bapia\b|\bsamoan\b", r"\bamerican samoa\b"),
    "sudan": ("SDN", r"\bkhartoum\b|\bsudanese\b|\bdarfur\b|\bnile\b", r"\bsouth sudan\b"),
    "cyprus": ("CYP", r"\bnicosia\b|\bcypriot\b|\bmediterranean\b", r""),
    "lebanon": ("LBN", r"\bbeirut\b|\blebanese\b|\bmediterranean\b", r"\blebanon,? (?:pa|nh|tn|or|in|mo|ky|va|il|oh)\b"),
    "malta": ("MLT", r"\bvalletta\b|\bmaltese\b|\bmediterranean\b", r""),
    "panama": ("PAN", r"\bpanama city\b|\bpanamanian\b|\bpanama canal\b|\bisthmus\b|\bbarro colorado\b", r"\bpanama,? (?:fl|ok|ia)\b"),
}

# Non-country regional descriptors that should NOT be resolved to one country
SUPRANATIONAL = {
    "europe": "Europe (multi-country)",
    "european union": "Europe (multi-country)",
    "sub-saharan africa": "Africa (multi-country)",
    "west africa": "Africa (multi-country)",
    "east africa": "Africa (multi-country)",
    "southern africa": "Africa (multi-country)",
    "north africa": "Africa (multi-country)",
    "latin america": "Latin America (multi-country)",
    "south america": "Latin America (multi-country)",
    "central america": "Latin America (multi-country)",
    "southeast asia": "Asia (multi-country)",
    "south asia": "Asia (multi-country)",
    "east asia": "Asia (multi-country)",
    "central asia": "Asia (multi-country)",
    "middle east": "Middle East (multi-country)",
    "scandinavia": "Europe (multi-country)",
    "nordic countries": "Europe (multi-country)",
    "arctic": "Polar (multi-country)",
    "antarctic": "Polar (multi-country)",
    "global": "Global / worldwide",
    "worldwide": "Global / worldwide",
}

# ---------------------------------------------------------------------------
# Global North / South (UN "developed regions" definition, M49)
# ---------------------------------------------------------------------------
GLOBAL_NORTH = {
    "USA", "CAN", "GBR", "IRL", "FRA", "DEU", "ITA", "ESP", "PRT", "NLD",
    "BEL", "LUX", "CHE", "AUT", "SWE", "NOR", "DNK", "FIN", "ISL", "GRC",
    "POL", "CZE", "SVK", "HUN", "SVN", "HRV", "EST", "LVA", "LTU", "ROU",
    "BGR", "MLT", "CYP", "AND", "MCO", "SMR", "LIE", "VAT", "FRO", "GRL",
    "JPN", "AUS", "NZL", "ISR", "KOR", "SGP", "TWN", "HKG", "MAC",
    "RUS", "UKR", "BLR", "SRB", "BIH", "MKD", "MNE", "ALB", "XKX", "MDA",
}
# Note: the UN classification places Eastern Europe/CIS in "developed regions";
# Korea, Singapore, Taiwan, HK and Macao are added as high-income economies.
# This boundary is contested; the manuscript reports sensitivity to it.


def iso3_from_country_string(s):
    """Resolve a raw affiliation country token to ISO alpha-3."""
    n = _norm(s)
    if not n:
        return None
    n = re.sub(r"[.\)\(]", "", n).strip()
    if n in NAME_TO_ISO3:
        return NAME_TO_ISO3[n]
    # trailing qualifiers e.g. "Beijing 100101, China"
    parts = [p.strip() for p in n.split(",")]
    for p in reversed(parts):
        p = re.sub(r"\d+", "", p).strip()
        if p in NAME_TO_ISO3:
            return NAME_TO_ISO3[p]
    return None


def parse_affiliation_countries(affil_field):
    """Return (ordered unique ISO3 list, n_affiliation_strings)."""
    if not affil_field:
        return [], 0
    chunks = [c.strip() for c in affil_field.split(";") if c.strip()]
    isos = []
    for ch in chunks:
        tokens = [t.strip() for t in ch.split(",") if t.strip()]
        iso = None
        for t in reversed(tokens[-3:]):
            t2 = re.sub(r"\b\d[\d\- ]*\b", "", t).strip()
            iso = iso3_from_country_string(t2)
            if iso:
                break
        if iso:
            isos.append(iso)
    seen, out = set(), []
    for i in isos:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out, len(chunks)


def parse_affiliation_institutions(affil_field):
    """Heuristic institution extraction: the comma-token containing an
    organisational keyword, per ';'-separated affiliation string."""
    if not affil_field:
        return []
    org_kw = re.compile(
        r"\b(universit|institut|college|school|academy|academi|laborator|"
        r"centre|center|hospital|ministry|agency|department of\b.*\bgovern|"
        r"observatory|foundation|polytechnic|CNRS|CSIC|USGS|NASA|NOAA|CSIRO)\b",
        re.IGNORECASE)
    out, seen = [], set()
    for ch in affil_field.split(";"):
        best = None
        for tok in [t.strip() for t in ch.split(",")]:
            if org_kw.search(tok):
                # prefer the token that names the parent organisation
                if best is None or ("universit" in tok.lower()
                                    or "institut" in tok.lower()):
                    best = tok
        if best:
            key = _norm(best)
            if key not in seen:
                seen.add(key)
                out.append(best)
    return out


def _mk_case_patterns():
    pats = []
    # full country names & aliases (>=4 chars, avoid noisy short tokens)
    for name, iso in NAME_TO_ISO3.items():
        if len(name) < 4 or name in AMBIGUOUS_TOPONYMS:
            continue
        if name in {"us", "uk", "uae", "drc", "ksa"}:
            continue
        pats.append((re.compile(r"\b" + re.escape(name) + r"\b", re.I), iso, "country_name"))
    for dem, iso in DEMONYMS.items():
        if iso:
            pats.append((re.compile(r"\b" + re.escape(dem) + r"\b", re.I), iso, "demonym"))
    for city, iso in CITY_TO_ISO3.items():
        if iso:
            pats.append((re.compile(r"\b" + re.escape(city) + r"\b", re.I), iso, "city_region"))
    return pats


CASE_PATTERNS = _mk_case_patterns()
AMBIG_COMPILED = {
    tok: (iso,
          re.compile(ctx, re.I) if ctx else None,
          re.compile(blk, re.I) if blk else None)
    for tok, (iso, ctx, blk) in AMBIGUOUS_TOPONYMS.items()
}
SUPRA_COMPILED = {re.compile(r"\b" + re.escape(k) + r"\b", re.I): v
                  for k, v in SUPRANATIONAL.items()}


def detect_case_study_countries(text):
    """Detect the geography of the empirical case study.

    Returns (iso3_list, supranational_labels, evidence_kinds).
    """
    if not text:
        return [], [], []
    hits, kinds = {}, {}
    for pat, iso, kind in CASE_PATTERNS:
        if pat.search(text):
            hits[iso] = hits.get(iso, 0) + 1
            kinds.setdefault(iso, set()).add(kind)
    for tok, (iso, ctx, blk) in AMBIG_COMPILED.items():
        if re.search(r"\b" + re.escape(tok) + r"\b", text, re.I):
            if blk is not None and blk.search(text):
                if tok == "georgia":                       # resolve to the US
                    hits["USA"] = hits.get("USA", 0) + 1
                    kinds.setdefault("USA", set()).add("disambiguated")
                continue
            if ctx is not None and ctx.pattern and not ctx.search(text):
                continue
            hits[iso] = hits.get(iso, 0) + 1
            kinds.setdefault(iso, set()).add("disambiguated")
    supra = sorted({v for p, v in SUPRA_COMPILED.items() if p.search(text)})
    ordered = [k for k, _ in sorted(hits.items(), key=lambda kv: -kv[1])]
    ev = sorted({k for s in kinds.values() for k in s})
    return ordered, supra, ev


def hemisphere(iso3):
    return "Global North" if iso3 in GLOBAL_NORTH else "Global South"
