from typing import Tuple, List, Dict
import json

from ..clients.unipile_client import UnipileClient
from ..db.models import PotentialCustomer, LinkedInPost
from ..utils.config import CALENDLY_BOOKING_URL


class OutreachAgent:
    """
    Generates personalized messages:
    - LinkedIn DM
    - Short LinkedIn connection note
    - Soft, human follow-ups
    - Calendly followup text
    """

    SERVICE_AREAS = [
        "lead generation",
        "sales",
        "business development",
        "marketing automation",
        "automation",
        "generative ai",
        "ai agents",
        "generative engine optimization",
    ]

    def __init__(self):
        self.unipile = UnipileClient()

    # ---------------------------------------------
    #  Classify interest (theme + service area)
    # ---------------------------------------------
    def _classify_interest(self, post_text: str) -> Dict:
        if not post_text:
            return {"theme": None, "area": None, "reason": "no_post"}

        prompt = f"""
        You are an expert B2B intent analyst.

        Classify this LinkedIn post into one service area:
        {", ".join(self.SERVICE_AREAS)}

        Post:
        {post_text}

        Return STRICT JSON:
        {{
          "theme": "<short theme>",
          "area": "<one of the list or null>",
          "reason": "<very short reasoning>"
        }}
        """

        try:
            completion = self.unipile.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=220,
            )
            raw = completion.choices[0].message.content
            return json.loads(raw)
        except Exception:
            return {"theme": None, "area": None, "reason": "error"}

    # ---------------------------------------------
    #  Generate LinkedIn DM (longer message used also for email body)
    # ---------------------------------------------
    def generate_dm(
        self, lead: PotentialCustomer, post: LinkedInPost
    ) -> Tuple[str, List[str]]:
        interest = self._classify_interest(post.post_text if post else "")
        name = lead.name or "there"
        role = lead.role or "leader"
        company = lead.company or "your company"
        theme = interest.get("theme") or "what you shared"
        area = interest.get("area") or "improving your pipeline"

        post_snippet = (post.post_text[:220] + "...") if post and post.post_text else ""

        prompt = f"""
        You are a founder reaching out with a very friendly, low-pressure message.

        Write a 2–3 sentence LinkedIn DM that can ALSO be used as an email body.

        Lead:
        - Name: {name}
        - Role: {role}
        - Company: {company}

        Context:
        - They engaged with content around: {theme}
        - Relevant improvement area: {area}
        - Post snippet (for your context only, do NOT copy it verbatim):
          \"\"\"{post_snippet}\"\"\"

        Style:
        - Sound like a real human, not a robot.
        - Be specific about {area}, mention ONE concrete angle/value (e.g. better reply rates, more qualified conversations, less manual work).
        - No pitch deck talk, no buzzwords.
        - No emojis.
        - End with a soft CTA like:
          "If you're open to it, happy to share a quick example." or
          "Would it make sense to compare notes for 10–15 minutes?"

        Constraints:
        - 2–3 sentences max
        - No bullet points
        - No subject line
        """

        try:
            completion = self.unipile.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=260,
            )
            dm_text = completion.choices[0].message.content.strip()
        except Exception:
            dm_text = (
                f"Hi {name}, I really liked how you approached {theme} — it’s very aligned "
                f"with how we think about {area}. If you’re open to it, I’d be happy to share "
                f"a quick example of what’s working well with similar teams."
            )

        followups = self.generate_followups(lead, interest)
        return dm_text, followups

    # ---------------------------------------------
    #  Followups (short, human, 1 sentence each)
    # ---------------------------------------------
    def generate_followups(
        self, lead: PotentialCustomer, interest: Dict
    ) -> List[str]:
        area = interest.get("area") or "automation"
        name = lead.name.split()[0] if lead.name else "there"

        prompt = f"""
        Write TWO short follow-up messages for someone who has NOT replied yet.

        Context:
        - Recipient first name: {name}
        - Topic: {area}

        Style:
        - One sentence each
        - No emojis
        - Light, respectful, non-pushy
        - Reference that you reached out earlier without saying "follow up"
        - Each line should stand alone as a complete message

        Output:
        - Line 1: first message
        - Line 2: second message
        """

        try:
            completion = self.unipile.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=180,
            )
            raw = completion.choices[0].message.content
            lines = [
                l.strip("-• ").strip()
                for l in raw.split("\n")
                if l.strip()
            ]
            # Filter out any numbering like "1." / "2."
            cleaned = []
            for l in lines:
                cleaned.append(l.lstrip("1234567890. ").strip())
            # Keep only non-empty and unique ones
            cleaned = [c for c in cleaned if c]
            # Ensure at least 2
            if len(cleaned) < 2:
                raise ValueError("Not enough followups generated")
            return cleaned[:2]

        except Exception:
            return [
                f"Hey {name}, just bringing this back on your radar in case {area} is still something you’re exploring.",
                f"If it becomes relevant, I’m happy to share a quick example of how others are improving {area} without adding extra workload.",
            ]

    # ---------------------------------------------
    #  LinkedIn Invitation Short Note (<= 180 chars)
    # ---------------------------------------------
    def generate_linkedin_note(
        self, lead: PotentialCustomer, post: LinkedInPost
    ) -> str:
        """
        Strictly <= 180 chars.
        1–2 short clauses.
        No emojis, no URLs, no line breaks.
        """

        post_text = post.post_text[:80] if post and post.post_text else ""
        name = (lead.name or "").split()[0] if lead.name else ""
        company = lead.company or ""
        role = lead.role or ""

        prompt = f"""
        Write ONE sentence LinkedIn connection note STRICTLY under 180 characters.

        Include:
        - Their name: {name} (if available)
        - Light reference to their role/company: {role} at {company}
        - A subtle nod to what they post about: {post_text}

        Rules:
        - No emojis
        - No line breaks
        - No URLs
        - No selling, no mention of "demo", "offer", "sales" etc.
        - End with a soft question like:
          "open to connecting?" or "happy to connect?"

        Output:
        - Just the sentence, nothing else.
        """

        completion = self.unipile.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
        )

        text = completion.choices[0].message.content.strip()
        text = text.replace("\n", " ")

        # Hard truncate to 180 chars
        if len(text) > 180:
            text = text[:177].rstrip() + "..."

        return text

    # ---------------------------------------------
    #  Calendly followup text (for warm leads)
    # ---------------------------------------------
    def generate_calendly_followup(self, lead: PotentialCustomer) -> str:
        name = lead.name.split()[0] if lead.name else "there"
        return (
            f"Hey {name}, this sounds worth a proper chat — if it helps, "
            f"here’s a link to pick a time that works for you: {CALENDLY_BOOKING_URL}"
        )
