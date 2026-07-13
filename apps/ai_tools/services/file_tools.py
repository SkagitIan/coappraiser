import csv
import io
from datetime import datetime

DATE_NAMES = ["sale_date", "sold_date", "close_date", "closed_date", "contract_date"]
PRICE_NAMES = ["sale_price", "sold_price", "close_price", "price"]
LIST_NAMES = ["list_price", "original_list_price", "asking_price"]
DOM_NAMES = ["dom", "days_on_market", "marketing_time"]
TYPE_NAMES = ["property_type", "style", "type"]

def _normalized(value):
    return "".join(ch for ch in str(value).lower().strip() if ch.isalnum())

def detect_columns(fieldnames):
    normalized = {_normalized(name): name for name in fieldnames if name}
    def find(candidates):
        for candidate in candidates:
            if _normalized(candidate) in normalized:
                return normalized[_normalized(candidate)]
        for name in fieldnames:
            n = _normalized(name)
            if any(_normalized(candidate) in n for candidate in candidates):
                return name
        return ""
    return {"sale_date": find(DATE_NAMES), "sale_price": find(PRICE_NAMES), "list_price": find(LIST_NAMES), "dom": find(DOM_NAMES), "property_type": find(TYPE_NAMES)}

def _number(value):
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None

def _date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date().isoformat()
        except ValueError:
            pass
    return None

def analyze_csv(uploaded_file, mapping=None):
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    fieldnames = reader.fieldnames or []
    detected = detect_columns(fieldnames)
    if mapping:
        detected.update({key: value for key, value in mapping.items() if value})
    rows = list(reader)
    prices = [_number(row.get(detected["sale_price"])) for row in rows] if detected["sale_price"] else []
    prices = [x for x in prices if x is not None]
    doms = [_number(row.get(detected["dom"])) for row in rows] if detected["dom"] else []
    doms = [x for x in doms if x is not None]
    dates = [_date(row.get(detected["sale_date"])) for row in rows] if detected["sale_date"] else []
    dates = [x for x in dates if x]
    ratios = []
    if detected["list_price"] and detected["sale_price"]:
        for row in rows:
            sale, listing = _number(row.get(detected["sale_price"])), _number(row.get(detected["list_price"]))
            if sale is not None and listing:
                ratios.append(sale / listing)
    def median(values):
        values = sorted(values)
        if not values: return None
        mid = len(values) // 2
        return values[mid] if len(values) % 2 else (values[mid - 1] + values[mid]) / 2
    missing = [name for name in ("sale_date", "sale_price") if not detected[name]]
    return {"columns": fieldnames, "mapping": detected, "row_count": len(rows), "date_range": [min(dates), max(dates)] if dates else [], "sale_price": {"average": round(sum(prices) / len(prices), 2) if prices else None, "median": median(prices), "count": len(prices)}, "dom": {"average": round(sum(doms) / len(doms), 2) if doms else None, "median": median(doms), "count": len(doms)}, "list_to_sale_ratio": {"average": round(sum(ratios) / len(ratios), 4) if ratios else None, "count": len(ratios)}, "missing_required_columns": missing, "outlier_note": "Review unusually high or low sales before using this summary." if prices else "No sale prices were detected."}

def extract_pdf_text(uploaded_file):
    try:
        from pypdf import PdfReader
        reader = PdfReader(uploaded_file)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as exc:
        raise ValueError("CoAppraiser could not read this PDF. You can paste the relevant report section manually below.") from exc

