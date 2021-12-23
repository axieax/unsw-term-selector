"""Library Imports"""
from collections import defaultdict
import json
import requests

# override defaults
def get_input(prompt, cast=str, default=None):
    """
    Get user input

    :param prompt: prompt to display
    :param cast: type to cast input to
    :param default: default value
    """
    try:
        return cast(input(prompt))
    except (ValueError, EOFError, TypeError):
        return default


print("Override or accept defaults (<CR>)")
DEFAULT_YEAR = 2022
YEAR = get_input(f"Year (default {DEFAULT_YEAR}): ", int, DEFAULT_YEAR)
DEFAULT_SUBJECT_AREA = "COMP"
SUBJECT_AREA = get_input(
    f"Subject area (default {DEFAULT_SUBJECT_AREA}): ", str, DEFAULT_SUBJECT_AREA
)
DEFAULT_LIMIT = 200
LIMIT = get_input(f"Query limit (default {DEFAULT_LIMIT}): ", int, DEFAULT_LIMIT)

# constants
URL = f"https://www.handbook.unsw.edu.au/undergraduate/courses/{YEAR}/"
API = "https://www.handbook.unsw.edu.au/api/es/search"
FILTER_INPUTS = ["Summer Term", "Term 1", "Term 2", "Term 3", "No Filter"]

# prepare request (elastic search)
request = {
    "query": {
        "bool": {
            "must": [
                {"term": {"live": True}},
                [
                    {
                        "bool": {
                            "minimum_should_match": "100%",
                            "should": [
                                {
                                    "query_string": {
                                        "fields": ["unsw_psubject.implementationYear"],
                                        "query": f"*{YEAR}*",
                                    }
                                }
                            ],
                        }
                    },
                    {
                        "bool": {
                            "minimum_should_match": "100%",
                            "should": [
                                {
                                    "query_string": {
                                        "fields": ["unsw_psubject.studyLevelValue"],
                                        "query": "*ugrd*",
                                    }
                                }
                            ],
                        }
                    },
                    {
                        "bool": {
                            "minimum_should_match": "100%",
                            "should": [
                                {
                                    "query_string": {
                                        "fields": ["unsw_psubject.active"],
                                        "query": "*1*",
                                    }
                                }
                            ],
                        }
                    },
                    {
                        "bool": {
                            "minimum_should_match": "100%",
                            "should": [
                                {
                                    "query_string": {
                                        "fields": ["unsw_psubject.educationalArea"],
                                        "query": f"*{SUBJECT_AREA}*",
                                    }
                                }
                            ],
                        }
                    },
                ],
            ],
            "filter": [{"terms": {"contenttype": ["unsw_psubject"]}}],
        }
    },
    "sort": [{"unsw_psubject.code_dotraw": {"order": "asc"}}],
    "from": 0,
    "size": LIMIT,
    "track_scores": True,
    "_source": {"includes": ["*.code", "*.name"], "excludes": ["", None]},
}

# make request
response = requests.get(API, json=request)
payload = response.json()

# parse response
results = defaultdict(list)
names = {}
for course_json in payload.get("contentlets", []):
    course_data = json.loads(course_json["data"])
    terms = tuple(course_data["offering_detail"]["offering_terms"].split(", "))
    course = {
        "code": course_data["code"],
        "name": course_data["title"],
        "terms": terms,
    }
    for TERM in terms:
        results[TERM].append(course)

# filter results
try:
    OPTION = int(
        input(
            "Filter courses by term:\n"
            + "\n".join(f"\t{i}. {x}" for i, x in enumerate(FILTER_INPUTS))
            + "\n"
        )
    )
except (EOFError, ValueError):
    OPTION = len(FILTER_INPUTS) - 1

TERM = FILTER_INPUTS[OPTION]
if TERM == FILTER_INPUTS[-1]:
    courses = set()
    for course in results.values():
        courses.update(course)
    courses = list(sorted(courses))
else:
    courses = results[TERM]

# display results
print(f">> Filter: {TERM}")
print("Code\tName\tTerms")
for course in courses:
    print(f"{course['code']}\t{course['name']}\t{', '.join(course['terms'])}")
    print(URL + course["code"])
