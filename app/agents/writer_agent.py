# app/agents/writer_agent.py

import random
import json
import re
import unicodedata
import statistics
from collections import Counter
from typing import Dict, Any

from openai import OpenAI
from sqlalchemy.orm import Session

from ..db.models import LinkedInPost, Comment
from ..utils.config import OPENAI_API_KEY
from ..analysis.social_pattern_analyzer import SocialPatternAnalyzer


# CORE: mapping emoji -> LinkedIn reaction code for Unipile
REACTION_MAP = {
    "👏": "CELEBRATE",
    "💡": "INSIGHTFUL",
    "🔥": "FIRE",
    "🚀": "SUPPORT",
}

PERSONA_STYLES: Dict[str, str] = {
    "friendly": (
        "Warm, supportive, collaborative. Use simple language, be encouraging, "
        "never condescending, and keep it human and approachable."
    ),
    "expert": (
        "Confident but humble, concise, adds one concrete insight, framework, or nuance. "
        "No hype, no exaggeration."
    ),
    "challenger": (
        "Respectful but provocative. Gently question assumptions or expose a blind spot, "
        "without being rude or arrogant."
    ),
    "analytical": (
        "Calm, structured, and focused on mechanisms, causes, or metrics. "
        "Avoid fluff and emotional exaggeration."
    ),
}


