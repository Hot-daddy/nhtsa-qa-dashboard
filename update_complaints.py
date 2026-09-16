import argparse
import csv
import io
import json
import os
import re
import tempfile
import time
import unicodedata
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

GOOGLE_SHEET_ID = "1BMlASAFSqNOwyU9AfysERrao39i0kvl94z1JLe-7Zxk"
WORKSHEET_TITLE = "Tire_Complaints"

NHTSA_COMPLAINT_URLS = [
    (
        "2020-2024",
        "https://static.nhtsa.gov/odi/ffdd/cmpl/"
        "COMPLAINTS_RECEIVED_2020-2024.zip",
    ),
    (
        "2025-2026",
        "https://static.nhtsa.gov/odi/ffdd/cmpl/"
        "COMPLAINTS_RECEIVED_2025-2026.zip",
    ),
]

REQUEST_TIMEOUT = 180
MAX_RETRIES = 3
WRITE_BATCH_SIZE = 400
MAX_ALLOWED_DROP_RATE = 0.25

NHTSA_FIELDS = [
    "CMPLID",
    "ODINO",
    "MFR_NAME",
    "MAKETXT",
    "MODELTXT",
    "YEARTXT",
    "CRASH",
    "FAILDATE",
    "FIRE",
    "INJURED",
    "DEATHS",
    "COMPDESC",
    "CITY",
    "STATE",
    "VIN",
    "DATEA",
    "LDATE",
    "MILES",
    "OCCURENCES",
    "CDESCR",
    "CMPL_TYPE",
    "POLICE_RPT_YN",
    "PURCH_DT",
    "ORIG_OWNER_YN",
    "ANTI_BRAKES_YN",
    "CRUISE_CONT_YN",
    "NUM_CYLS",
    "DRIVE_TRAIN",
    "FUEL_SYS",
    "FUEL_TYPE",
    "TRANS_TYPE",
    "VEH_SPEED",
    "DOT",
    "TIRE_SIZE",
    "LOC_OF_TIRE",
    "TIRE_FAIL_TYPE",
    "ORIG_EQUIP_YN",
    "MANUF_DT",
    "SEAT_TYPE",
    "RESTRAINT_TYPE",
    "DEALER_NAME",
    "DEALER_TEL",
    "DEALER_CITY",
    "DEALER_STATE",
    "DEALER_ZIP",
    "PROD_TYPE",
    "REPAIRED_YN",
    "MEDICAL_ATTN",
    "VEHICLES_TOWED_YN",
    "STATE_OF_INCIDENT",
    "VEHICLE_OPERATOR",
]

OUTPUT_COLUMNS = [
    "ODI_Number",
    "Complaint_Received_Date",
    "Failure_Date",
    "Brand_Original",
    "Brand_Standard",
    "Brand_Confidence",
    "Pattern_Original",
    "Pattern_Standard",
    "Pattern_Source",
    "Pattern_Confidence",
    "Pattern_Review_Required",
    "Manufacturer",
    "Component",
    "DOT",
    "DOT_Plant_Code",
    "DOT_Production_Week",
    "DOT_Production_Year",
    "Tire_Size",
    "Product_Year",
    "Vehicle_Context",
    "Mileage",
    "Vehicle_Speed",
    "OE_RE",
    "Tire_Location",
    "NHTSA_Failure_Code",
    "Primary_Issue",
    "Secondary_Issues",
    "Safety_Risk",
    "Warranty_Complaint_YN",
    "Crash_YN",
    "Fire_YN",
    "Injuries",
    "Deaths",
    "Medical_Attention_YN",
    "Towed_YN",
    "Incident_State",
    "Description",
    "Source_URL",
    "Data_Quality_Flags",
]

