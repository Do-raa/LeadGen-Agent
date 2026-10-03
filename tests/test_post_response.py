import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/post_response"


def make_request(payload_dict):
    payload_str = json.dumps(payload_dict)
    response = requests.post(
        BASE_URL,
        data={"payload": payload_str},   # <-- CRITICAL FIX
        timeout=20
    )
    print("Status:", response.status_code)
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception:
        print(response.text)


def test_approve_comment_only():
    print("\n🟢 APPROVE COMMENT ONLY")

    payload = {
        "actions": [
            {"value": "approve_3"}
        ],
        "state": {
            "values": {
                "wTF4f": {
                    "comment_choice": {
                        "selected_option": { "value": "1" }
                    }
                }
            }
        }
    }

    make_request(payload)


def test_approve_comment_and_reaction():
    print("\n🟣 APPROVE COMMENT + REACTION")

    payload = {
        "actions": [
            {"value": "approve_3"}
        ],
        "state": {
            "values": {
                "wTF4f": {
                    "comment_choice": {
                        "selected_option": { "value": "2" }
                    }
                },
                "ELF6X": {
                    "reaction_choice": {
                        "selected_option": { "value": "INSIGHTFUL" }
                    }
                }
            }
        }
    }

    make_request(payload)


def test_decline():
    print("\n🔴 DECLINE")

    payload = {
        "actions": [
            {"value": "decline_3"}
        ]
    }

    make_request(payload)


if __name__ == "__main__":
    print("🚀 Running API tests...")
    test_approve_comment_only()
    test_approve_comment_and_reaction()
    test_decline()
