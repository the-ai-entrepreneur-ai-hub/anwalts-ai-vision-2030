#!/usr/bin/env python3
"""
Run All Legal Corpus Scrapers
Executes all available scrapers and provides comprehensive report
"""

import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

def run_scraper(script_name, description):
    """Run a scraper and capture results"""
    print(f"\n{'='*60}")
    print(f"🚀 RUNNING: {script_name}")
    print(f"📋 Description: {description}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["python3", f"scripts/{script_name}"],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per scraper
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"📤 Return Code: {result.returncode}")
        
        if result.stdout:
            print(f"📄 Output:")
            print(result.stdout)
            
        if result.stderr:
            print(f"❌ Errors:")
            print(result.stderr)
            
        return {
            "script": script_name,
            "description": description,
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT: {script_name} exceeded 10 minutes")
        return {
            "script": script_name,
            "description": description,
            "duration": 600,
            "return_code": -1,
            "stdout": "",
            "stderr": "Timeout after 10 minutes",
            "success": False
        }
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            "script": script_name,
            "description": description,
            "duration": 0,
            "return_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def count_jsonl_lines(filepath):
    """Count lines in JSONL file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for line in f if line.strip())
    except:
        return 0

def analyze_output_files():
    """Analyze all output files and provide statistics"""
    print(f"\n{'='*60}")
    print(f"📊 OUTPUT FILE ANALYSIS")
    print(f"{'='*60}")
    
    cleaned_dir = Path("cleaned")
    if not cleaned_dir.exists():
        print("❌ No cleaned/ directory found")
        return {}
    
    files_analysis = {}
    total_docs = 0
    
    for jsonl_file in cleaned_dir.glob("*.jsonl"):
        line_count = count_jsonl_lines(jsonl_file)
        file_size = jsonl_file.stat().st_size
        
        files_analysis[jsonl_file.name] = {
            "documents": line_count,
            "size_bytes": file_size,
            "size_mb": file_size / (1024 * 1024)
        }
        
        total_docs += line_count
        print(f"📁 {jsonl_file.name}: {line_count:,} documents ({file_size/1024/1024:.1f} MB)")
    
    print(f"\n🎯 TOTAL DOCUMENTS: {total_docs:,}")
    return files_analysis

def generate_comprehensive_report(scraper_results, files_analysis):
    """Generate final comprehensive report"""
    print(f"\n{'='*80}")
    print(f"📋 COMPREHENSIVE LEGAL CORPUS REPORT")
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    # Scraper Summary
    print(f"\n🚀 SCRAPER EXECUTION SUMMARY:")
    print(f"{'Script':<35} {'Status':<10} {'Duration':<10} {'Description'}")
    print(f"{'-'*80}")
    
    successful = 0
    failed = 0
    total_time = 0
    
    for result in scraper_results:
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        duration = f"{result['duration']:.1f}s"
        
        print(f"{result['script']:<35} {status:<10} {duration:<10} {result['description']}")
        
        if result["success"]:
            successful += 1
        else:
            failed += 1
            
        total_time += result["duration"]
    
    print(f"\n📊 EXECUTION STATISTICS:")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total Time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    
    # Data Collection Summary
    print(f"\n📚 DATA COLLECTION SUMMARY:")
    total_documents = sum(analysis["documents"] for analysis in files_analysis.values())
    total_size_mb = sum(analysis["size_mb"] for analysis in files_analysis.values())
    
    print(f"📄 Total Documents: {total_documents:,}")
    print(f"💾 Total Size: {total_size_mb:.1f} MB")
    print(f"📁 Output Files: {len(files_analysis)}")
    
    # File Breakdown
    print(f"\n📂 FILE BREAKDOWN:")
    for filename, analysis in sorted(files_analysis.items(), key=lambda x: -x[1]["documents"]):
        print(f"  {filename}: {analysis['documents']:,} documents ({analysis['size_mb']:.1f} MB)")
    
    # Quality Assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    if total_documents >= 5000:
        print("🌟 EXCELLENT: 5000+ documents - Premium training dataset")
    elif total_documents >= 2000:
        print("🎉 VERY GOOD: 2000+ documents - High-quality training dataset")
    elif total_documents >= 1000:
        print("✅ GOOD: 1000+ documents - Solid training dataset")
    elif total_documents >= 500:
        print("👍 DECENT: 500+ documents - Adequate for basic training")
    else:
        print("⚠️  LIMITED: <500 documents - May need additional sources")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    bgh_docs = files_analysis.get("decisions_bgh.jsonl", {}).get("documents", 0)
    bverfg_docs = files_analysis.get("decisions_bverfg.jsonl", {}).get("documents", 0)
    
    if bgh_docs == 0:
        print("  🔧 BGH scraper collected 0 decisions - needs fixing")
    if bverfg_docs == 0:
        print("  🔧 BVerfG scraper collected 0 decisions - needs fixing")
    
    if total_documents >= 1000:
        print("  ✅ Ready to proceed with training preparation")
        print("  🎯 Run combine_prepare_train.py to create training sets")
    
    print(f"\n{'='*80}")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "scraper_results": scraper_results,
        "files_analysis": files_analysis,
        "summary": {
            "successful_scrapers": successful,
            "failed_scrapers": failed,
            "total_execution_time": total_time,
            "total_documents": total_documents,
            "total_size_mb": total_size_mb,
            "output_files": len(files_analysis)
        }
    }

if __name__ == "__main__":
    print(f"🚀 LEGAL CORPUS SCRAPER SUITE")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Define all scrapers to run
    scrapers = [
        ("fetch_bgh_CLEAN.py", "BGH Court Decisions (German Federal Court of Justice)"),
        ("fetch_bverfg.py", "BVerfG Court Decisions (German Constitutional Court)"),
        ("fetch_eurlex.py", "EUR-Lex EU Legal Documents"),
        ("fetch_statutes_codes_FIXED.py", "German Legal Statutes and Codes"),
        ("fetch_openlegaldata.py", "Open Legal Data API Collection"),
    ]
    
    # Run all scrapers
    scraper_results = []
    
    for script, description in scrapers:
        result = run_scraper(script, description)
        scraper_results.append(result)
        
        # Brief pause between scrapers
        time.sleep(2)
    
    # Analyze output files
    files_analysis = analyze_output_files()
    
    # Generate comprehensive report
    report = generate_comprehensive_report(scraper_results, files_analysis)
    
    # Save report to file
    report_file = Path("scraper_execution_report.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full report saved to: {report_file}")
    print(f"🏁 SCRAPER SUITE COMPLETE")