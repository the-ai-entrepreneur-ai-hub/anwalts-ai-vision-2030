#!/usr/bin/env python3
"""
FIXED BGH Scraper with German view, PDF fallback, and smart filtering
Based on exact specifications for maximum coverage and quality
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
    """Save object to JSONL file"""
    with OUT.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def get_state(name, default):
    """Get state from file"""
    p = STATE / f"{name}.txt"
    return int(p.read_text()) if p.exists() else default

def set_state(name, val):
    """Set state to file"""
    (STATE / f"{name}.txt").write_text(str(val))

def pdf_variant(url: str) -> str:
    """Convert document URL to PDF variant"""
    u = urlparse(url)
    q = parse_qs(u.query)
    q["Blank"] = ["1.pdf"]
    return urlunparse((u.scheme, u.netloc, u.path, u.params, 
                      urlencode({k: v[0] for k, v in q.items()}), u.fragment))

def extract_nr(url):
    """Extract decision number from URL for deduplication"""
    m = re.search(r"[?&]nr=(\d+)", url)
    return m.group(1) if m else None

def list_page(page):
    """Get valid decision URLs from BGH listing (German view, filtered)"""
    # Use German view (no Art=en) for maximum coverage
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
    
    # Save raw HTML for debugging
    (RAW / f"bgh_list_{page}.html").write_text(html, encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    
    links = []
    for a in soup.select('a[href*="document.py"]'):
        href = a.get("href", "")
        
        # Filter out problematic links
        if "linked=pm" in href:  # Skip press releases
            continue
        if "nr=" not in href:  # Must have decision ID
            continue
            
        full_url = urljoin(BASE, href)
        links.append(full_url)
    
    return sorted(set(links))

def safe_get(url, timeout=30):
    """Safely get URL content"""
    try:
        r = session.get(url, timeout=timeout)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except Exception:
        pass
    return None

def extract_pdf_text(pdf_url):
    """Extract text from PDF with streaming download"""
    try:
        fn = RAW / ("bgh_" + re.sub(r"[^A-Za-z0-9]+", "_", pdf_url)[-80:] + ".pdf")
        
        # Stream download to avoid memory issues
        with session.get(pdf_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(fn, "wb") as f:
                for chunk in r.iter_content(131072):
                    if chunk:
                        f.write(chunk)
        
        # Extract text
        text = ""
        reader = PdfReader(str(fn))
        for p in reader.pages:
            text += p.extract_text() or ""
            
        return text.strip()
    except Exception as e:
        print(f"    PDF extraction failed: {e}")
        return ""

def make_record(title, text, url, citation=None, date=None, pdf=False):
    """Create standardized record"""
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
    """Parse BGH decision with HTML + PDF fallback"""
    # Try HTML first
    html = safe_get(url)
    title = "BGH Entscheidung"
    text = ""
    citation = None
    date = None
    used_pdf = False
    
    if html and len(html) >= 1000:
        # Save raw HTML
        (RAW / ("bgh_" + re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".html")).write_text(html, encoding="utf-8")
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(" ", strip=True)
            
        # Extract text
        text = soup.get_text(" ", strip=True)
        
        # Extract metadata
        meta_block = soup.find("table") or soup
        meta_text = meta_block.get_text(" ", strip=True)
        
        # Extract case number and date
        aktenz_match = re.search(r"Aktenzeichen[:\s]*([A-Za-z0-9\s./-]+)", meta_text)
        if aktenz_match:
            citation = aktenz_match.group(1).strip()
            
        date_match = re.search(r"Entscheidungsdatum[:\s]*([0-9.]{8,10})", meta_text)
        if date_match:
            date = date_match.group(1)
    
    # Try PDF fallback if HTML failed or is too short
    if not html or len(text) < 1000:
        print(f"    Trying PDF fallback...")
        pdf_url = pdf_variant(url)
        pdf_text = extract_pdf_text(pdf_url)
        
        if len(pdf_text) >= 500:
            # Use PDF content
            if len(pdf_text) > len(text):
                text = pdf_text
                used_pdf = True
                print(f"    ✅ Using PDF text ({len(pdf_text)} chars)")
        else:
            print(f"    ✗ PDF fallback failed")
    
    # Quality gate
    if len(text) < 500:
        print(f"    ✗ Skipping short content ({len(text)} chars)")
        return None
        
    # Light German check (optional soft gate)
    if not any(ch in text for ch in "äöüÄÖÜß§"):
        print(f"    ⚠ Content may not be German")
    
    return make_record(title, text, url, citation, date, used_pdf)

if __name__ == "__main__":
    print("🚀 Starting FIXED BGH scraper (German view + PDF fallback)...")
    OUT.unlink(missing_ok=True)
    
    page = get_state("bgh_page", 1)
    processed = 0
    skipped = 0
    empty_streak = 0
    seen_nrs = set()
    
    print(f"Starting from page {page}")
    
    while page <= 200:  # Increased limit since German view has more content
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
            
            print(f"  Found {len(urls)} potential URLs (after filtering)")
            
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
                
                time.sleep(0.5)  # Be respectful
            
            # Page telemetry
            avg_chars = page_chars_total // max(page_processed, 1)
            print(f"  📊 Page {page}: {page_processed}/{len(page_urls)} collected, avg {avg_chars} chars")
            
            set_state("bgh_page", page + 1)
            page += 1
            time.sleep(2)  # Longer pause between pages
            
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
    
    if success_rate < 20:
        print("⚠️  Low success rate - check if selectors need updating")
    elif success_rate > 60:
        print("🎉 Good success rate - collection working well!")