class HumanLikeWriter:
    def __init__(self, db: Session = None):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.pattern_analyzer = SocialPatternAnalyzer()
        # Global rules from Reddit / data patterns
        self.global_rules = self.pattern_analyzer.generate_human_like_rules()
        self.db = db

        # Simple in-memory incremental learning (non-persistent)
        self.stats = {
            "total_comments": 0,
            "persona_counts": Counter(),
            "intent_counts": Counter(),
        }

    # ------------------------------------------------------------------
    # TEXT CLEANING
    # ------------------------------------------------------------------
    def clean_text(self, text: str) -> str:
        """
        Sanitize generated comments so they are Slack/LinkedIn-safe.
        Keeps emojis but removes dangerous punctuation and markdown.
        """
        if not text:
            return ""

        # Normalize fancy unicode
        text = unicodedata.normalize("NFKC", text)

        # Remove hashtags (#AI -> AI)
        text = re.sub(r"#\w+", "", text)

        # Remove leading/trailing quotes
        text = text.strip()
        text = re.sub(r'^[\'"“”]+', "", text)
        text = re.sub(r'[\'"“”]+$', "", text)

        # Strip markdown symbols
        text = text.replace("*", "").replace("_", "").replace("`", "")

        # Normalize dashes
        text = text.replace("–", "-").replace("—", "-")

        # Collapse whitespace
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()

    # ------------------------------------------------------------------
    # POST-LEVEL COMMENT LEARNING (ONLY THIS POST’S COMMENTS)
    # ------------------------------------------------------------------
    def learn_from_post_comments(self, comments: list[Comment]) -> Dict[str, Any]:
        """
        Analyze ONLY the comments of ONE LinkedIn post.
        `comments` must be a list of Comment objects from LinkedInPost.comments.
        """
        if not comments or len(comments) == 0:
            return {
                "tone": "balanced",
                "emoji_usage": 0.1,
                "avg_length": 140,
                "question_rate": 0.1,
                "keywords": [],
            }

        # Extract text of all comments
        texts = [c.comment_text for c in comments if c.comment_text and c.comment_text.strip()]

        if not texts:
            return {
                "tone": "balanced",
                "emoji_usage": 0.1,
                "avg_length": 140,
                "question_rate": 0.1,
                "keywords": [],
            }

        lengths = [len(t) for t in texts]
        avg_length = statistics.mean(lengths)

        # Emoji usage in thread
        emoji_count = sum(
            t.count("🔥") + t.count("👏") + t.count("💡") + t.count("🚀")
            for t in texts
        )
        emoji_usage = emoji_count / len(texts)

        # Question mark frequency
        question_count = sum(1 for t in texts if "?" in t)
        question_rate = question_count / len(texts)

        # Extract common keywords from thread
        words = " ".join(texts).lower().split()
        common_words = [
            w for w, _ in Counter(words).most_common(20)
            if len(w) > 4 and w.isalpha()
        ]

        # Determine tone
        if emoji_usage > 0.3:
            tone = "energetic"
        elif avg_length < 80:
            tone = "short_direct"
        elif question_rate > 0.25:
            tone = "curious"
        else:
            tone = "balanced"

        return {
            "tone": tone,
            "emoji_usage": emoji_usage,
            "avg_length": avg_length,
            "question_rate": question_rate,
            "keywords": common_words,
        }

    # ------------------------------------------------------------------
    # POST INTENT CLASSIFICATION (AI / SALES / MINDSET / OTHER)
    # ------------------------------------------------------------------
    def classify_post_intent(self, text: str) -> str:
        """
        Detect the main intent category of a post: AI, sales, mindset, business, other.
        Uses GPT with a tiny, cheap call, plus a fallback heuristic.
        """
        text_snippet = text[:600]

        prompt = f"""
You must answer with exactly ONE label from this list:
AI, sales, business, mindset, marketing, operations, other

Choose the label that best describes the MAIN topic of this LinkedIn post.

Post:
{text_snippet}
"""
        try:
            resp = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                max_output_tokens=10,
            )
            raw = resp.output_text.strip().lower()
            label = raw.split()[0].strip(",. ")

            allowed = {
                "ai", "sales", "business", "mindset",
                "marketing", "operations", "other",
            }
            if label not in allowed:
                return "other"
            return label

        except Exception:
            # Fallback simple keyword-based classifier
            lower = text.lower()
            if any(k in lower for k in ["llm", "chatgpt", "openai", "ai ", "gpt"]):
                return "ai"
            if any(k in lower for k in ["lead", "pipeline", "prospect", "outbound", "close rate"]):
                return "sales"
            if any(k in lower for k in ["mindset", "growth", "discipline", "habits", "motivation"]):
                return "mindset"
            if any(k in lower for k in ["campaign", "copy", "conversion", "funnel"]):
                return "marketing"
            return "business"

    # ------------------------------------------------------------------
    # SENTIMENT / ENERGY ANALYSIS (HEURISTIC)
    # ------------------------------------------------------------------
    def analyze_post_sentiment(self, text: str) -> str:
        """
        Very light heuristic sentiment: positive / neutral / negative.
        Good enough to choose reactions, no extra GPT needed.
        """
        lower = text.lower()
        positive_words = [
            "great", "love", "excited", "amazing", "awesome", "win", "progress",
            "improve", "improved", "improving", "breakthrough", "happy", "grateful",
        ]
        negative_words = [
            "frustrated", "hate", "stuck", "annoying", "problem", "issue",
            "broken", "worried", "concerned", "tired", "overwhelmed",
        ]

        score = 0
        for w in positive_words:
            if w in lower:
                score += 1
        for w in negative_words:
            if w in lower:
                score -= 1

        if "!" in text:
            score += 0.5

        if score > 1:
            return "positive"
        if score < -1:
            return "negative"
        return "neutral"

    # ------------------------------------------------------------------
    # PERSONA + TONE INSTRUCTIONS
    # ------------------------------------------------------------------
    def build_tone_instructions(self, persona: str, global_rules: Dict, local_context: Dict, intent: str) -> str:
        persona_key = persona if persona in PERSONA_STYLES else "friendly"
        persona_desc = PERSONA_STYLES[persona_key]

        pieces = [f"Persona: {persona_key}. {persona_desc}"]

        # Use emotional triggers from global rules
        triggers = global_rules.get("emotional_triggers", [])
        if triggers:
            pieces.append(f"Tap lightly into emotions like: {', '.join(triggers[:3])}.")

        # Local thread tone
        tone = local_context.get("tone", "balanced")
        if tone == "energetic":
            pieces.append("Match an energetic, upbeat thread.")
        elif tone == "curious":
            pieces.append("Match a curious, exploratory thread.")
        elif tone == "short_direct":
            pieces.append("Keep it concise and direct like the other comments.")
        else:
            pieces.append("Maintain a balanced, conversational tone.")

        # Intent-specific hint
        if intent == "ai":
            pieces.append("Write as someone comfortable with AI and practical implementation.")
        elif intent == "sales":
            pieces.append("Write as someone who understands pipeline, deals, and real-world sales constraints.")
        elif intent == "mindset":
            pieces.append("Write with a reflective but grounded mindset angle, no fake motivation.")
        elif intent == "marketing":
            pieces.append("Subtly show understanding of messaging, positioning, and experiments.")
        # business/operations/other: no special addition, already covered by general persona

        # Thread keywords (from comments)
        keywords = local_context.get("keywords") or []
        if keywords:
            pieces.append(f"Optionally echo one natural keyword like '{keywords[0]}' if it fits.")

        return " ".join(pieces)

    # ------------------------------------------------------------------
    # REACTION SELECTION BASED ON SENTIMENT + INTENT
    # ------------------------------------------------------------------
    def pick_reactions(self, sentiment: str, intent: str, local_context: Dict) -> list:
        """
        Choose 2 reaction emojis based on post sentiment, topic intent, and thread energy.
        """
        base_pool = []

        # Sentiment-based weighting
        if sentiment == "positive":
            base_pool += ["👏", "🚀", "🔥", "💡"]
        elif sentiment == "negative":
            # More supportive / thoughtful
            base_pool += ["💡", "👏", "🚀"]
        else:  # neutral
            base_pool += ["💡", "👏", "🚀"]

        # Intent adjustments
        if intent == "ai":
            base_pool += ["💡", "🚀"]
        elif intent == "sales":
            base_pool += ["🔥", "🚀", "👏"]
        elif intent == "mindset":
            base_pool += ["💡", "👏"]
        # marketing / business / other just keep base_pool

        # Thread emoji usage: if people already use emojis a lot, we can be more expressive
        if local_context.get("emoji_usage", 0.0) > 0.3:
            base_pool += ["🔥", "🚀", "👏"]

        # Make unique
        unique = list(set(base_pool))
        if len(unique) >= 2:
            chosen = random.sample(unique, 2)
        elif unique:
            chosen = unique + ["💡"]
        else:
            chosen = ["👏", "💡"]

        # Map to Unipile reaction codes
        return [
            {"emoji": e, "code": REACTION_MAP.get(e, "LIKE")}
            for e in chosen
        ]

    # ------------------------------------------------------------------
    # PUBLIC ENTRYPOINT: GENERATE OPTIONS FOR A GIVEN POST
    # ------------------------------------------------------------------
    def generate_comment_options(self, post_id: int, persona: str = "friendly") -> Dict[str, Any]:
        """
        Generate 3 comment options for a post based on:
        - Post content
        - All comments on that post
        - Persona style
        - Reddit-derived writing rules
        """

        # 1️⃣ Fetch post and its comments from DB
        post: LinkedInPost = self.db.query(LinkedInPost).filter_by(id=post_id).first()
        if not post:
            raise Exception(f"Post with ID {post_id} not found.")

        post_text = post.post_text or ""
        author_name = post.author_name or "the author"

        # 2️⃣ Learn from the entire thread (post.comments)
        local_context = self.learn_from_post_comments(post.comments)

        # 3️⃣ Detect intent and sentiment
        intent = self.classify_post_intent(post_text)
        sentiment = self.analyze_post_sentiment(post_text)

        # 4️⃣ Generate comment options
        comments = []
        for _ in range(3):
            generated = self.generate_single_comment(
                post_text=post_text,
                author_name=author_name,
                persona=persona,
                local_context=local_context,
                intent=intent,
                sentiment=sentiment,
            )
            comments.append(generated)

        # 5️⃣ Pick reactions based on sentiment, intent, thread tone
        mapped_reactions = self.pick_reactions(sentiment, intent, local_context)

        # 6️⃣ Track learning statistics
        self.stats["total_comments"] += len(comments)
        self.stats["persona_counts"][persona] += len(comments)
        self.stats["intent_counts"][intent] += len(comments)

        return {
            "post_text": post_text[:120] + "..." if len(post_text) > 120 else post_text,
            "author": author_name,
            "comment_options": comments,
            "reactions": mapped_reactions,
            "meta": {
                "persona": persona,
                "intent": intent,
                "sentiment": sentiment,
                "thread_tone": local_context.get("tone"),
            },
        }

    # ------------------------------------------------------------------
    # SINGLE COMMENT GENERATION
    # ------------------------------------------------------------------
    def generate_single_comment(
        self,
        post_text: str,
        author_name: str,
        persona: str,
        local_context: Dict[str, Any],
        intent: str,
        sentiment: str,
    ) -> str:
        """
        Generate ONE comment using:
        - persona style
        - thread tone
        - global Reddit patterns
        - post intent & sentiment
        """
        tone_instructions = self.build_tone_instructions(
            persona=persona,
            global_rules=self.global_rules,
            local_context=local_context,
            intent=intent,
        )

        truncated_post = post_text[:250] + "..." if len(post_text) > 250 else post_text

        # Length target based on thread behavior
        avg_len = local_context.get("avg_length", 140)
        target_length = int(avg_len * 0.8)
        target_length = max(80, min(target_length, 220))

        # Use one question pattern if thread tends to be curious or global patterns exist
        q_patterns = self.global_rules.get("question_patterns", [])
        question_hint = ""
        if local_context.get("question_rate", 0.0) > 0.2 and q_patterns:
            question_hint = f"Optionally echo the style of this kind of question: '{q_patterns[0]}'"

        # Use industry terms if intent is AI/sales/marketing
        industry_terms = self.global_rules.get("industry_terms", [])
        term_hint = ""
        if industry_terms and intent in {"ai", "sales", "marketing", "business"}:
            term_hint = f"Optionally mention a relevant concept like '{industry_terms[0]}' if it fits naturally."

        prompt = f"""
You are writing a short LinkedIn COMMENT replying to a post.

POST BY {author_name}:
\"\"\"{truncated_post}\"\"\"

CONTEXT:
- Detected intent: {intent}
- Detected sentiment: {sentiment}
- Thread tone & behavior: {local_context.get("tone")}

WRITING RULES:
- {tone_instructions}
- Length target: about {target_length} characters.
- Avoid generic phrases like: {self.global_rules.get("avoid_generic")}
- Use natural sentence variation (one short, one slightly longer).
- Max 2 sentences.
- At most 1 emoji, only if it fits the persona and tone.
- NO hashtags.
- NO markdown (no *, _, ~~).
- Sound like a real human replying directly to this post.
- {question_hint}
- {term_hint}

Now write the comment text only:
"""

        try:
            response = self.openai_client.responses.create(
                model="gpt-4o-mini",
                input=prompt,
                max_output_tokens=80,
                temperature=0.7,
            )
            raw = response.output_text.strip()
            cleaned = self.clean_text(raw)
            return cleaned

        except Exception:
            return self.generate_fallback_comment()

    # ------------------------------------------------------------------
    # FALLBACK COMMENT (NO GPT / ERROR CASE)
    # ------------------------------------------------------------------
    def generate_fallback_comment(self) -> str:
        fallbacks = [
            "Really appreciate how you explained this — curious what sparked this experiment.",
            "Love this breakdown. What’s been the most surprising learning so far?",
            "Great perspective. How are you measuring the impact in practice?",
        ]
        return self.clean_text(random.choice(fallbacks))
