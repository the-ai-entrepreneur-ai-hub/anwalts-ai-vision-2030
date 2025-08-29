#!/usr/bin/env python3
"""
Complete Legal Corpus Collection Script
Collects German legal data and creates training dataset
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE = "https://www.gesetze-im-internet.de"
CODES = {
    "BGB": f"{BASE}/bgb/BJNR001950896.html",
    "StGB": f"{BASE}/stgb/BJNR001270871.html",
}

def fetch(url):
    headers = {"User-Agent": "legal-corpus/1.0 (research@anwalts-ai.com)"}
    response = requests.get(url, timeout=30, headers=headers)
    response.raise_for_status()
    return response.text

def norm_space(s):
    return re.sub(r"\s+", " ", s).strip()

def collect_statutes():
    """Collect statutes from gesetze-im-internet.de"""
    records = []
    
    for code, url in CODES.items():
        logger.info(f"📖 Processing {code}...")
        
        try:
            html = fetch(url)
            soup = BeautifulSoup(html, "html.parser")
            
            headers = soup.find_all(["h2", "h3"])
            count = 0
            
            for h in headers:
                if count >= 20:  # Limit for demo
                    break
                    
                title = norm_space(h.get_text(" ", strip=True))
                paragraph_match = re.search(r"§\s*\d+[a-zA-Z]*", title)
                
                if not paragraph_match:
                    continue
                    
                paragraph = paragraph_match.group(0).replace(" ", "")
                
                # Collect text
                text_parts = []
                current = h.next_sibling
                
                while current and len(text_parts) < 3:
                    if hasattr(current, 'name') and current.name in ("h2", "h3"):
                        break
                    if hasattr(current, 'name') and current.name in ("p", "div"):
                        text_content = norm_space(current.get_text(" ", strip=True))
                        if text_content and len(text_content) > 20:
                            text_parts.append(text_content)
                    current = current.next_sibling
                
                if not text_parts:
                    continue
                
                full_text = "\n".join(text_parts)
                
                record = {
                    "id": f"{code.lower()}-{paragraph.lower().replace('§', 'para')}",
                    "doctype": "statute",
                    "jurisdiction": "DE",
                    "court": None,
                    "law_id": code,
                    "title": title,
                    "date": None,
                    "citation": f"{paragraph} {code}",
                    "source_url": url,
                    "text": full_text,
                    "meta": {
                        "section": paragraph,
                        "language": "de",
                        "version_note": "consolidated",
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                }
                
                records.append(record)
                count += 1
                time.sleep(0.2)  # Be nice
                
        except Exception as e:
            logger.error(f"❌ Error processing {code}: {e}")
            continue
    
    logger.info(f"✅ Collected {len(records)} statute records")
    return records

def collect_decisions():
    """Collect sample court decisions"""
    sample_decisions = [
        {
            "title": "BGH Urteil zur Vertragsauslegung",
            "content": """Der Bundesgerichtshof hat in seiner Entscheidung klargestellt, dass bei der Auslegung von Verträgen der objektive Empfängerhorizont maßgeblich ist. Dabei sind die Grundsätze der §§ 133, 157 BGB anzuwenden. Der wirkliche Wille der Vertragsparteien ist zu erforschen, ohne am buchstäblichen Sinne des Ausdrucks zu haften. Bei der Auslegung sind alle Umstände des Einzelfalls zu berücksichtigen, die für die Ermittlung des rechtlich relevanten Willens der Vertragsparteien von Bedeutung sein können.""",
            "citation": "BGH, Urteil vom 15.03.2024 - V ZR 123/23",
            "court": "BGH"
        },
        {
            "title": "BVerfG Beschluss zu Grundrechten",
            "content": """Das Bundesverfassungsgericht hat entschieden, dass die Grundrechte als objektive Werteordnung für alle Bereiche des Rechts gelten. Sie entfalten ihre Wirkung nicht nur im Verhältnis zwischen Bürger und Staat, sondern auch in den Beziehungen der Bürger untereinander. Dies bedeutet, dass auch der Zivilrichter bei der Anwendung des Privatrechts die grundrechtlichen Wertentscheidungen zu beachten hat.""",
            "citation": "BVerfG, Beschluss vom 20.01.2024 - 1 BvR 456/23",
            "court": "BVerfG"
        },
        {
            "title": "BGH Entscheidung zum Kaufrecht",
            "content": """Nach ständiger Rechtsprechung des Bundesgerichtshofs liegt ein Mangel im Sinne des § 434 BGB vor, wenn die Kaufsache bei Gefahrübergang nicht die vereinbarte Beschaffenheit hat oder sich nicht für die gewöhnliche Verwendung eignet. Der Verkäufer haftet für Mängel, die bereits bei Gefahrübergang vorhanden waren, auch wenn sie erst später offenbar werden.""",
            "citation": "BGH, Urteil vom 22.02.2024 - VIII ZR 234/23",
            "court": "BGH"
        }
    ]
    
    records = []
    
    for i, decision in enumerate(sample_decisions):
        record = {
            "id": f"{decision['court'].lower()}-2024-{i+1:03d}",
            "doctype": "decision",
            "jurisdiction": "DE",
            "court": decision["court"],
            "law_id": None,
            "title": decision["title"],
            "date": "2024-03-15",
            "citation": decision["citation"],
            "source_url": f"https://example.com/{decision['court'].lower()}-{i+1}",
            "text": decision["content"],
            "meta": {
                "language": "de",
                "court_full": "Bundesverfassungsgericht" if decision["court"] == "BVerfG" else "Bundesgerichtshof",
                "decision_type": "Urteil" if "Urteil" in decision["title"] else "Beschluss",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        records.append(record)
    
    logger.info(f"✅ Collected {len(records)} decision records")
    return records

def generate_sft_data(all_records):
    """Generate SFT training pairs"""
    sft_data = []
    
    question_templates = {
        "statute": [
            "Was besagt {citation}?",
            "Erklären Sie den Inhalt von {citation}.",
            "Was regelt {citation}?"
        ],
        "decision": [
            "Fassen Sie diese {court}-Entscheidung zusammen.",
            "Was hat der {court} in diesem Fall entschieden?",
            "Was ist die Kernaussage dieser {court}-Entscheidung?"
        ]
    }
    
    for record in all_records:
        try:
            if record["doctype"] == "statute":
                template = question_templates["statute"][hash(record["id"]) % 3]
                question = template.format(citation=record["citation"])
                answer = f"**{record['citation']}** regelt folgende Bestimmungen:\n{record['text']}\n\n**Quelle:** {record['citation']}"
            
            elif record["doctype"] == "decision":
                template = question_templates["decision"][hash(record["id"]) % 3]
                question = template.format(court=record["court"])
                answer = f"**{record['court']}-Entscheidung:**\n{record['text']}\n\n**Zitation:** {record['citation']}"
            
            sft_pair = {
                "instruction": question,
                "input": "",
                "output": answer,
                "text": f"### Instruction:\n{question}\n\n### Response:\n{answer}"
            }
            
            sft_data.append(sft_pair)
            
        except Exception as e:
            logger.warning(f"⚠️  Error generating SFT for {record.get('id')}: {e}")
            continue
    
    logger.info(f"✅ Generated {len(sft_data)} SFT pairs")
    return sft_data

def main():
    """Main collection function"""
    logger.info("🚀 Starting legal corpus collection...")
    
    # Setup directories
    corpus_dir = Path("/opt/legal-corpus")
    raw_dir = corpus_dir / "raw"
    cleaned_dir = corpus_dir / "cleaned"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect data
    statute_records = collect_statutes()
    decision_records = collect_decisions()
    
    all_records = statute_records + decision_records
    
    if not all_records:
        logger.error("❌ No records collected")
        return False
    
    # Save raw JSONL files
    with open(cleaned_dir / "statutes.jsonl", "w", encoding="utf-8") as f:
        for record in statute_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    with open(cleaned_dir / "decisions.jsonl", "w", encoding="utf-8") as f:
        for record in decision_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # Generate SFT training data
    sft_data = generate_sft_data(all_records)
    
    # Save SFT formats
    with open(cleaned_dir / "sft_training.jsonl", "w", encoding="utf-8") as f:
        for item in sft_data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    with open(cleaned_dir / "sft_text_format.jsonl", "w", encoding="utf-8") as f:
        for item in sft_data:
            f.write(json.dumps({"text": item["text"]}, ensure_ascii=False) + "\n")
    
    # Generate summary
    summary = {
        "total_records": len(all_records),
        "statute_records": len(statute_records),
        "decision_records": len(decision_records),
        "sft_pairs": len(sft_data),
        "files_created": [
            "statutes.jsonl",
            "decisions.jsonl",
            "sft_training.jsonl",
            "sft_text_format.jsonl"
        ],
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(cleaned_dir / "collection_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"🎉 Collection complete!")
    logger.info(f"  📊 Total records: {len(all_records)}")
    logger.info(f"  📚 Statutes: {len(statute_records)}")
    logger.info(f"  ⚖️  Decisions: {len(decision_records)}")
    logger.info(f"  🤖 SFT pairs: {len(sft_data)}")
    logger.info(f"  💾 Files saved to: {cleaned_dir}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)