import sys
import os
import argparse

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import get_doc, ensure_access_token, load_oauth_client

def get_heading_level(para):
    style = para.get("paragraphStyle", {}).get("namedStyleType", "NORMAL_TEXT")
    if style.startswith("HEADING_"):
        return int(style.split("_")[1])
    return 0

def list_h2(doc_name):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    doc = get_doc(document_id=doc_name, access_token=access_token)
    
    print(f"H2 headers in '{doc_name}':")
    count = 0
    for item in doc.get("body", {}).get("content", []):
        if item.get("paragraph"):
            lvl = get_heading_level(item.get("paragraph"))
            if lvl > 0:
                count += 1
                text = "".join(el.get("textRun", {}).get("content", "") for el in item.get("paragraph").get("elements", []))
                print(f"[{lvl}] |{text.strip()}|")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", required=True)
    args = parser.parse_args()
    list_h2(args.doc)
