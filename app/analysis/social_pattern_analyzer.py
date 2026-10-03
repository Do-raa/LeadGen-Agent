# app/analysis/social_pattern_analyzer.py

import requests
from openai import OpenAI
from sqlalchemy import create_engine
import json
from ..utils.config import OPENAI_API_KEY, DATABASE_URL
from cachetools import TTLCache
import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class SocialPatternAnalyzer:
    """
    Main analyzer class containing:
    - Reddit scraping
    - Text pattern extraction
    - AI pattern synthesis (using gpt-4o-mini)
    - Caching for speed
    """

    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.client = OpenAI(api_key=OPENAI_API_KEY)

        # CACHE
        self.patterns_cache = TTLCache(maxsize=10, ttl=3600)  # 1 hour
        self.reddit_cache = TTLCache(maxsize=10, ttl=600)     # 10 minutes

    # ----------------------------------------------------------------------
    # CACHING HELPERS
    # ----------------------------------------------------------------------

    def get_cached_patterns(self, subreddit: str) -> Optional[Dict]:
        return self.patterns_cache.get(f"patterns_{subreddit}")

    def cache_patterns(self, subreddit: str, patterns: Dict):
        self.patterns_cache[f"patterns_{subreddit}"] = patterns

    def get_cached_reddit_data(self, subreddit: str, limit: int):
        return self.reddit_cache.get(f"reddit_{subreddit}_{limit}")

    def cache_reddit_data(self, subreddit: str, limit: int, data: List):
        self.reddit_cache[f"reddit_{subreddit}_{limit}"] = data

    # ----------------------------------------------------------------------
    # REDDIT SCRAPER
    # ----------------------------------------------------------------------

    def scrape_reddit_top_posts(
        self, subreddit: str = "GenEngineOptimization", limit: int = 30
    ) -> List[Dict]:

        cached = self.get_cached_reddit_data(subreddit, limit)
        if cached:
            return cached

        try:
            url = (
                f"https://api.pushshift.io/reddit/search/"
                f"submission/?subreddit={subreddit}&size={limit}&sort=desc&score=>10"
            )
            response = requests.get(url, timeout=15)

            if response.status_code != 200:
                # fallback to Reddit API
                fallback = f"https://www.reddit.com/r/{subreddit}/top/.json?limit={limit}&t=week"
                response = requests.get(
                    fallback, timeout=15,
                    headers={"User-Agent": "PatternAnalyzer/1.0"}
                )

                if response.status_code != 200:
                    raise Exception(f"Reddit returned {response.status_code}")

                posts = [c["data"] for c in response.json()["data"]["children"]]

            else:
                posts = response.json().get("data", [])

            enhanced = []
            for post in posts:
                if post.get("score", 0) < 10:
                    continue

                combined_text = f"{post.get('title','')} {post.get('selftext','')}"
                record = {
                    "title": post.get("title", ""),
                    "selftext": post.get("selftext", "")[:500],
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                    "text_length": len(combined_text),
                    "question_count": combined_text.count("?"),
                    "exclamation_count": combined_text.count("!"),
                    "has_media": bool(
                        post.get("media")
                        or str(post.get("url", "")).endswith((".jpg", ".png", ".gif"))
                    ),
                }
                enhanced.append(record)

            self.cache_reddit_data(subreddit, limit, enhanced)
            return enhanced

        except Exception as e:
            logger.error(f"Reddit scraping failed: {e}")
            return []

    # ----------------------------------------------------------------------
    # PATTERN ANALYTICS
    # ----------------------------------------------------------------------

    def extract_patterns_from_reddit_data(self, posts: List[Dict]) -> Dict:
        if not posts:
            return self.get_fallback_patterns()

        titles = [p["title"] for p in posts]
        text = " ".join([p["title"] + " " + p.get("selftext", "") for p in posts])

        stats = {
            "title_patterns": self._analyze_title_patterns(titles),
            "common_phrases": self._extract_common_phrases(text),
            "emotional_indicators": self._extract_emotional_words(text),
        }

        return stats

    def _analyze_title_patterns(self, titles: List[str]) -> Dict:
        patterns = {
            "starts_with_question": sum(t.lower().startswith(("how", "why", "what")) for t in titles),
            "contains_numbers": sum(any(ch.isdigit() for ch in t) for t in titles),
            "common_starters": Counter(t.split()[0].lower() for t in titles if t).most_common(5),
        }
        return patterns

    def _extract_common_phrases(self, text: str) -> List[str]:
        words = text.split()
        counts = Counter(" ".join(words[i:i+3]).lower() for i in range(len(words)-3))
        return [p for p, c in counts.most_common(10) if c > 1]

    def _extract_emotional_words(self, text: str) -> List[str]:
        emotional = {
            "frustrated", "excited", "amazing", "terrible", "awesome",
            "hate", "love", "breakthrough", "disappointed"
        }
        return list({w for w in text.lower().split() if w in emotional})

    # ----------------------------------------------------------------------
    # AI-POWERED PATTERN GENERATION
    # ----------------------------------------------------------------------

    def generate_human_like_rules(
        self, subreddit: str = "GenEngineOptimization"
    ) -> Dict:

        cached = self.get_cached_patterns(subreddit)
        if cached:
            return cached

        posts = self.scrape_reddit_top_posts(subreddit)
        stats = self.extract_patterns_from_reddit_data(posts)

        summary = json.dumps(stats, indent=2)

        prompt = f"""
        You are an expert writing-pattern analyst.

        Reddit dataset summary:
        {summary}

        Using this data, generate JSON with:
        - data_insights
        - title_formulas
        - content_patterns
        - emotional_triggers
        - optimal_length (object)
        - question_strategies
        - common_mistakes
        - industry_terms

        Make all rules highly actionable and data-backed.
        RETURN ONLY VALID JSON.
        """

        try:
            response = self.client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                max_output_tokens=800,
                temperature=0.4
            )

            raw = response.output_text.strip()

            # Safety: clean code fences if GPT adds them
            raw = raw.replace("```json", "").replace("```", "").strip()

            rules = json.loads(raw)

            final = {
                **rules,
                "statistical_patterns": stats,
                "posts_analyzed": len(posts),
                "analysis_date": datetime.now().isoformat(),
            }

            self.cache_patterns(subreddit, final)
            return final

        except Exception as e:
            logger.error(f"AI rule-generation failed: {e}")
            return self.get_fallback_patterns()

    # ----------------------------------------------------------------------
    # FALLBACKS
    # ----------------------------------------------------------------------

    def get_fallback_patterns(self) -> Dict:
        return {
            "sentence_variation": "Mix short punchy sentences with longer explanatory ones",
            "emotional_triggers": ["curiosity", "excitement", "pain points"],
            "industry_jargon": ["GEO", "AI search", "signal", "SERP"],
            "question_patterns": ["How do you handle...", "Why does...", "Anyone else noticing..."],
            "avoid_generic": ["I hope this helps", "Let me know"],
        }
