import requests
import json

# This mimics what React will eventually do
test_student_data = {
    "rank": 5000,
    "preferences": {
        "placement_score": 9.0,
        "higher_study_score": 5.0,
        "gov_exam_score": 3.0,
        "coding_env_score": 9.0,
        "faculty_score": 7.0,
        "college_life_score": 8.0,
        "sports_score": 6.0
    }
}

print("Sending order to the Flask Waiter...\n")
response = requests.post('http://localhost:5000/api/recommend', json=test_student_data)

print("Status Code:", response.status_code)
print("\n--- AI Recommendations ---")
print(json.dumps(response.json(), indent=4))