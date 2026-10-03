import requests
import json

URL = "http://127.0.0.1:8000/api/post_response"
# If using docker-based n8n: URL = "http://host.docker.internal:8000/api/post_response"

# -----------------------------
# CHANGE THESE FOR TEST CASES
# -----------------------------

TEST_CASE = "approve_no_comment"
# Options:
# "approve_no_comment"
# "approve_with_comment"
# "decline"
# "random"


def build_payload(case):
    base = {
        "type": "block_actions",
        "user": {"id": "U123", "username": "test-user"},
        "actions": [],
        "state": {
            "values": {
                "RUNxm": {
                    "comment_choice": {
                        "type": "radio_buttons",
                        "selected_option": None
                    }
                },
                "UGDZ/": {
                    "reaction_choice": {
                        "type": "radio_buttons",
                        "selected_option": None
                    }
                }
            }
        }
    }

    if case == "approve_no_comment":
        base["actions"] = [
            {"action_id": "approve_button", "value": "approve_123"}
        ]
    
    elif case == "approve_with_comment":
        base["actions"] = [
            {"action_id": "approve_button", "value": "approve_123"}
        ]
        base["state"]["values"]["RUNxm"]["comment_choice"]["selected_option"] = {
            "text": {"type": "plain_text", "text": "Third option"},
            "value": "3"
        }
        base["state"]["values"]["UGDZ/"]["reaction_choice"]["selected_option"] = {
            "text": {"type": "plain_text", "text": "Like"},
            "value": "like"
        }

    elif case == "decline":
        base["actions"] = [
            {"action_id": "decline_button", "value": "decline_123"}
        ]

    elif case == "random":
        base["actions"] = [
            {"action_id": "random_action", "value": "hello"}
        ]

    return {"payload": base}


def run_test():
    payload = build_payload(TEST_CASE)
    print("\n🔵 Sending Test Case:", TEST_CASE)
    print("Payload:", json.dumps(payload, indent=2))

    response = requests.post(URL, json=payload)
    print("\n🟢 Response Status:", response.status_code)
    try:
        print("🟢 Response JSON:", response.json())
    except:
        print("🟡 Raw Response:", response.text)


if __name__ == "__main__":
    run_test()
