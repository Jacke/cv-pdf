"""Constants used throughout the CV apply system."""

import re

# Bullet markers for different sections
EXP_BULLET_MARKER = "<<EXP_BULLET>> "
SKILL_BULLET_MARKER = "<<SKILL_BULLET>> "

# Technology line prefixes
TECH_PREFIXES = ("tech:", "technologies:")

# Regular expressions for content detection
URL_REGEX = re.compile(r'(?:https?://|www\.|github\.com/|linkedin\.com/|t\.me/)[^\s<>"]+')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_REGEX = re.compile(r'\+\d[\d\(\)\-\. ]{8,18}\d')

# Contact info emojis
CONTACT_EMOJIS = ["✉️", "⚒️", "🌐", "📞", "📖", "💼"]

# Section headers that should be styled as H2
SECTION_HEADERS = ["Skills", "Experience", "Entrepreneurship", "Summary", "Education", "Publications"]

# Block landmarks mapping
BLOCK_LANDMARKS = {
    "{{SUMMARY}}": "Summary",
    "{{skills}}": "Skills",
    "{{exps}}": "Experience",
    "{{entrepreneurship}}": "Entrepreneurship",
    "{{education}}": "Education",
    "{{publications}}": "Publications",
}

# Header anchors that should have tight spacing
TIGHT_ANCHORS = [
    "{{fullname}}",
    "{{title}}",
    "{{nickname}}",
    "{{timezone}}",
    "{{email}}",
    "{{github}}",
    "{{website}}",
    "{{tags}}",
    "{{phone}}",
    "{{available_for}}",
    "{{legal_entity}}"
]

# OAuth scopes for Google Docs API
GDOCS_SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.readonly",
]