KNOWN_BRANDS = [
    ("NEXEN", ["NEXEN"]),
    ("BRIDGESTONE", ["BRIDGESTONE"]),
    ("FIRESTONE", ["FIRESTONE"]),
    ("GOODYEAR", ["GOODYEAR"]),
    ("DUNLOP", ["DUNLOP"]),
    ("MICHELIN", ["MICHELIN"]),
    ("BFGOODRICH", ["BFGOODRICH", "B F GOODRICH"]),
    ("CONTINENTAL", ["CONTINENTAL"]),
    ("GENERAL TIRE", ["GENERAL TIRE"]),
    ("PIRELLI", ["PIRELLI"]),
    ("HANKOOK", ["HANKOOK"]),
    ("KUMHO", ["KUMHO"]),
    ("COOPER", ["COOPER TIRE", "COOPER"]),
    ("FALKEN", ["FALKEN"]),
    ("YOKOHAMA", ["YOKOHAMA"]),
    ("TOYO", ["TOYO"]),
    ("NOKIAN", ["NOKIAN"]),
    ("SUMITOMO", ["SUMITOMO"]),
    ("SENTURY", ["SENTURY"]),
    ("CASTLE ROCK", ["CASTLE ROCK"]),
]

ISSUE_RULES = [
    (
        "Tread Separation",
        r"tread\s+(?:separat|detach)|tread.*(?:came|coming)\s+off|"
        r"tread\s+(?:was|is)\s+gone",
    ),
    ("Blowout", r"blow[ -]?out|blew\s+out|explod(?:e|ed|ing|es|sion)"),
    (
        "Belt/Internal Separation",
        r"belt\s+separat|internal.*separat|separat.*inside|radial.*damage",
    ),
    ("Dry Rot/Cracking", r"dry\s*rot|weather\s*check|\bcrack(?:s|ed|ing)?\b"),
    (
        "Rapid/Irregular Wear",
        r"premature\s+wear|rapid\s+wear|uneven\s+wear|\bwore\b|\bworn\b|"
        r"2\s*/\s*32|belt\s+wires?|steel\s+belt",
    ),
    ("Chunking/Peeling", r"chunk(?:ing|ed)?|peel(?:ing|ed)?|pieces?\s+of\s+(?:tire|rubber)"),
    ("Sidewall Bubble/Bulge", r"\bbubble\b|\bbulge\b|\bswell(?:ing|ed)?\b"),
    (
        "Air Loss/Leak",
        r"slow\s+leak|air\s+loss|going\s+flat|went\s+flat|"
        r"tire\s+(?:was|is)\s+flat|pressure.*very\s+low",
    ),
    ("Vibration/Out-of-Round", r"vibrat|\bshudder|out[ -]of[ -]round|\bshak(?:e|ing)"),
    ("Road Hazard", r"\bpuncture|\bnail\b|road\s+hazard|\bpothole\b|hit.*object"),
    (
        "Warranty/Claim Handling",
        r"claim\s+(?:was\s+)?denied|warranty|reject(?:ed|ion)|refund\s+claim|\brude\b",
    ),
]

FAILURE_CODE_MAP = {
    "BST": "Sidewall Bubble/Bulge",
    "BLW": "Blowout",
    "TTL": "Dry Rot/Cracking",
    "OFR": "Vibration/Out-of-Round",
    "TSW": "Air Loss/Leak",
    "TTR": "Road Hazard",
    "TSP": "Tread Separation",
}

PRIMARY_ISSUE_ORDER = [
    "Tread Separation",
    "Blowout",
    "Belt/Internal Separation",
    "Sidewall Bubble/Bulge",
    "Dry Rot/Cracking",
    "Rapid/Irregular Wear",
    "Chunking/Peeling",
    "Air Loss/Leak",
    "Vibration/Out-of-Round",
    "Road Hazard",
    "Warranty/Claim Handling",
]


def clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).replace("\x00", " ").split())


def normalized_match_text(value):
    value = unicodedata.normalize("NFKD", clean_text(value))
    value = value.encode("ascii", "ignore").decode("ascii").upper()
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", value).split())


def normalized_display(value):
    return clean_text(value).upper()


def parse_int(value):
    try:
        return max(int(float(clean_text(value) or "0")), 0)
    except ValueError:
        return 0


def normalize_yes_no(value):
    return "Y" if clean_text(value).upper() == "Y" else "N"


def normalize_date(value):
    value = re.sub(r"\D", "", clean_text(value))
    if len(value) != 8:
        return ""
    try:
        return datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        return ""


