#!/usr/bin/env python3
"""
FIXED BVerfG Scraper with paginated crawl, verified selectors, and PDF fallback
Based on exact specifications for maximum coverage and quality
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
    """Extract text from PDF with streaming download"""
    try:
        fn = RAW / ("bverfg_" + re.sub(r"[^A-Za-z0-9]+", "_", pdf_url)[-80:] + ".pdf")
        
        # Stream download
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

def crawl_index():
    """Crawl official BVerfG index with pagination"""
    print("🔍 Crawling BVerfG official index...")
    all_links = []
    offset = 0
    empty_streak = 0
    
    while offset < 2000:  # Safety limit
        if offset == 0:
            url = LIST
        else:
            url = f"{LIST}?cms_id=Entscheidungen&offset={offset}"
        
        print(f"  Fetching offset {offset}...")
        
        try:
            r = session.get(url, timeout=30)
            r.raise_for_status()
            html = r.text
            time.sleep(1.0)
        except Exception as e:
            print(f"  ❌ Index error at offset {offset}: {e}")
            break
        
        soup = BeautifulSoup(html, "lxml")
        
        # Find decision links
        page_links = []
        for a in soup.select('a[href^="/SharedDocs/Entscheidungen/DE/"][href$=".html"]'):
            href = a.get("href")
            if href:
                full_url = urljoin(BASE, href)
                if full_url not in all_links:
                    page_links.append(full_url)
                    all_links.append(full_url)
        
        print(f"    Found {len(page_links)} new decisions")
        
        if not page_links:
            empty_streak += 1
            if empty_streak >= 3:
                print(f"    No results for {empty_streak} pages, stopping")
                break
        else:
            empty_streak = 0
        
        # Look for next page link
        next_link = soup.find("a", class_="btPagination__link", string=lambda s: s and "ächste" in s)
        if not next_link:
            print("    No more pages indicated")
            break
            
        offset += 20
        time.sleep(1)
    
    print(f"✅ Index crawl complete: {len(all_links)} total decisions found")
    return all_links

def parse_detail(url):
    """Parse BVerfG decision with verified selectors + PDF fallback"""
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        html = r.text
        time.sleep(0.8)
    except Exception as e:
        print(f"    ❌ Failed to fetch {url}: {e}")
        return None
    
    # Save raw HTML
    filename = "bverfg_" + re.sub(r"[^A-Za-z0-9]+", "_", url)[-80:] + ".html"
    (RAW / filename).write_text(html, encoding="utf-8")
    
    soup = BeautifulSoup(html, "lxml")
    
    # Extract title using verified selector
    title_elem = soup.select_one("h1.btHeadline__title")
    title = title_elem.get_text(" ", strip=True) if title_elem else "BVerfG Entscheidung"
    
    # Extract main text using verified selector
    body_elem = soup.select_one("div.btText") or soup.select_one("main") or soup
    
    if body_elem and body_elem.name != 'html':
        # Get structured content
        text_parts = []
        for elem in body_elem.select("p, li, div"):
            text = elem.get_text(" ", strip=True)
            if len(text) > 30:  # Skip short elements
                text_parts.append(text)
        txt = "\n\n".join(text_parts) if text_parts else body_elem.get_text(" ", strip=True)
    else:
        txt = soup.get_text(" ", strip=True)
    
    # Extract metadata using verified selector
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
    else:
        # Try to extract from URL as fallback
        url_match = re.search(r"(\d+bv[rlqe]\d+)", url.lower())
        if url_match:
            aktenz = url_match.group(1).upper().replace("BV", "Bv")
    
    # PDF fallback if content is short
    if len(txt) < 1000:
        pdf_elem = soup.select_one('a[href$=".pdf"]')
        if pdf_elem:
            pdf_url = urljoin(BASE, pdf_elem.get("href"))
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
        "title": title,
        "date": date,
        "citation": aktenz,
        "source_url": url,
        "text": txt,
        "meta": {"language": "de"}
    }

if __name__ == "__main__":
    print("🏛️ Starting FIXED BVerfG scraper (paginated crawl + PDF fallback)...")
    OUT.unlink(missing_ok=True)
    
    # Crawl the official index
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
            
            time.sleep(0.8)  # Be respectful
    
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