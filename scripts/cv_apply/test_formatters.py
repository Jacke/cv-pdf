"""
Example unit tests for formatters module.

Run with: python -m pytest test_formatters.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cv_apply.formatters import (
    format_summary,
    format_skills,
    format_education,
    format_publications,
    is_entrepreneurship,
    format_experience_block,
    build_replacements,
)


def test_format_summary_string():
    """Test formatting summary when it's a simple string."""
    data = {"summary": "Software engineer with 10 years of experience"}
    result = format_summary(data)
    assert result == "Software engineer with 10 years of experience"


def test_format_summary_object():
    """Test formatting summary when it's an object with paragraph and about."""
    data = {
        "summary": {
            "paragraph": "Experienced developer",
            "about": "Passionate about clean code"
        }
    }
    result = format_summary(data)
    assert "Experienced developer" in result
    assert "Passionate about clean code" in result


def test_format_skills_single():
    """Test formatting a single skill with bullets."""
    data = {
        "skills": {
            "title": "Programming Languages",
            "bullets": ["Python", "JavaScript", "Go"]
        }
    }
    result = format_skills(data)
    assert "Programming Languages" in result
    assert "<<SKILL_BULLET>> Python" in result
    assert "<<SKILL_BULLET>> JavaScript" in result
    assert "<<SKILL_BULLET>> Go" in result


def test_format_skills_multiple():
    """Test formatting multiple skill categories."""
    data = {
        "skills": [
            {
                "title": "Languages",
                "bullets": ["Python", "JavaScript"]
            },
            {
                "title": "Frameworks",
                "bullets": ["Django", "React"]
            }
        ]
    }
    result = format_skills(data)
    assert "Languages" in result
    assert "Frameworks" in result
    assert "<<SKILL_BULLET>> Python" in result
    assert "<<SKILL_BULLET>> Django" in result


def test_is_entrepreneurship():
    """Test entrepreneurship detection."""
    assert is_entrepreneurship({"role": "Co-Founder & CTO"}) is True
    assert is_entrepreneurship({"role": "Founder"}) is True
    assert is_entrepreneurship({"role": "CEO"}) is True
    assert is_entrepreneurship({"role": "Senior Software Engineer"}) is False
    assert is_entrepreneurship({"role": "Tech Lead"}) is False


def test_format_experience_block():
    """Test formatting a single experience block."""
    item = {
        "company": "Tech Corp",
        "dates": "2020-2023",
        "duration": "3 years",
        "role": "Senior Engineer",
        "employment": "Full-time",
        "bullets": [
            "Built scalable systems",
            "Led team of 5 engineers"
        ],
        "technologies": "Python, Django, PostgreSQL"
    }
    result = format_experience_block(item)
    assert "Tech Corp" in result
    assert "(2020-2023)" in result
    assert "Senior Engineer / Full-time" in result
    assert "<<EXP_BULLET>> Built scalable systems" in result
    assert "<<EXP_BULLET>> Led team of 5 engineers" in result
    assert "Tech: Python, Django, PostgreSQL" in result


def test_format_education_single():
    """Test formatting single education entry."""
    data = {
        "education": {
            "dates": "2015-2019",
            "school": "MIT",
            "degree": "B.S. Computer Science"
        }
    }
    result = format_education(data)
    assert "2015-2019" in result
    assert "MIT" in result
    assert "B.S. Computer Science" in result


def test_format_education_list():
    """Test formatting multiple education entries."""
    data = {
        "education": [
            {
                "dates": "2015-2019",
                "school": "MIT",
                "degree": "B.S. Computer Science"
            },
            {
                "dates": "2019-2021",
                "school": "Stanford",
                "degree": "M.S. Computer Science"
            }
        ]
    }
    result = format_education(data)
    assert "MIT" in result
    assert "Stanford" in result
    assert "B.S." in result
    assert "M.S." in result


def test_format_publications_list():
    """Test formatting publications as list."""
    data = {
        "publications": [
            "Deep Learning Paper (2021)",
            "Scalable Systems Architecture (2022)"
        ]
    }
    result = format_publications(data)
    assert "- Deep Learning Paper (2021)" in result
    assert "- Scalable Systems Architecture (2022)" in result


def test_format_publications_string():
    """Test formatting publications as string."""
    data = {
        "publications": "See my profile for publications"
    }
    result = format_publications(data)
    assert result == "See my profile for publications"


def test_build_replacements_complete():
    """Test building complete replacements dictionary."""
    data = {
        "header": {
            "full_name": "John Doe",
            "role_title": "Senior Software Engineer",
            "nickname": "johndoe",
            "contact": {
                "email": "john@example.com",
                "github": "github.com/johndoe",
                "phone": "+1234567890"
            }
        },
        "summary": "Experienced developer",
        "skills": {
            "title": "Languages",
            "bullets": ["Python", "JavaScript"]
        },
        "experience": [
            {
                "company": "Tech Corp",
                "role": "Engineer",
                "bullets": ["Built systems"]
            }
        ],
        "education": {
            "school": "MIT",
            "degree": "B.S. CS"
        }
    }

    replacements = build_replacements(data)

    # Check header fields
    assert replacements["{{fullname}}"] == "John Doe"
    assert replacements["{{title}}"] == "Senior Software Engineer"
    assert "john@example.com" in replacements["{{email}}"]

    # Check content sections
    assert replacements["{{SUMMARY}}"] == "Experienced developer"
    assert "Languages" in replacements["{{skills}}"]
    assert "Tech Corp" in replacements["{{exps}}"]
    assert "MIT" in replacements["{{education}}"]


def test_empty_data_handling():
    """Test handling of empty/missing data."""
    data = {}
    replacements = build_replacements(data)

    # Should not crash, should return empty strings
    assert replacements["{{fullname}}"] == ""
    assert replacements["{{SUMMARY}}"] == ""
    assert replacements["{{skills}}"] == ""


if __name__ == "__main__":
    # Simple test runner if pytest is not available
    import traceback

    tests = [
        test_format_summary_string,
        test_format_summary_object,
        test_format_skills_single,
        test_format_skills_multiple,
        test_is_entrepreneurship,
        test_format_experience_block,
        test_format_education_single,
        test_format_education_list,
        test_format_publications_list,
        test_format_publications_string,
        test_build_replacements_complete,
        test_empty_data_handling,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1
        except Exception as e:
            print(f"💥 {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Tests: {passed} passed, {failed} failed")
    print(f"{'='*50}")

    sys.exit(0 if failed == 0 else 1)