def most_common_value(values, unknown_values=None):
    unknown_values = unknown_values or set()
    cleaned = [clean_text(value) for value in values if clean_text(value)]
    preferred = [
        value for value in cleaned if value.upper() not in unknown_values
    ]
    candidates = preferred or cleaned
    if not candidates:
        return ""
    return Counter(candidates).most_common(1)[0][0]


def download_file(url, destination):
    import requests

    last_error = None
    headers = {"User-Agent": "NHTSA-Tire-Quality-Dashboard/2.0"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"다운로드 중: {url} (시도 {attempt}/{MAX_RETRIES})")
            with requests.get(
                url,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                stream=True,
            ) as response:
                response.raise_for_status()
                with open(destination, "wb") as output_file:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output_file.write(chunk)

            if not zipfile.is_zipfile(destination):
                raise ValueError("다운로드한 파일이 유효한 ZIP 파일이 아닙니다.")

            with zipfile.ZipFile(destination) as archive:
                damaged_file = archive.testzip()
                if damaged_file:
                    raise ValueError(f"ZIP 내부 파일이 손상되었습니다: {damaged_file}")

            return
        except (requests.RequestException, OSError, ValueError, zipfile.BadZipFile) as exc:
            last_error = exc
            print(f"다운로드 실패: {exc}")
            if attempt < MAX_RETRIES:
                time.sleep(2**attempt)

    raise RuntimeError(f"NHTSA 불만 파일 다운로드에 실패했습니다: {url}") from last_error


def read_tire_rows(zip_path, source_label):
    cases = {}
    total_rows = 0
    tire_rows = 0

    with zipfile.ZipFile(zip_path) as archive:
        text_files = [name for name in archive.namelist() if name.lower().endswith(".txt")]
        if len(text_files) != 1:
            raise RuntimeError(
                f"{source_label}: ZIP 안의 TXT 파일 수가 예상과 다릅니다."
            )

        with archive.open(text_files[0]) as binary_file:
            text_file = io.TextIOWrapper(
                binary_file,
                encoding="utf-8",
                errors="replace",
                newline="",
            )
            reader = csv.reader(text_file, delimiter="\t")

            for line_number, row in enumerate(reader, start=1):
                total_rows += 1
                if len(row) != len(NHTSA_FIELDS):
                    raise RuntimeError(
                        f"{source_label} {line_number}행의 필드 수가 "
                        f"{len(row)}개입니다. 예상값은 {len(NHTSA_FIELDS)}개입니다."
                    )

                record = dict(zip(NHTSA_FIELDS, row))
                if clean_text(record["PROD_TYPE"]).upper() != "T":
                    continue

                tire_rows += 1
                odi_number = clean_text(record["ODINO"])
                if not odi_number:
                    continue

                case = cases.setdefault(
                    odi_number,
                    {
                        "source_labels": set(),
                        "manufacturers": [],
                        "makes": [],
                        "models": [],
                        "product_years": [],
                        "received_dates": [],
                        "failure_dates": [],
                        "components": set(),
                        "dots": [],
                        "sizes": [],
                        "locations": set(),
                        "failure_codes": set(),
                        "orig_equipment": set(),
                        "descriptions": [],
                        "mileages": [],
                        "vehicle_speeds": [],
                        "states": set(),
                        "crash": "N",
                        "fire": "N",
                        "injuries": 0,
                        "deaths": 0,
                        "medical_attention": "N",
                        "towed": "N",
                    },
                )

                case["source_labels"].add(source_label)
                case["manufacturers"].append(record["MFR_NAME"])
                case["makes"].append(record["MAKETXT"])
                case["models"].append(record["MODELTXT"])
                case["product_years"].append(record["YEARTXT"])
                case["received_dates"].append(record["LDATE"])
                case["failure_dates"].append(record["FAILDATE"])
                case["components"].add(clean_text(record["COMPDESC"]))
                case["dots"].append(record["DOT"])
                case["sizes"].append(record["TIRE_SIZE"])
                case["locations"].add(clean_text(record["LOC_OF_TIRE"]))
                case["failure_codes"].add(
                    clean_text(record["TIRE_FAIL_TYPE"]).upper()
                )
                case["orig_equipment"].add(
                    clean_text(record["ORIG_EQUIP_YN"]).upper()
                )
                case["descriptions"].append(clean_text(record["CDESCR"]))
                case["mileages"].append(record["MILES"])
                case["vehicle_speeds"].append(record["VEH_SPEED"])
                case["states"].add(
                    clean_text(record["STATE_OF_INCIDENT"] or record["STATE"])
                )

                if normalize_yes_no(record["CRASH"]) == "Y":
                    case["crash"] = "Y"
                if normalize_yes_no(record["FIRE"]) == "Y":
                    case["fire"] = "Y"
                if normalize_yes_no(record["MEDICAL_ATTN"]) == "Y":
                    case["medical_attention"] = "Y"
                if normalize_yes_no(record["VEHICLES_TOWED_YN"]) == "Y":
                    case["towed"] = "Y"

                case["injuries"] = max(
                    case["injuries"], parse_int(record["INJURED"])
                )
                case["deaths"] = max(
                    case["deaths"], parse_int(record["DEATHS"])
                )

    if total_rows == 0 or tire_rows == 0:
        raise RuntimeError(f"{source_label}: 사용할 수 있는 타이어 데이터가 없습니다.")

    print(
        f"{source_label}: 전체 {total_rows:,}행, "
        f"타이어 {tire_rows:,}행, 고유 ODI {len(cases):,}건"
    )
    return cases


