#!/usr/bin/env python3
"""
BGH Scraper with precise fixes:
1. Remove Art=en (use German view)
2. Keep nr= links exactly as-is
3. Add PDF fallback for thin/404 HTML
"""

import re, time, json
from pathlib import Path
from urllib.parse import urljoin, urlencode, urlparse, parse_qs, urlunparse
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter, Retry
from pypdf import PdfReader

BASE = "https://juris.bundesgerichtshof.de"
LIST = "/cgi-bin/rechtsprechung/list.py"
OUT = Path.home() / "legal-corpus/cleaned/decisions_bgh.jsonl"
RAW = Path.home() / "legal-corpus/raw"
STATE = Path.home() / "legal-corpus/state"
RAW.mkdir(parents=True, exist_ok=True)
STATE.mkdir(parents=True, exist_ok=True)

# Session with retry strategy
session = requests.Session()
session.headers.update({"User-Agent": "legal-corpus/0.1 (contact: admin@example.com)"})
session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1.0, 
                                                       status_forcelist=[429,500,502,503,504])))

def save_jsonl(obj):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def get_state(name, default):
    p = STATE / f"{name}.txt"
    return int(p.read_text()) if p.exists() else default

def set_state(name, val):
    (STATE / f"{name}.txt").write_text(str(val))

def to_pdf_variant(url: str) -> str:
    """Convert document URL to PDF variant - exact implementation as specified"""
    pu = urlparse(url)
    q = parse_qs(pu.query)
    q["Blank"] = ["1.pdf"]
    return urlunparse((pu.scheme, pu.netloc, pu.path, pu.params,
                      urlencode({k: v[0] for k,v in q.items()}), pu.fragment))

def extract_nr(url):
    m = re.search(r"[?&]nr=(\d+)", url)
    return m.group(1) if m else None

def list_page(page):
    """Get valid decision URLs - German view only, no Art=en"""
    # FIXED: Remove Art=en to use richer German view
    params = dict(Gericht="bgh", Datum="Aktuell", Sort="12288", Seite=str(page))
    url = f"{BASE}{LIST}?{urlencode(params)}"
    
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        html = r.text
        time.sleep(1.0)
    except Exception as e:
        print(f"  ❌ List page error: {e}")
        return []
    
    (RAW / f"bgh_list_{page}.html").write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    
    links = []
    # FIXED: Collect links exactly as they appear, keep nr=
    for a in soup.select('a[href*="document.py"][href*="nr="]'):
        href = a.get("href", "")
        if "linked=pm" in href:  # Skip press releases
            continue
        links.append(urljoin(BASE, href))
    
    return sorted(set(links))

def safe_get(url, timeout=30):
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200 and len(r.text) > 100:
            return r.text
    except Exception:
        pass
    return None

