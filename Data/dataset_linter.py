import json
import os
import re
from typing import Dict, Any, List, Tuple, Optional

"""
Dataset Linter for German Legal Instructi
on-Tuning Data

Inputs:
  - Data/massive_legal_data/train.jsonl

Outputs:
  - Data/massive_legal_data/clean.train.jsonl
  - Data/massive_legal_data/quality_report.md

Validation rules:
  1) JSON schema and required keys
     - Must contain "text" string.
     - Optional helper metadata keys: "source", "category", "instruction_type", "legal_term", "legal_source", "id".
  2) Template boundary checks
     - "text" must contain <s>[INST] ... [/INST] ... </s> in correct order, with non-empty instruction and answer.
  3) Placeholder and truncation checks
     - Reject if it contains unresolved placeholders like "{NAME}", "{LAW_REF}", "{PER}", "{LOC}".
     - Reject if overly truncated or malformed (heuristics).
  4) Legal citation validation (legal_source)
     - If legal_source exists, it must match a valid code family and plausible section/article number:
         * BGB §§ 1–2385
         * StGB §§ 1–358
         * StPO §§ 1–491
         * VwVfG §§ 1–110
         * VwGO §§ 1–197
         * GG Art. 1–146
     - Also reject common misattributions (e.g., using StPO for Diebstahl, which belongs to StGB).
  5) Consistency checks between legal_term/category and code family (basic heuristics).
  6) Boilerplate/same-answer clones (basic similarity hash to reduce obvious duplicates)

Notes:
  - This linter is conservative. It will discard rows that fail any critical check.
  - It does not attempt to auto-correct citations. That should be done in a separate enrichment pipeline.
"""

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "massive_legal_data")
INPUT_PATH = os.path.join(DATA_DIR, "train.jsonl")
CLEAN_PATH = os.path.join(DATA_DIR, "clean.train.jsonl")
REPORT_PATH = os.path.join(DATA_DIR, "quality_report.md")

# Regexes
INST_OPEN_RE = re.compile(r"<s>\s*\[INST\]\s*(.+?)\s*\[/INST\]\s*(.+?)\s*</s>|<s>\s*\[INST\]\s*(.+?)\s*\[/INST\]\s*(.+?)\s*</s>", re.DOTALL)
PLACEHOLDER_RE = re.compile(r"\{(?:NAME|LAW_REF|PER|LOC)\}")
WHITESPACE_RE = re.compile(r"\s+")

# Legal source parsing
LEGAL_SOURCE_RE = re.compile(
    r"^\s*(?P<code>BGB|StGB|StPO|VwVfG|VwGO|GG)\s*[§|Art\.]?\s*(?P<num>[\d]+)(?:\s*Abs\.\s*\d+)?", re.IGNORECASE
)

# Code family plausible ranges
CODE_RANGES = {
    "BGB": (1, 2385),
    "StGB": (1, 358),
    "StPO": (1, 491),
    "VwVfG": (1, 110),
    "VwGO": (1, 197),
    "GG": (1, 146),  # Articles
}

# Simple mapping from terms/categories to expected code families (heuristics)
EXPECTED_FAMILY_HINTS = {
    "Diebstahl": {"StGB"},
    "Raub": {"StGB"},
    "Totschlag": {"StGB"},
    "Beleidigung": {"StGB"},
    "Körperverletzung": {"StGB"},
    "Betrug": {"StGB"},
    "Untreue": {"StGB"},

    "Strafprozess": {"StPO"},
    "Strafprozessordnung": {"StPO"},

    "Widerspruch": {"VwVfG", "VwGO"},
    "Verhältnismäßigkeit": {"VwVfG", "VwGO"},
    "Verpflichtungsklage": {"VwGO"},
    "Anfechtungsklage": {"VwGO"},
    "Verwaltungsakt": {"VwVfG", "VwGO"},
    "Ermessen": {"VwVfG", "VwGO"},

    "Mietvertrag": {"BGB"},
    "Kaufvertrag": {"BGB"},
    "Werkvertrag": {"BGB"},
    "Gewährleistung": {"BGB"},
    "Scheidung": {"BGB"},
    "Sorgerecht": {"BGB"},
    "Erbfolge": {"BGB"},
    "Pfandrecht": {"BGB"},
    "Willenserklärung": {"BGB"},

    "Grundrechte": {"GG"},
    "Meinungsfreiheit": {"GG"},
    "Pressefreiheit": {"GG"},
    "Vereinigungsfreiheit": {"GG"},
    "Menschenwürde": {"GG"},

    # Arbeitsrecht terms often BGB/KSchG/ArbZG, but KSchG/ArbZG are not validated here; we only validate families we know.
    "Kündigung": {"BGB"},
    "Tarifvertrag": {"BGB"},
    "Arbeitszeit": {"BGB"},
    "Abmahnung": {"BGB"},
    "Zeugnis": {"BGB"},
}