def merge_cases(target, incoming):
    for odi_number, source_case in incoming.items():
        if odi_number not in target:
            target[odi_number] = source_case
            continue

        case = target[odi_number]
        for key in [
            "source_labels",
            "components",
            "locations",
            "failure_codes",
            "orig_equipment",
            "states",
        ]:
            case[key].update(source_case[key])

        for key in [
            "manufacturers",
            "makes",
            "models",
            "product_years",
            "received_dates",
            "failure_dates",
            "dots",
            "sizes",
            "descriptions",
            "mileages",
            "vehicle_speeds",
        ]:
            case[key].extend(source_case[key])

        for key in ["crash", "fire", "medical_attention", "towed"]:
            if source_case[key] == "Y":
                case[key] = "Y"

        case["injuries"] = max(case["injuries"], source_case["injuries"])
        case["deaths"] = max(case["deaths"], source_case["deaths"])


def load_pattern_master(path):
    rules = []
    with open(path, encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        required_columns = {"Pattern_Standard", "Alias"}
        if not required_columns.issubset(reader.fieldnames or []):
            raise RuntimeError("pattern_master.csv의 컬럼 구조가 올바르지 않습니다.")

        for row in reader:
            standard = clean_text(row["Pattern_Standard"])
            alias = normalized_match_text(row["Alias"])
            if standard and alias:
                rules.append((standard, alias))

    rules.sort(key=lambda item: len(item[1]), reverse=True)
    if not rules:
        raise RuntimeError("pattern_master.csv에 패턴 규칙이 없습니다.")
    return rules


def match_pattern(value, pattern_rules):
    haystack = f" {normalized_match_text(value)} "
    for standard, alias in pattern_rules:
        if f" {alias} " in haystack:
            return standard
    return ""


def classify_brand(manufacturer, make, model, description):
    manufacturer_norm = normalized_match_text(manufacturer)
    make_norm = normalized_match_text(make)
    model_norm = normalized_match_text(model)
    description_norm = normalized_match_text(description)
    unknown_values = {"", "UNKNOWN", "UNKNOWN MANUFACTURER", "NOT REPORTED"}

    if "NEXEN" in make_norm or "NEXEN" in manufacturer_norm:
        return "NEXEN", "High", False

    if " NEXEN " in f" {description_norm} ":
        conflict = make_norm not in unknown_values or manufacturer_norm not in unknown_values
        return "NEXEN", "Medium", conflict

    if model_norm == "NEXEN":
        return "NEXEN", "Low", True

    candidates = f" {make_norm} {manufacturer_norm} "
    for standard, aliases in KNOWN_BRANDS:
        if any(f" {normalized_match_text(alias)} " in candidates for alias in aliases):
            return standard, "High", False

    if make_norm not in unknown_values:
        return make_norm, "Medium", False

    return "UNKNOWN", "Low", True


def classify_pattern(brand, model, description, dot_value, pattern_rules):
    model_display = normalized_display(model)

    if brand != "NEXEN":
        if model_display and model_display not in {"UNKNOWN", "NOT REPORTED"}:
            return model_display, "MODELTXT", "Medium", False
        return "UNKNOWN", "Unresolved", "Low", True

    description_pattern = match_pattern(description, pattern_rules)
    model_pattern = match_pattern(model, pattern_rules)
    dot_pattern = match_pattern(dot_value, pattern_rules)

    if description_pattern:
        conflict = bool(model_pattern and model_pattern != description_pattern)
        confidence = "Medium" if conflict else "High"
        return description_pattern, "Description", confidence, conflict

    if model_pattern:
        return model_pattern, "MODELTXT", "Medium", False

    if dot_pattern:
        return dot_pattern, "DOT field", "Low", True

    generic_models = {"", "UNKNOWN", "NEXEN", "ROADIAN", "NOT REPORTED"}
    if model_display not in generic_models:
        return model_display, "Unmapped MODELTXT", "Low", True

    return "UNKNOWN", "Unresolved", "Low", True


def extract_tire_size(size_value, description):
    direct_value = normalized_display(size_value)
    if direct_value and direct_value not in {"UNKNOWN", "N/A"}:
        return direct_value.replace(" ", "")

    text = normalized_match_text(description)
    metric_match = re.search(
        r"\b(P|LT|ST)?\s*(\d{3})\s+(\d{2})\s*(ZR|R)?\s*(\d{2})\b",
        text,
    )
    if metric_match:
        prefix, width, ratio, construction, rim = metric_match.groups()
        return f"{prefix or ''}{width}/{ratio}{construction or 'R'}{rim}"

    flotation_match = re.search(
        r"\b(\d{2,3})\s+X\s+(\d{1,2}(?:\s+\d+)?)\s+R\s*(\d{2})\b",
        text,
    )
    if flotation_match:
        diameter, width, rim = flotation_match.groups()
        return f"{diameter}X{width.replace(' ', '.') }R{rim}"

    return ""


def parse_dot(dot_value):
    dot_text = normalized_display(dot_value)
    compact = re.sub(r"[^A-Z0-9]", "", re.sub(r"^DOT", "", dot_text))
    plant_code = compact[:3] if len(compact) >= 3 else ""

    week = ""
    year = ""
    candidates = re.findall(r"(?<!\d)(\d{4})(?!\d)", dot_text)
    if not candidates and len(compact) >= 4:
        candidates = [compact[-4:]]

    for candidate in reversed(candidates):
        candidate_week = parse_int(candidate[:2])
        candidate_year = parse_int(candidate[2:])
        if 1 <= candidate_week <= 53:
            week = f"{candidate_week:02d}"
            year = str(2000 + candidate_year)
            break

    return plant_code, week, year


def extract_vehicle_context(description):
    patterns = [
        r"(?:owns|owned)\s+(?:a|an)\s+((?:19|20)\d{2}\s+[^,.;]{2,60})",
        r"(?:OEM|factory installed)\s+(?:tires?\s+)?on\s+((?:19|20)\d{2}\s+[^,.;-]{2,60})",
    ]
    for pattern in patterns:
        match = re.search(pattern, description, flags=re.IGNORECASE)
        if match:
            value = re.split(
                r"\s+(?:equipped|with|that|which)\s+",
                clean_text(match.group(1)),
                maxsplit=1,
                flags=re.IGNORECASE,
            )[0]
            return value[:80]
    return ""


def classify_issues(description, components, failure_codes):
    searchable = " ".join([description, components])
    issues = []

    for issue_name, pattern in ISSUE_RULES:
        if re.search(pattern, searchable, flags=re.IGNORECASE):
            issues.append(issue_name)

    for failure_code in failure_codes.split(" | "):
        mapped_issue = FAILURE_CODE_MAP.get(failure_code)
        if mapped_issue and mapped_issue not in issues:
            issues.append(mapped_issue)

    if not issues:
        issues = ["Other/Unclassified"]

    primary = next(
        (issue for issue in PRIMARY_ISSUE_ORDER if issue in issues),
        issues[0],
    )
    secondary = [issue for issue in issues if issue != primary]
    return primary, " | ".join(secondary)


def determine_safety_risk(case, primary_issue, secondary_issues):
    all_issues = f"{primary_issue} | {secondary_issues}"
    if case["deaths"] > 0:
        return "Critical"
    if (
        case["injuries"] > 0
        or case["crash"] == "Y"
        or case["fire"] == "Y"
    ):
        return "High"
    high_risk_issues = [
        "Tread Separation",
        "Blowout",
        "Belt/Internal Separation",
    ]
    if any(issue in all_issues for issue in high_risk_issues):
        return "High"
    if primary_issue == "Warranty/Claim Handling":
        return "Low"
    return "Medium"


def finalize_case(odi_number, case, pattern_rules):
    unknown_values = {"UNKNOWN", "UNKNOWN MANUFACTURER", "NOT REPORTED"}
    manufacturer = most_common_value(case["manufacturers"], unknown_values)
    make = most_common_value(case["makes"], unknown_values)
    model = most_common_value(case["models"], unknown_values)
    product_year = most_common_value(case["product_years"], {"9999", "0000"})
    dot_value = most_common_value(case["dots"], {"UNKNOWN", "N/A"})
    size_value = most_common_value(case["sizes"], {"UNKNOWN", "N/A"})
    description = max(case["descriptions"], key=len, default="")

    received_date = max(
        (normalize_date(value) for value in case["received_dates"]),
        default="",
    )
    failure_date = max(
        (normalize_date(value) for value in case["failure_dates"]),
        default="",
    )
    components = " | ".join(sorted(value for value in case["components"] if value))
    failure_codes = " | ".join(
        sorted(value for value in case["failure_codes"] if value)
    )

    brand, brand_confidence, brand_review = classify_brand(
        manufacturer,
        make,
        model,
        description,
    )
    pattern, pattern_source, pattern_confidence, pattern_review = classify_pattern(
        brand,
        model,
        description,
        dot_value,
        pattern_rules,
    )
    tire_size = extract_tire_size(size_value, description)
    plant_code, production_week, production_year = parse_dot(dot_value)
    primary_issue, secondary_issues = classify_issues(
        description,
        components,
        failure_codes,
    )
    safety_risk = determine_safety_risk(
        case,
        primary_issue,
        secondary_issues,
    )

    flags = []
    if brand_review:
        flags.append("Brand review")
    if pattern_review:
        flags.append("Pattern review")
    if brand == "UNKNOWN":
        flags.append("Brand unknown")
    if pattern == "UNKNOWN":
        flags.append("Pattern unknown")
    if not tire_size:
        flags.append("Tire size missing")
    if not dot_value:
        flags.append("DOT missing")
    if dot_value and not (production_week and production_year):
        flags.append("DOT date incomplete")

    if len({normalized_display(value) for value in case["makes"] if clean_text(value)}) > 1:
        flags.append("Make conflict")
    if len({normalized_display(value) for value in case["models"] if clean_text(value)}) > 1:
        flags.append("Model conflict")

    oe_values = {value for value in case["orig_equipment"] if value}
    if "Y" in oe_values:
        oe_re = "OE"
    elif "N" in oe_values:
        oe_re = "RE"
    else:
        oe_re = "Unknown"

    mileage = max((parse_int(value) for value in case["mileages"]), default=0)
    vehicle_speed = max(
        (parse_int(value) for value in case["vehicle_speeds"]),
        default=0,
    )
    locations = " | ".join(sorted(value for value in case["locations"] if value))
    incident_state = most_common_value(case["states"])
    warranty_flag = (
        "Y"
        if "Warranty/Claim Handling" in f"{primary_issue} | {secondary_issues}"
        else "N"
    )

    return [
        odi_number,
        received_date,
        failure_date,
        make or manufacturer,
        brand,
        brand_confidence,
        model,
        pattern,
        pattern_source,
        pattern_confidence,
        "Y" if pattern_review else "N",
        manufacturer,
        components,
        dot_value,
        plant_code,
        production_week,
        production_year,
        tire_size,
        product_year,
        extract_vehicle_context(description),
        str(mileage) if mileage else "",
        str(vehicle_speed) if vehicle_speed else "",
        oe_re,
        locations,
        failure_codes,
        primary_issue,
        secondary_issues,
        safety_risk,
        warranty_flag,
        case["crash"],
        case["fire"],
        str(case["injuries"]),
        str(case["deaths"]),
        case["medical_attention"],
        case["towed"],
        incident_state,
        description[:20000],
        f"https://api.nhtsa.gov/complaints/odinumber?odinumber={odi_number}",
        " | ".join(flags),
    ]


def build_output_rows(cases, pattern_rules):
    data_rows = [
        finalize_case(odi_number, case, pattern_rules)
        for odi_number, case in cases.items()
    ]
    date_index = OUTPUT_COLUMNS.index("Complaint_Received_Date")
    odi_index = OUTPUT_COLUMNS.index("ODI_Number")
    data_rows.sort(
        key=lambda row: (row[date_index], row[odi_index]),
        reverse=True,
    )
    return [OUTPUT_COLUMNS, *data_rows]


def validate_output_rows(rows):
    if not rows or rows[0] != OUTPUT_COLUMNS:
        raise RuntimeError("불만 데이터의 출력 헤더가 올바르지 않습니다.")

    if len(rows) <= 1:
        raise RuntimeError(
            "타이어 불만 데이터가 0건입니다. 기존 Google Sheets를 유지합니다."
        )

    odi_index = OUTPUT_COLUMNS.index("ODI_Number")
    seen_odi = set()

    for row_number, row in enumerate(rows[1:], start=2):
        if len(row) != len(OUTPUT_COLUMNS):
            raise RuntimeError(f"출력 {row_number}행의 컬럼 수가 올바르지 않습니다.")
        odi_number = row[odi_index]
        if not odi_number or odi_number in seen_odi:
            raise RuntimeError(f"중복 또는 빈 ODI Number가 있습니다: {odi_number}")
        seen_odi.add(odi_number)


def connect_spreadsheet():
    import gspread

    credentials_json = os.environ.get("GCP_CREDENTIALS")
    if not credentials_json:
        raise RuntimeError("GitHub Secret 'GCP_CREDENTIALS'를 찾을 수 없습니다.")

    try:
        credentials_dict = json.loads(credentials_json)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GCP_CREDENTIALS가 올바른 JSON 형식이 아닙니다.") from exc

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    try:
        client = gspread.service_account_from_dict(
            credentials_dict,
            scopes=scopes,
        )
        return client.open_by_key(GOOGLE_SHEET_ID)
    except Exception as exc:
        raise RuntimeError(
            "Google Sheets 인증 또는 연결에 실패했습니다."
        ) from exc


def column_letter(column_number):
    letters = ""
    while column_number:
        column_number, remainder = divmod(column_number - 1, 26)
        letters = chr(65 + remainder) + letters
    return letters


def write_rows_in_batches(worksheet, rows):
    end_column = column_letter(len(OUTPUT_COLUMNS))
    for start_index in range(0, len(rows), WRITE_BATCH_SIZE):
        batch = rows[start_index : start_index + WRITE_BATCH_SIZE]
        start_row = start_index + 1
        end_row = start_row + len(batch) - 1
        worksheet.update(
            values=batch,
            range_name=f"A{start_row}:{end_column}{end_row}",
            value_input_option="RAW",
        )
        print(f"Staging 작성: {start_row:,}~{end_row:,}행")


def update_google_sheet_safely(spreadsheet, rows):
    from gspread.exceptions import WorksheetNotFound

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    staging_title = f"{WORKSHEET_TITLE}_Staging_{timestamp}"
    backup_title = f"{WORKSHEET_TITLE}_Backup_{timestamp}"
    staging = None

    try:
        production = spreadsheet.worksheet(WORKSHEET_TITLE)
        old_data_count = max(len(production.get_all_values()) - 1, 0)
    except WorksheetNotFound:
        production = None
        old_data_count = 0

    new_data_count = len(rows) - 1
    if (
        old_data_count >= 100
        and new_data_count < old_data_count * (1 - MAX_ALLOWED_DROP_RATE)
    ):
        raise RuntimeError(
            f"새 데이터가 기존 대비 25% 이상 감소했습니다. "
            f"기존 {old_data_count:,}건, 신규 {new_data_count:,}건. "
            "기존 시트를 유지합니다."
        )

    try:
        staging = spreadsheet.add_worksheet(
            title=staging_title,
            rows=max(len(rows) + 10, 100),
            cols=len(OUTPUT_COLUMNS),
        )
        write_rows_in_batches(staging, rows)

        staged_values = staging.get_all_values()
        if len(staged_values) != len(rows) or staged_values[0] != OUTPUT_COLUMNS:
            raise RuntimeError("Staging 시트 검증에 실패했습니다.")

        if production is None:
            staging.update_title(WORKSHEET_TITLE)
        else:
            spreadsheet.batch_update(
                {
                    "requests": [
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": production.id,
                                    "title": backup_title,
                                },
                                "fields": "title",
                            }
                        },
                        {
                            "updateSheetProperties": {
                                "properties": {
                                    "sheetId": staging.id,
                                    "title": WORKSHEET_TITLE,
                                },
                                "fields": "title",
                            }
                        },
                    ]
                }
            )

            new_production = spreadsheet.worksheet(WORKSHEET_TITLE)
            if len(new_production.get_all_values()) != len(rows):
                raise RuntimeError("Production 시트 전환 후 검증에 실패했습니다.")

            try:
                spreadsheet.del_worksheet(spreadsheet.worksheet(backup_title))
            except Exception as cleanup_error:
                print(f"경고: 백업 탭 정리에 실패했습니다: {cleanup_error}")

        print(f"Google Sheets '{WORKSHEET_TITLE}' 업데이트 완료: {new_data_count:,}건")

    except Exception:
        if staging is not None:
            try:
                current_staging = spreadsheet.worksheet(staging_title)
                spreadsheet.del_worksheet(current_staging)
            except Exception:
                pass
        raise