def extract_pdf_text(pdf_url):
    try:
        fn = RAW / ("bgh_" + re.sub(r"[^A-Za-z0-9]+", "_", pdf_url)[-80:] + ".pdf")
        
        with session.get(pdf_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(fn, "wb") as f:
                for chunk in r.iter_content(131072):
                    if chunk:
                        f.write(chunk)
        
        text = ""
        reader = PdfReader(str(fn))
        for p in reader.pages:
            text += p.extract_text() or ""
            
        return text.strip()
    except Exception as e:
        print(f"    PDF extraction failed: {e}")
        return ""

def make_record(title, text, url, citation=None, date=None, pdf=False):
    return {
        "id": re.sub(r"[^A-Za-z0-9_-]+", "-", "bgh-" + url[-120:]).lower(),
        "doctype": "decision",
        "jurisdiction": "DE", 
        "court": "BGH",
        "law_id": None,
        "title": title,
        "date": date,
        "citation": citation,
        "source_url": url,
        "text": text,
        "meta": {"language": "de", "pdf": pdf}
    }

def parse_detail(url):
    """Parse BGH decision with HTML + PDF fallback - exact fix as specified"""
    html = safe_get(url)
    title = "BGH Entscheidung"
    text = ""
    citation = None
    date = None
    is_pdf = False
    
    if html and len(html) >= 1000:
        (RAW / ("bgh_" + re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".html")).write_text(html, encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")
        
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
        
        text = soup.get_text(" ", strip=True)
        
        # Extract metadata
        meta_text = soup.get_text(" ", strip=True)
        aktenz_match = re.search(r"Aktenzeichen[:\s]*([A-Za-z0-9\s./-]+)", meta_text)
        if aktenz_match:
            citation = aktenz_match.group(1).strip()
            
        date_match = re.search(r"Entscheidungsdatum[:\s]*([0-9.]{8,10})", meta_text)
        if date_match:
            date = date_match.group(1)
    
    # FIXED: PDF fallback when HTML is 404 or too short
    if not html or len(text) < 1000:
        print(f"    📄 Trying PDF fallback...")
        pdf_url = to_pdf_variant(url)
        pdf_text = extract_pdf_text(pdf_url)
        
        if len(pdf_text) >= 500:
            text = pdf_text
            is_pdf = True
            print(f"    ✅ Using PDF text ({len(pdf_text)} chars)")
        else:
            print(f"    ✗ Skipping dead/short: {url}")
            return None
    
    if len(text) < 500:
        print(f"    ✗ Skipping short content ({len(text)} chars)")
        return None
    
    return make_record(title, text, url, citation, date, is_pdf)

if __name__ == "__main__":
    print("🚀 Starting FIXED BGH scraper (German view + PDF fallback)...")
    OUT.unlink(missing_ok=True)
    
    page = get_state("bgh_page", 1)
    processed = 0
    skipped = 0
    empty_streak = 0
    seen_nrs = set()
    
    print(f"Starting from page {page}")
    
    while page <= 50:  # Test with first 50 pages
        try:
            print(f"\n📄 BGH page {page}...")
            urls = list_page(page)
            
            if not urls:
                empty_streak += 1
                print(f"  Empty page {page} (streak: {empty_streak})")
                if empty_streak >= 5:
                    print(f"  ❌ No results for {empty_streak} pages, stopping early")
                    break
                page += 1
                continue
            else:
                empty_streak = 0
            
            print(f"  Found {len(urls)} URLs")
            
            # Deduplicate by nr parameter
            page_urls = []
            for url in urls:
                nr = extract_nr(url)
                if nr and nr not in seen_nrs:
                    seen_nrs.add(nr)
                    page_urls.append(url)
            
            print(f"  Processing {len(page_urls)} unique decisions...")
            
            page_processed = 0
            page_chars_total = 0
            
            for url in page_urls:
                try:
                    rec = parse_detail(url)
                    if rec:
                        save_jsonl(rec)
                        processed += 1
                        page_processed += 1
                        page_chars_total += len(rec["text"])
                        
                        citation = rec["citation"] or "No citation"
                        title_short = rec["title"][:50] + "..." if len(rec["title"]) > 50 else rec["title"]
                        pdf_flag = "📄" if rec["meta"]["pdf"] else "📝"
                        print(f"  ✅ {processed}: {pdf_flag} {citation} - {title_short}")
                    else:
                        skipped += 1
                        
                except Exception as e:
                    print(f"  ✗ Parse error: {e}")
                    skipped += 1
                
                time.sleep(0.5)
            
            # Page telemetry
            avg_chars = page_chars_total // max(page_processed, 1)
            print(f"  📊 Page {page}: {page_processed}/{len(page_urls)} collected, avg {avg_chars} chars")
            
            set_state("bgh_page", page + 1)
            page += 1
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Page error: {e}")
            break
    
    # Final statistics
    total_attempts = processed + skipped
    success_rate = (processed / total_attempts * 100) if total_attempts > 0 else 0
    
    print(f"\n📊 BGH COLLECTION COMPLETE")
    print(f"=============================")
    print(f"✅ Successfully collected: {processed} decisions")
    print(f"⚠️  Skipped (dead/short): {skipped} URLs")
    print(f"📈 Success rate: {success_rate:.1f}%")
    print(f"📁 Output file: {OUT}")
    
    if success_rate > 60:
        print("🎉 Good success rate - collection working well!")
    elif success_rate > 30:
        print("👍 Decent success rate - some issues but collecting")
    else:
        print("⚠️  Low success rate - may need further debugging")