CATEGORY_HINTS = {
    "strafrecht": {"StGB"},
    "strafrecht_case": {"StGB"},
    "verfassungsrecht": {"GG"},
    "verfassungsrecht_case": {"GG"},
    "verwaltungsrecht": {"VwVfG", "VwGO"},
    "verwaltungsrecht_case": {"VwVfG", "VwGO"},
    "buergerliches_recht": {"BGB"},
    "buergerliches_recht_case": {"BGB"},
    "arbeitsrecht": {"BGB"},
    "arbeitsrecht_case": {"BGB"},
}

def normalize_text(s: str) -> str:
    return WHITESPACE_RE.sub(" ", s).strip()

def parse_inst_block(text: str) -> Optional[Tuple[str, str]]:
    """
    Extract instruction and answer from the <s>[INST] ... [/INST] ... </s> or <s> variant.
    """
    m = INST_OPEN_RE.search(text)
    if not m:
        return None
    # The regex has two alternatives; pick non-None groups
    groups = m.groups()
    if len(groups) == 4:
        inst = groups[0] if groups[0] is not None else groups[2]
        ans = groups[1] if groups[1] is not None else groups[3]
    else:
        inst, ans = groups[0], groups[1]
    if not inst or not ans:
        return None
    inst = normalize_text(inst)
    ans = normalize_text(ans)
    if len(inst) < 5 or len(ans) < 10:
        return None
    return inst, ans

def has_placeholders(s: str) -> bool:
    return bool(PLACEHOLDER_RE.search(s))

def parse_legal_source(legal_source: str) -> Optional[Tuple[str, int]]:
    m = LEGAL_SOURCE_RE.match(legal_source.strip())
    if not m:
        return None
    code = m.group("code").upper()
    try:
        num = int(m.group("num"))
    except ValueError:
        return None
    return code, num

def legal_source_plausible(code: str, num: int) -> bool:
    if code not in CODE_RANGES:
        return False
    low, high = CODE_RANGES[code]
    return low <= num <= high

def infer_expected_families(sample: Dict[str, Any]) -> List[str]:
    hints = set()
    term = str(sample.get("legal_term", "") or "")
    cat = str(sample.get("category", "") or "")
    # Check term hints
    for k, families in EXPECTED_FAMILY_HINTS.items():
        if k.lower() in term.lower():
            hints.update(families)
    # Check category hints
    for k, families in CATEGORY_HINTS.items():
        if k.lower() == cat.lower():
            hints.update(families)
    return sorted(hints)

def is_truncated_answer(ans: str) -> bool:
    # Heuristic: if answer obviously ends mid-sentence without proper punctuation and length is suspicious.
    if ans.endswith("..."):
        return True
    # If last char is an unmatched opening clause
    if len(ans) > 40 and not re.search(r"[\.!?»”)]\s*$", ans):
        return True
    return False

def looks_like_boilerplate(ans: str) -> bool:
    boilerplate_patterns = [
        r"Nach der ständigen Rechtsprechung des Bundesgerichtshofs",
        r"Die Rechtssicherheit gebietet eine einheitliche Anwendung",
        r"Die praktische Anwendung erfordert eine umfassende Würdigung",
        r"Im Ergebnis führt dies zu folgenden rechtlichen Konsequenzen",
        r"Eine abweichende Beurteilung kommt nur in begründeten Ausnahmefällen in Betracht",
    ]
    return any(re.search(pat, ans) for pat in boilerplate_patterns)

def simple_answer_fingerprint(ans: str) -> str:
    # crude fingerprint to help detect clones
    s = ans.lower()
    s = re.sub(r"[^a-zäöüß0-9 ]", "", s)
    s = WHITESPACE_RE.sub(" ", s)
    tokens = s.split()
    core = tokens[:40]  # first 40 tokens
    return " ".join(core)

