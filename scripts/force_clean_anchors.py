import sys
import os
import json
import re

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from gdocs_cli import get_doc, ensure_access_token, load_oauth_client, docs_batch_update

def clean_all_anchors(doc_id):
    client = load_oauth_client(".secrets/google-oauth-client.json")
    access_token = ensure_access_token(client=client, token_path=".secrets/google-token.json")
    
    # We want to restore the doc to the "Gold Standard" state.
    # We'll use a series of replacements to fix common corruptions.
    requests = [
        {"replaceAllText": {"containsText": {"text": "{{website}}::::", "matchCase": True}, "replaceText": "{{website}}"}},
        {"replaceAllText": {"containsText": {"text": "{{website}}:::", "matchCase": True}, "replaceText": "{{website}}"}},
        {"replaceAllText": {"containsText": {"text": "{{website}}::", "matchCase": True}, "replaceText": "{{website}}"}},
        {"replaceAllText": {"containsText": {"text": "{{website}}:", "matchCase": True}, "replaceText": "{{website}}"}},
        
        # Merge issues
        {"replaceAllText": {"containsText": {"text": "{{SUMMARY}}Skills", "matchCase": True}, "replaceText": "{{SUMMARY}}\nSkills"}},
        {"replaceAllText": {"containsText": {"text": "{{skills}}Experience", "matchCase": True}, "replaceText": "{{skills}}\nExperience"}},
        {"replaceAllText": {"containsText": {"text": "{{exps}}Entrepreneurship", "matchCase": True}, "replaceText": "{{exps}}\nEntrepreneurship"}},
        {"replaceAllText": {"containsText": {"text": "{{entrepreneurship}}Education", "matchCase": True}, "replaceText": "{{entrepreneurship}}\nEducation"}},
        
        # Duplicates at the end
        {"replaceAllText": {"containsText": {"text": "{{education}}\n{{education}}", "matchCase": True}, "replaceText": "{{education}}"}},
    ]
    
    docs_batch_update(document_id=doc_id, access_token=access_token, requests=requests)

if __name__ == "__main__":
    clean_all_anchors("1v6w66RXuq4xVqQM1ZBGuB0siSLS7K3Betk_oHxvxG98")
