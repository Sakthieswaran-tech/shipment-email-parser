PROMPT_V1 = """Extract shipment details from this freight forwarding email.

Email Subject: {subject}
Email Body: {body}

Use the following rule for product_line:
- If destination port code starts with "IN" → product_line = "pl_sea_import_lcl"
- If origin port code starts with "IN" → product_line = "pl_sea_export_lcl"


Extract and return JSON with these fields:
- product_line
- origin_port_code: UN/LOCODE (5 letters)
- origin_port_name: Port name
- destination_port_code: UN/LOCODE (5 letters)  
- destination_port_name: Port name
- incoterm: Trade term (FOB, CIF, etc.)
- cargo_weight_kg: Weight in kg
- cargo_cbm: Volume in CBM
- is_dangerous: true/false

Return only valid JSON."""

PROMPT_V2 = """
You are a freight forwarding email parser. Extract shipment details into a SINGLE JSON object.

Email Subject: {subject}
Email Body: {body}

## PORT CODE ABBREVIATIONS (convert these to 5-letter UN/LOCODE):
- JED = SAJED (Jeddah)
- DAM = SADAM (Dammam)  
- RUH = SARUH (Riyadh)
- MAA = INMAA (Chennai)
- BLR = INBLR (Bangalore)
- HYD = INHYD (Hyderabad)
- SHA = CNSHA (Shanghai)
- SIN = SGSIN (Singapore)
- HKG/HK = HKHKG (Hong Kong)
- YOK = JPYOK (Yokohama)
- PUS = KRPUS (Busan)
- KEL = TWKEL (Keelung)
- SUB = IDSUB (Surabaya)
- HCM/SGN = VNSGN (Ho Chi Minh)
- CPT = ZACPT (Cape Town)
- HOU = USHOU (Houston)
- LAX = USLAX (Los Angeles)
- LGB = USLGB (Long Beach)
- MNL = PHMNL (Manila)
- JBL = AEJEA (Jebel Ali)
- HAM = DEHAM (Hamburg)
- LCH = THLCH (Laem Chabang)
- PKG = MYPKG (Port Klang)

## CRITICAL RULES FOR MULTIPLE SHIPMENTS:

When an email contains MULTIPLE shipment legs (e.g., "JED→MAA; DAM→BLR; RUH→HYD"):

1. **origin_port_code**: Use the FIRST shipment's origin code
2. **origin_port_name**: Combine ALL origin port names with " / " separator
   Example: "Jeddah / Dammam / Riyadh"
3. **destination_port_code**: Use the FIRST shipment's destination code  
4. **destination_port_name**: Combine ALL destination port names with " / " separator
   Example: "Chennai ICD / Bangalore ICD / Hyderabad ICD"
5. **cargo_cbm**: Use the FIRST mentioned CBM value from any shipment
6. **cargo_weight_kg**: Use the FIRST mentioned weight value from any shipment
7. **RT (Revenue Ton)**: This is NOT weight - ignore RT values for cargo_weight_kg

## OTHER RULES:

1. **product_line**:
   - If destination code starts with "IN" → "pl_sea_import_lcl"
   - If origin code starts with "IN" → "pl_sea_export_lcl"

2. **incoterm**:
   - Valid: FOB, CIF, CFR, EXW, DDP, DAP, FCA, CPT, CIP, DPU
   - If not mentioned or ambiguous → "FOB"

3. **is_dangerous**:
   - TRUE if ANY of these appear: DG, dangerous, hazardous, UN + number, Class + number, IMO, IMDG
   - FALSE if: non-DG, non-hazardous, not dangerous
   - FALSE if not mentioned

4. **Weight conversions**:
   - If in lbs: multiply by 0.453592
   - If in tonnes/MT: multiply by 1000
   - Round to 2 decimal places

5. **Null handling**:
   - Missing values → null (not 0 or empty string)
   - "TBD", "N/A" → null

## OUTPUT FORMAT:
Return ONLY a single JSON object (NOT an array):

{{
  "product_line": "pl_sea_import_lcl or pl_sea_export_lcl",
  "origin_port_code": "5-letter code or null",
  "origin_port_name": "name(s) or null",
  "destination_port_code": "5-letter code or null",
  "destination_port_name": "name(s) or null",
  "incoterm": "FOB/CIF/etc",
  "cargo_weight_kg": number or null,
  "cargo_cbm": number or null,
  "is_dangerous": true or false
}}

## EXAMPLE - Multiple shipments:

Email: "JED→MAA ICD 1.9 cbm; DAM→BLR ICD 3 RT; RUH→HYD ICD 850kg"

Output:
{{
  "product_line": "pl_sea_import_lcl",
  "origin_port_code": "SAJED",
  "origin_port_name": "Jeddah / Dammam / Riyadh",
  "destination_port_code": "INMAA",
  "destination_port_name": "Chennai ICD / Bangalore ICD / Hyderabad ICD",
  "incoterm": "FOB",
  "cargo_weight_kg": 850.0,
  "cargo_cbm": 1.9,
  "is_dangerous": false
}}

Return ONLY the JSON object. No explanation.
"""


