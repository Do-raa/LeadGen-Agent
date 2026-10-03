# test_warm_classifier.py

from app.agents.warm_classifier import classify_warm_lead

TEST_INPUTS = {
    "cold_1": "Not interested, thanks.",
    "cold_2": "Please remove me from your list.",
    "neutral_1": "Can you send me more details?",
    "neutral_2": "I saw your message, still thinking about it.",
    "warm_1": "That sounds interesting, I'd like to learn more.",
    "warm_2": "Yes, this could be relevant for our team.",
    "hot_1": "Let's book a call today.",
    "hot_2": "I'm very interested — can we talk ASAP?",
}

def print_result(label, text, result):
    print("------------------------------------------------------")
    print(f"📝 TEST CASE: {label}")
    print(f"Input Text: {text}")
    print("Result:")
    print(f"  Intent: {result['intent']}")
    print(f"  Score : {result['score']}")
    print(f"  Reason: {result['reason']}")
    print("------------------------------------------------------\n")


def run_tests():
    print("\n=========================================")
    print("🔍 TESTING classify_warm_lead()")
    print("=========================================\n")

    for label, text in TEST_INPUTS.items():
        result = classify_warm_lead(text)
        print_result(label, text, result)

    print("\n=========================================")
    print("✅ TESTING COMPLETE")
    print("=========================================\n")


if __name__ == "__main__":
    run_tests()
