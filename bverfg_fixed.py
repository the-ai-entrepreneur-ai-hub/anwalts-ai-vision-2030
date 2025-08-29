#!/usr/bin/env python3
"""
BVerfG Scraper with precise fixes:
1. Replace seeds with real index crawl + pagination by offset=20
2. Use verified selectors (h1.btHeadline__title, div.btText)
3. Add PDF fallback when HTML is short
"""

import json, time, re
from urllib.parse import urljoin
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter, Retry
from bs4 import BeautifulSoup
from pypdf import PdfReader

BASE = "https://www.bundesverfassungsgericht.de"
LIST = f"{BASE}/DE/Entscheidungen/Entscheidungen_node.html"
OUT = Path.home() / "legal-corpus/cleaned/decisions_bverfg.jsonl"
RAW = Path.home() / "legal-corpus/raw"
RAW.mkdir(parents=True, exist_ok=True)

# Session with retry strategy
session = requests.Session()
session.headers.update({"User-Agent": "legal-corpus/0.1 (contact: admin@example.com)"})
session.mount("https://", HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1.0, 
                                                       status_forcelist=[429,500,502,503,504])))

def extract_pdf_text(pdf_url):
    try:
        fn = RAW / ("bverfg_" + re.sub(r"[^A-Za-z0-9]+", "_", pdf_url)[-80:] + ".pdf")
        
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

def fetch(url, sleep=1.0):
    """Safe fetch with retry"""
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        time.sleep(sleep)
        return r.text
    except Exception as e:
        print(f"    Fetch error {url}: {e}")
        return ""

def crawl_index():
    """Crawl BVerfG index with offset=20 pagination - exact fix as specified"""
    print("🔍 Crawling BVerfG official index with pagination...")
    all_links = []
    offset = 0
    
    while True:
        # FIXED: Start at official index and paginate by offset=20
        url = LIST if offset == 0 else f"{LIST}?cms_id=Entscheidungen&offset={offset}"
        print(f"  Fetching offset {offset}...")
        
        html = fetch(url)
        if not html:
            print(f"    Failed to fetch offset {offset}")
            break
            
        soup = BeautifulSoup(html, "lxml")
        
        # FIXED: Use exact selector for SharedDocs decision links
        page_links = [urljoin(BASE, a["href"]) for a in soup.select(
            'a[href^="/SharedDocs/Entscheidungen/DE/"][href$=".html"]')]
        
        if not page_links:
            print(f"    No more decisions at offset {offset}")
            break
            
        # Add new links only
        new_links = [link for link in page_links if link not in all_links]
        all_links.extend(new_links)
        print(f"    Found {len(new_links)} new decisions ({len(all_links)} total)")
        
        # FIXED: Look for next page exactly as specified
        next_link = soup.find("a", class_="btPagination__link", string=lambda s: s and "ächste" in s)
        if not next_link:
            print(f"    No more pages indicated")
            break
            
        offset += 20
        
        # Safety limit
        if offset > 2000:
            print(f"    Reached safety limit at offset {offset}")
            break
    
    print(f"✅ Index crawl complete: {len(all_links)} total decisions found")
    return all_links

