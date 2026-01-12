import sys
import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import get_doc, ensure_access_token, load_oauth_client

def get_all_paragraphs(content):
    paras = []
    for item in content:
        if item.get("paragraph"):
            paras.append(item)
        elif item.get("table"):
            for row in item.get("table", {}).get("tableRows", []):
                for cell in row.get("tableCells", []):
                    paras.extend(get_all_paragraphs(cell.get("content", [])))
    return paras

def dump_header(doc_id):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    doc = get_doc(document_id=doc_id, access_token=access_token)
    
    content = doc.get("body", {}).get("content", [])
    all_paras = get_all_paragraphs(content)
    
    for i, item in enumerate(all_paras[:100]):
        para = item.get("paragraph")
        elements = para.get("elements") or []
        text = "".join(el.get("textRun", {}).get("content", "") for el in elements).strip()
        if text:
            print(f"[{i}] |{text}|")

if __name__ == "__main__":
    dump_header("1v6w66RXuq4xVqQM1ZBGuB0siSLS7K3Betk_oHxvxG98")
