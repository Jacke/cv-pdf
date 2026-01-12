import sys
import os
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
from gdocs_cli import get_doc, ensure_access_token, load_oauth_client

def check_indices(doc_id):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    doc = get_doc(document_id=doc_id, access_token=access_token)
    
    print(f"Body range: {doc.get('body', {}).get('content', [])[0].get('startIndex')} - {doc.get('body', {}).get('content', [])[-1].get('endIndex')}")
    
    for hid, h in doc.get("headers", {}).items():
        content = h.get("content", [])
        if content:
            print(f"Header {hid} range: {content[0].get('startIndex')} - {content[-1].get('endIndex')}")

if __name__ == "__main__":
    check_indices("1v6w66RXuq4xVqQM1ZBGuB0siSLS7K3Betk_oHxvxG98")
