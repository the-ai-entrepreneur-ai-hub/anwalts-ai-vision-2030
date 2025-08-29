#!/usr/bin/env python3
"""
Add document generation endpoint to backend main.py properly
"""

import os

def add_document_endpoint():
    """Add document generation endpoint to main.py"""
    
    main_py_path = "/var/www/portal-anwalts.ai/backend/main.py"
    
    # Read current main.py
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Check if endpoint already exists
    if "/api/ai/generate-document-simple" in content:
        print("✅ Document endpoint already exists")
        return True
    
    # Add datetime import if not present
    if "from datetime import datetime" not in content:
        content = content.replace("from typing import Optional", "from typing import Optional\nfrom datetime import datetime")
    
    # Add the endpoint before the last line
    endpoint_code = '''
# Document Generation Endpoint  
@app.post("/api/ai/generate-document-simple")
async def generate_document_simple(request: dict):
    """Generate document using AI"""
    try:
        title = request.get('title', 'Untitled Document')
        document_type = request.get('document_type', 'general')
        prompt = request.get('prompt', f'Create a {document_type} document with title: {title}')
        
        # Simulate AI document generation
        content = f"""# {title}

## Dokumenttyp: {document_type.title()}

**Erstellt am:** {datetime.now().strftime('%d.%m.%Y %H:%M')}

---

## Inhalt

Dies ist ein automatisch generiertes Dokument basierend auf Ihren Anforderungen.

### Wichtige Punkte:
- Dokument wurde mit AnwaltsAI erstellt
- Typ: {document_type}
- Titel: {title}

### Rechtliche Hinweise:
Dieses Dokument wurde automatisch erstellt und sollte von einem Rechtsanwalt geprüft werden.

---

**Generiert von AnwaltsAI**"""
        
        return {
            "success": True,
            "content": content,
            "title": title,
            "document_type": document_type,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

'''
    
    # Add endpoint to the file
    content = content.rstrip() + endpoint_code
    
    # Write back to file
    with open(main_py_path, 'w') as f:
        f.write(content)
    
    print("✅ Document generation endpoint added to main.py")
    return True

if __name__ == "__main__":
    add_document_endpoint()