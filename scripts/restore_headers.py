import sys
import os
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import docs_batch_update, ensure_access_token, load_oauth_client

def restore_headers(doc_id):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    
    requests = [
        {"replaceAllText": {"containsText": {"text": "{{SUMMARY}}", "matchCase": True}, "replaceText": "{{SUMMARY}}\nSkills"}},
        {"replaceAllText": {"containsText": {"text": "{{skills}}", "matchCase": True}, "replaceText": "{{skills}}\nExperience"}},
        {"replaceAllText": {"containsText": {"text": "{{exps}}", "matchCase": True}, "replaceText": "{{exps}}\nEntrepreneurship"}},
        {"replaceAllText": {"containsText": {"text": "{{entrepreneurship}}", "matchCase": True}, "replaceText": "{{entrepreneurship}}\nEducation"}},
    ]
    # Wait, if I do this, it will result in "{{SUMMARY}}\nSkills\nSkills" if I run it twice.
    # So I should be careful.
    
    docs_batch_update(document_id=doc_id, access_token=access_token, requests=requests)

if __name__ == "__main__":
    restore_headers("1v6w66RXuq4xVqQM1ZBGuB0siSLS7K3Betk_oHxvxG98")