def write_csv(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(rows)


def collect_cases(input_zip_paths=None):
    all_cases = {}

    if input_zip_paths:
        for index, zip_path in enumerate(input_zip_paths, start=1):
            source_cases = read_tire_rows(zip_path, f"Local-{index}")
            merge_cases(all_cases, source_cases)
        return all_cases

    with tempfile.TemporaryDirectory(prefix="nhtsa-complaints-") as temp_dir:
        for source_label, url in NHTSA_COMPLAINT_URLS:
            zip_path = Path(temp_dir) / f"complaints-{source_label}.zip"
            download_file(url, zip_path)
            source_cases = read_tire_rows(zip_path, source_label)
            merge_cases(all_cases, source_cases)

    return all_cases


def parse_args():
    parser = argparse.ArgumentParser(
        description="Collect and normalize NHTSA tire complaint data."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Collect and validate data without updating Google Sheets.",
    )
    parser.add_argument(
        "--input-zip",
        action="append",
        default=[],
        help="Use a local NHTSA complaint ZIP file. May be repeated.",
    )
    parser.add_argument(
        "--output-csv",
        help="Optionally save normalized data to a local CSV file.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pattern_path = Path(__file__).with_name("pattern_master.csv")

    print("=" * 70)
    print("NHTSA 타이어 불만 데이터 수집 시작")
    print("=" * 70)

    pattern_rules = load_pattern_master(pattern_path)
    cases = collect_cases(args.input_zip or None)
    rows = build_output_rows(cases, pattern_rules)
    validate_output_rows(rows)

    brand_index = OUTPUT_COLUMNS.index("Brand_Standard")
    nexen_count = sum(row[brand_index] == "NEXEN" for row in rows[1:])
    print(f"고유 타이어 불만: {len(rows) - 1:,}건")
    print(f"NEXEN 관련 불만: {nexen_count:,}건")

    if args.output_csv:
        write_csv(args.output_csv, rows)
        print(f"CSV 저장 완료: {args.output_csv}")

    if args.dry_run:
        print("Dry run 완료: Google Sheets는 변경하지 않았습니다.")
        return

    spreadsheet = connect_spreadsheet()
    update_google_sheet_safely(spreadsheet, rows)

    print("=" * 70)
    print("NHTSA 타이어 불만 데이터 업데이트 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