def parse_detail(url):
    """Parse BVerfG decision with verified selectors + PDF fallback - exact fix as specified"""
    html = fetch(url, 0.8)
    if not html:
        return None
    
    # Save raw HTML
    filename = "bverfg_" + re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".html"
    (RAW / filename).write_text(html, encoding="utf-8")
    
    soup = BeautifulSoup(html, "lxml")
    
    # FIXED: Extract with verified selectors
    title = soup.select_one("h1.btHeadline__title")
    title_text = title.get_text(" ", strip=True) if title else "BVerfG Entscheidung"
    
    body = soup.select_one("div.btText") or soup.select_one("main") or soup
    
    # FIXED: Extract structured content as specified
    txt = "\n".join(p.get_text(" ", strip=True)
                    for p in (body.select("p,li,div") if body else [])
                    if len(p.get_text(strip=True)) > 30) or body.get_text(" ", strip=True)
    
    # Extract metadata
    aktenz = None
    date = None
    meta_elem = soup.select_one("div.btMetadaten")
    
    if meta_elem:
        mtxt = meta_elem.get_text(" ", strip=True)
        
        # Extract case number (various formats: 1 BvR 123/20, 2 BvE 4/19, etc.)
        m = re.search(r"\b([12])\s*Bv([RLQE])\s*(\d+/\d{2,4})\b", mtxt)
        if m:
            aktenz = f"{m.group(1)} Bv{m.group(2)} {m.group(3)}"
            aktenz = re.sub(r"\s+", " ", aktenz)
        
        # Extract date (DD.MM.YYYY format)
        d = re.search(r"\b(\d{2}\.\d{2}\.\d{4})\b", mtxt)
        if d:
            date = d.group(1)
    
    # FIXED: PDF fallback if content is short - exact implementation
    pdf_a = soup.select_one('a[href$=".pdf"]')
    if (not txt or len(txt) < 400) and pdf_a:
        pdf_url = urljoin(BASE, pdf_a["href"])
        print(f"    📄 Trying PDF fallback: {pdf_url}")
        pdf_text = extract_pdf_text(pdf_url)
        if len(pdf_text) > len(txt) * 0.8:
            txt = pdf_text
            print(f"    ✅ Using PDF text ({len(pdf_text)} chars)")
    
    # Final quality gate
    if len(txt) < 400:
        print(f"    ✗ Skipping short content ({len(txt)} chars)")
        return None
    
    return {
        "id": re.sub(r"[^A-Za-z0-9_-]+", "-", "bverfg-" + url[-120:]).lower(),
        "doctype": "decision",
        "jurisdiction": "DE",
        "court": "BVerfG",
        "law_id": None,
        "title": title_text,
        "date": date,
        "citation": aktenz,
        "source_url": url,
        "text": txt,
        "meta": {"language": "de"}
    }

if __name__ == "__main__":
    print("🏛️ Starting FIXED BVerfG scraper (index crawl + PDF fallback)...")
    OUT.unlink(missing_ok=True)
    
    # FIXED: Crawl the official index instead of using seeds
    decision_urls = crawl_index()
    
    if not decision_urls:
        print("❌ No decisions found in index")
        exit(1)
    
    print(f"\n📚 Processing {len(decision_urls)} decisions...")
    
    processed = 0
    skipped = 0
    
    with OUT.open("w", encoding="utf-8") as f:
        for i, url in enumerate(decision_urls, 1):
            try:
                rec = parse_detail(url)
                if rec:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    processed += 1
                    
                    citation = rec["citation"] or "No citation"
                    title_short = rec["title"][:60] + "..." if len(rec["title"]) > 60 else rec["title"]
                    print(f"  ✅ {processed}: {citation} - {title_short}")
                else:
                    skipped += 1
                    
            except Exception as e:
                print(f"  ✗ WARN {url}: {e}")
                skipped += 1
            
            # Progress indicator
            if i % 20 == 0:
                print(f"  📊 Progress: {i}/{len(decision_urls)} ({processed} collected, {skipped} skipped)")
            
            time.sleep(0.8)
    
    # Final statistics
    total = processed + skipped
    success_rate = (processed / total * 100) if total > 0 else 0
    
    print(f"\n📊 BVERFG COLLECTION COMPLETE")
    print(f"==============================")
    print(f"✅ Successfully collected: {processed} decisions")
    print(f"⚠️  Skipped (short/error): {skipped} decisions")
    print(f"📈 Success rate: {success_rate:.1f}%")
    print(f"📁 Output file: {OUT}")
    
    if processed >= 100:
        print("🎉 Excellent collection - ready for training!")
    elif processed >= 50:
        print("👍 Good collection - decent for training")
    else:
        print("⚠️  Small collection - check if index structure changed")