PROMPT_V3 = """
You are an expert freight forwarding email parser. Extract shipment details with HIGH ACCURACY.

Email Subject: {subject}
Email Body: {body}

## OFFICIAL PORT CODES REFERENCE (USE ONLY THESE):

| Code   | Name(s)                                              |
|--------|------------------------------------------------------|
| AEJEA  | Jebel Ali                                            |
| BDDAC  | Dhaka                                                |
| CNGZG  | Guangzhou                                            |
| CNNSA  | Nansha                                               |
| CNQIN  | Qingdao                                              |
| CNSHA  | Shanghai                                             |
| CNSZX  | Shenzhen, Shenzhen / Guangzhou                       |
| CNTXG  | Xingang, Tianjin / Xingang, Xingang / Tianjin        |
| DEHAM  | Hamburg                                              |
| HKHKG  | Hong Kong                                            |
| IDSUB  | Surabaya                                             |
| INBLR  | Bangalore ICD, ICD Bangalore                         |
| INMAA  | Chennai, Chennai ICD, Bangalore ICD (via Chennai)    |
| INMUN  | Mundra ICD                                           |
| INNSA  | Nhava Sheva                                          |
| INWFD  | ICD Whitefield                                       |
| ITGOA  | Genoa                                                |
| JPOSA  | Osaka                                                |
| JPUKB  | Japan (generic)                                      |
| JPYOK  | Yokohama                                             |
| KRPUS  | Busan, Pusan                                         |
| MYPKG  | Port Klang, Colombo                                  |
| PHMNL  | Manila                                               |
| SAJED  | Jeddah, Jeddah / Dammam / Riyadh                     |
| SGSIN  | Singapore                                            |
| THBKK  | Bangkok, Bangkok ICD                                 |
| THLCH  | Laem Chabang                                         |
| TRAMR  | Ambarli, Ambarli / Izmir                             |
| TRIZM  | Izmir                                                |
| TWKEL  | Keelung                                              |
| USHOU  | Houston                                              |
| USLAX  | Los Angeles, Los Angeles / Houston / Long Beach      |
| VNSGN  | Ho Chi Minh, HCM                                     |
| ZACPT  | Cape Town                                            |

## 3-LETTER ABBREVIATION TO 5-LETTER CODE MAPPING:

| Abbrev | Code   | City           |
|--------|--------|----------------|
| JED    | SAJED  | Jeddah         |
| MAA    | INMAA  | Chennai        |
| BLR    | INBLR  | Bangalore      |
| HYD    | INMAA  | Hyderabad ICD  |
| NSA    | INNSA  | Nhava Sheva    |
| SHA    | CNSHA  | Shanghai       |
| SIN    | SGSIN  | Singapore      |
| HKG    | HKHKG  | Hong Kong      |
| HK     | HKHKG  | Hong Kong      |
| YOK    | JPYOK  | Yokohama       |
| PUS    | KRPUS  | Busan          |
| KEL    | TWKEL  | Keelung        |
| SUB    | IDSUB  | Surabaya       |
| HCM    | VNSGN  | Ho Chi Minh    |
| SGN    | VNSGN  | Ho Chi Minh    |
| CPT    | ZACPT  | Cape Town      |
| HOU    | USHOU  | Houston        |
| LAX    | USLAX  | Los Angeles    |
| LGB    | USLAX  | Long Beach     |
| MNL    | PHMNL  | Manila         |
| JBL    | AEJEA  | Jebel Ali      |
| HAM    | DEHAM  | Hamburg        |
| LCH    | THLCH  | Laem Chabang   |
| PKG    | MYPKG  | Port Klang     |
| BKK    | THBKK  | Bangkok        |
| COL    | MYPKG  | Colombo        |
| QIN    | CNQIN  | Qingdao        |
| SZX    | CNSZX  | Shenzhen       |
| GZG    | CNGZG  | Guangzhou      |
| OSA    | JPOSA  | Osaka          |
| DAC    | BDDAC  | Dhaka          |
| TXG    | CNTXG  | Xingang        |
| GOA    | ITGOA  | Genoa          |
| AMR    | TRAMR  | Ambarli        |
| IZM    | TRIZM  | Izmir          |
| MUN    | INMUN  | Mundra         |
| WFD    | INWFD  | Whitefield     |

## EXTRACTION RULES:

### 1. PORT CODES (CRITICAL):
- ALWAYS output 5-letter UN/LOCODE (e.g., INMAA not MAA)
- Use the mapping tables above
- If port not in reference → null for both code and name

### 2. PORT NAMES:
- Use EXACT names from the reference table
- Match the canonical name for the code used

### 3. PRODUCT LINE:
- destination_port_code starts with "IN" → "pl_sea_import_lcl"
- origin_port_code starts with "IN" → "pl_sea_export_lcl"

### 4. MULTIPLE SHIPMENTS (e.g., "JED→MAA; DAM→BLR; RUH→HYD"):
- origin_port_code: FIRST shipment's origin code
- origin_port_name: Combine ALL origins with " / "
- destination_port_code: FIRST shipment's destination code
- destination_port_name: Combine ALL destinations with " / "
- cargo_cbm: FIRST CBM value mentioned
- cargo_weight_kg: FIRST weight (kg) value mentioned

### 5. INCOTERM:
- Valid: FOB, CIF, CFR, EXW, DDP, DAP, FCA, CPT, CIP, DPU
- If email explicitly states one → use it
- If not mentioned or ambiguous → "FOB"
- "FCA" in email body is valid if explicitly mentioned

### 6. DANGEROUS GOODS:
- TRUE if: DG, dangerous, hazardous, UN + number, Class + number, IMO, IMDG
- FALSE if: non-DG, non-hazardous, "not dangerous"
- FALSE if not mentioned at all

### 7. WEIGHT (cargo_weight_kg):
- Extract weight in kilograms
- Convert: lbs × 0.453592, tonnes × 1000
- RT (Revenue Ton) = max(weight_tonnes, cbm) → multiply RT by 1000 for kg
- Round to 2 decimal places
- null if not mentioned

### 8. VOLUME (cargo_cbm):
- Extract CBM directly
- Do NOT calculate from dimensions
- Round to 2 decimal places
- null if not mentioned

## OUTPUT FORMAT:
Return ONLY valid JSON (no markdown, no explanation):

{{
  "product_line": "pl_sea_import_lcl or pl_sea_export_lcl",
  "origin_port_code": "5-LETTER CODE or null",
  "origin_port_name": "exact name from reference or null",
  "destination_port_code": "5-LETTER CODE or null",
  "destination_port_name": "exact name from reference or null",
  "incoterm": "FOB/CIF/FCA/etc",
  "cargo_weight_kg": number or null,
  "cargo_cbm": number or null,
  "is_dangerous": true or false
}}
"""