def validate_sample(raw: Dict[str, Any], report: Dict[str, int]) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    # 1) schema
    if "text" not in raw or not isinstance(raw["text"], str):
        report["schema_invalid"] += 1
        return False, "Missing or invalid 'text' field", None

    text = raw["text"]
    parsed = parse_inst_block(text)
    if not parsed:
        report["inst_template_invalid"] += 1
        return False, "Missing or invalid <s>[INST]..[/INST]..</s> template", None

    inst, ans = parsed

    # 3) placeholders
    if has_placeholders(text) or has_placeholders(inst) or has_placeholders(ans):
        report["placeholders"] += 1
        return False, "Unresolved placeholders found", None

    # 4) legal_source validation (if present)
    family_expected = infer_expected_families(raw)
    if "legal_source" in raw and raw["legal_source"]:
        parsed_ls = parse_legal_source(str(raw["legal_source"]))
        if not parsed_ls:
            report["legal_source_parse_failed"] += 1
            return False, "Unparseable legal_source", None
        code, num = parsed_ls
        if not legal_source_plausible(code, num):
            report["legal_source_range_invalid"] += 1
            return False, f"Implausible legal_source range {code} {num}", None
        # basic mismatch check with hints
        if family_expected and code not in family_expected:
            report["legal_source_mismatch_expected"] += 1
            return False, f"legal_source family {code} mismatches expected {family_expected}", None

    # 5) truncation
    if is_truncated_answer(ans):
        report["truncated"] += 1
        return False, "Answer appears truncated", None

    # 6) boilerplate detection (soft, but here we choose to reject extremely templated answers)
    if looks_like_boilerplate(ans):
        report["boilerplate"] += 1
        return False, "Answer looks like boilerplate", None

    # Passed critical checks; return normalized sample
    cleaned = dict(raw)
    cleaned["text"] = f"<s>[INST] {inst} [/INST] {ans} </s>"
    return True, "ok", cleaned

def lint_file(input_path: str, clean_path: str, report_path: str) -> None:
    stats = {
        "total": 0,
        "kept": 0,
        "schema_invalid": 0,
        "inst_template_invalid": 0,
        "placeholders": 0,
        "legal_source_parse_failed": 0,
        "legal_source_range_invalid": 0,
        "legal_source_mismatch_expected": 0,
        "truncated": 0,
        "boilerplate": 0,
        "duplicates_filtered": 0,
    }

    os.makedirs(os.path.dirname(clean_path), exist_ok=True)
    fingerprints_seen = set()
    kept_samples: List[Dict[str, Any]] = []
    issues: List[str] = []

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as fin:
        for i, line in enumerate(fin, start=1):
            line = line.strip()
            if not line:
                continue
            stats["total"] += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                stats["schema_invalid"] += 1
                issues.append(f"Line {i}: JSON decode error: {e}")
                continue

            ok, reason, cleaned = validate_sample(obj, stats)
            if not ok:
                issues.append(f"Line {i}: {reason}")
                continue

            # de-dup by answer fingerprint
            inst, ans = parse_inst_block(cleaned["text"]) or ("", "")
            fp = simple_answer_fingerprint(ans)
            if fp in fingerprints_seen:
                stats["duplicates_filtered"] += 1
                continue
            fingerprints_seen.add(fp)

            kept_samples.append(cleaned)
            stats["kept"] += 1

    # Write cleaned
    with open(clean_path, "w", encoding="utf-8") as fout:
        for obj in kept_samples:
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")

    # Write report
    with open(report_path, "w", encoding="utf-8") as fr:
        fr.write("# Dataset Quality Report\n\n")
        fr.write(f"- Input: {os.path.relpath(input_path, start=BASE_DIR)}\n")
        fr.write(f"- Cleaned output: {os.path.relpath(clean_path, start=BASE_DIR)}\n")
        fr.write(f"- Total lines: {stats['total']}\n")
        fr.write(f"- Kept: {stats['kept']}\n")
        fr.write(f"- Filtered (schema_invalid): {stats['schema_invalid']}\n")
        fr.write(f"- Filtered (inst_template_invalid): {stats['inst_template_invalid']}\n")
        fr.write(f"- Filtered (placeholders): {stats['placeholders']}\n")
        fr.write(f"- Filtered (legal_source_parse_failed): {stats['legal_source_parse_failed']}\n")
        fr.write(f"- Filtered (legal_source_range_invalid): {stats['legal_source_range_invalid']}\n")
        fr.write(f"- Filtered (legal_source_mismatch_expected): {stats['legal_source_mismatch_expected']}\n")
        fr.write(f"- Filtered (truncated): {stats['truncated']}\n")
        fr.write(f"- Filtered (boilerplate): {stats['boilerplate']}\n")
        fr.write(f"- Filtered (duplicates): {stats['duplicates_filtered']}\n")
        fr.write("\n## Issues (first 500)\n")
        for msg in issues[:500]:
            fr.write(f"- {msg}\n")

    print(f"Wrote cleaned dataset to: {clean_path}")
    print(f"Wrote quality report to: {report_path}")
    print("Stats:", stats)


if __name__ == "__main__":
    lint_file(INPUT_PATH, CLEAN_PATH, REPORT_PATH)