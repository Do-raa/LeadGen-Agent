# tests/test_social_pattern_analyzer_full.py

import json
from app.analysis.social_pattern_analyzer import SocialPatternAnalyzer

def print_section(title, content):
    print(f"\n{'=' * 30} {title} {'=' * 30}")
    print(json.dumps(content, indent=2))

def run_full_test():
    analyzer = SocialPatternAnalyzer()

    print("\n🔵 Starting FULL integration test:")
    print("Reddit API → Pattern Extraction → OpenAI GPT → Final Rules\n")

    # 1. Test Reddit scraping
    print("\n🔍 Step 1: Fetching Reddit posts...")
    reddit_posts = analyzer.scrape_reddit_top_posts(
        subreddit="GenEngineOptimization",
        limit=20
    )

    print_section("Fetched Reddit Posts", reddit_posts[:3])
    print(f"📝 Total posts fetched: {len(reddit_posts)}")

    # 2. Test statistical pattern extraction
    print("\n🔍 Step 2: Extracting statistical patterns...")
    statistical_patterns = analyzer.extract_patterns_from_reddit_data(reddit_posts)

    print_section("Statistical Patterns", statistical_patterns)

    # 3. Test GPT-enhanced rule generation
    print("\n🤖 Step 3: Calling GPT (gpt-4.1-mini) for enhanced rules...")
    final_rules = analyzer.generate_human_like_rules(
        subreddit="GenEngineOptimization"
    )

    print_section("Final GPT-Enhanced Rules", final_rules)

    print("\n🟢 FULL TEST COMPLETE — Everything worked!\n")

if __name__ == "__main__":
    run_full_test()
