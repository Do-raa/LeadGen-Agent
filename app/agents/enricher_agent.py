import re
from datetime import datetime
from sqlalchemy.orm import Session
from ..db.models import PotentialCustomer
from ..clients.trykitt_client import TrykittClient

class EnricherAgent:
    def __init__(self):
        self.client = TrykittClient()

    def _extract_domain_from_linkedin(self, linkedin_url: str) -> str | None:
        """
        Try to extract a meaningful domain guess from a LinkedIn URL.
        Example: https://www.linkedin.com/in/john-doe-acme -> acme.com
        """
        if not linkedin_url:
            return None

        # Match patterns like linkedin.com/in/john-doe-acme
        pattern = r"linkedin\.com/(?:in|company)/([\w\-]+)"
        match = re.search(pattern, linkedin_url)
        if match:
            handle = match.group(1)
            # Try to extract potential company name hints
            fragments = [frag for frag in handle.split('-') if len(frag) > 3]
            if fragments:
                return f"{fragments[-1]}.com"
        return None

    def _generate_domain_guesses(self, lead) -> list[str]:
        """
        Generate multiple fallback domain guesses for enrichment.
        Order of priority:
        1️⃣ Lead company field
        2️⃣ Extracted from LinkedIn URL
        3️⃣ linkedin.com
        4️⃣ Default generic guess (gmail.com, yahoo.com, etc. for testing)
        """
        guesses = []

        if lead.company:
            cleaned = re.sub(r'https?://(www\.)?', '', lead.company).strip().lower()
            if '.' in cleaned:
                guesses.append(cleaned)
            else:
                guesses.append(f"{cleaned}.com")

        linkedin_guess = self._extract_domain_from_linkedin(lead.linkedin_url)
        if linkedin_guess:
            guesses.append(linkedin_guess)

        guesses.extend(["linkedin.com", "gmail.com", "yahoo.com"])
        return list(dict.fromkeys(guesses))  # remove duplicates

    def enrich_leads(self, db: Session, limit: int = 10):
        """
        Enrich 'new' potential customers with Trykitt.
        Automatically guesses the most likely email domain.
        """
        leads = (
            db.query(PotentialCustomer)
            .filter(PotentialCustomer.status == "new")
            .limit(limit)
            .all()
        )
        if not leads:
            print("⚠️ No new leads found for enrichment.")
            return []

        enriched = []
        for lead in leads:
            print(f"🔍 Enriching lead: {lead.name} ({lead.linkedin_url or 'no LinkedIn'})")

            domain_guesses = self._generate_domain_guesses(lead)
            print(f"🧠 Domain guesses: {domain_guesses}")

            enrichment_data = None
            for domain in domain_guesses:
                print(f"➡️ Trying Trykitt enrichment with domain: {domain}")
                result = self.client.find_email(
                    full_name=lead.name,
                    domain=domain,
                    linkedin_url=lead.linkedin_url
                )
                if result and result.get("email") and "no-results-found" not in result.get("email", "").lower():
                    enrichment_data = result
                    print(f"✅ Successful enrichment for {lead.name} using domain {domain}")
                    break
                else:
                    print(f"❌ No result with {domain}, trying next...")

            if enrichment_data:
                lead.email = enrichment_data.get("email")
                lead.company = enrichment_data.get("companyName") or enrichment_data.get("domain") or lead.company
                lead.role = enrichment_data.get("role") or enrichment_data.get("title")
                lead.status = "enriched"
                lead.enriched_at = datetime.utcnow()
                db.commit()

                enriched.append({
                    "name": lead.name,
                    "email": lead.email,
                    "company": lead.company,
                    "role": lead.role
                })
                print(f"💾 Saved enriched lead: {lead.name} ({lead.email})")

            else:
                print(f"⚠️ Could not enrich {lead.name} after all attempts.")
                lead.status = "unreachable"
                db.commit()

        print(f"🏁 Enrichment finished. Total enriched: {len(enriched)}")
        return enriched

