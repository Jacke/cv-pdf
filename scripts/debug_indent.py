import sys
import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import get_doc, ensure_access_token, load_oauth_client

def get_indent_stats(doc_id):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    doc = get_doc(document_id=doc_id, access_token=access_token)
    
    content = doc.get("body", {}).get("content", [])
    
    print(f"--- Indentation Styles for Bullet Lists in {doc_id} ---")
    
    for item in content:
        if not item.get("paragraph"):
            continue
            
        para = item.get("paragraph")
        bullet = para.get("bullet")
        
        # Only check paragraphs that are part of a list
        if bullet:
            elements = para.get("elements") or []
            text = "".join(el.get("textRun", {}).get("content", "") for el in elements).strip()
            style = para.get("paragraphStyle") or {}
            
            indent_start = style.get("indentStart", {}).get("magnitude", "N/A")
            indent_first = style.get("indentFirstLine", {}).get("magnitude", "N/A")
            
            print(f"ListId: {bullet.get('listId')} | Start: {indent_start}pt | First: {indent_first}pt | Text: {text[:40]}...")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", required=True, help="Document ID")
    args = parser.parse_args()
    
    get_indent_stats(args.doc)
