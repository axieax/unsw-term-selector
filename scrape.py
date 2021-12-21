from collections import defaultdict
import json
import requests

# constants
URL = "https://www.handbook.unsw.edu.au/undergraduate/courses/2022/"
API = "https://www.handbook.unsw.edu.au/api/es/search"
FILTER_INPUTS = ["Summer Term", "Term 1", "Term 2", "Term 3", "No Filter"]

# prepare request
with open("request.json") as f:
    # TODO: choose year
    query = json.load(f)
    query["size"] = 100

# make request
response = requests.get(API, json=query)
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

# print
print(f"Filter: {TERM}")
print("Code\tName\tTerms")
for course in courses:
    print(f"{course['code']}\t{course['name']}\t{', '.join(course['terms'])}")
    print(URL + course["code"])
