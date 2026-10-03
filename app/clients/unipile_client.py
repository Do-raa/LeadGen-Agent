import requests
from datetime import datetime
from openai import OpenAI 
from ..utils.config import UNIPILE_API_KEY, UNIPILE_LINKEDIN_ACCOUNT_ID, OPENAI_API_KEY, UNIPILE_MAIL_ACCOUNT_ID

BASE = "https://api19.unipile.com:14984/api/v1"
ACCOUNT_ID = UNIPILE_LINKEDIN_ACCOUNT_ID
MAIL_ACCOUNT_ID = UNIPILE_MAIL_ACCOUNT_ID  

class UnipileClient:
    def __init__(self, api_key=UNIPILE_API_KEY, account_id=ACCOUNT_ID):
        self.api_key = api_key
        self.account_id = account_id
        self.headers = {
            "X-API-KEY": self.api_key,
            "accept": "application/json"
        }
        self.openai = OpenAI(api_key=OPENAI_API_KEY)

    # ------------------------------------------------------------------
    # 1️⃣ GET PROVIDER PROFILE → returns provider_id (LinkedIn internal ID)
    # ------------------------------------------------------------------
    def get_provider_id(self, public_identifier: str):
        """
        Retrieve a LinkedIn user's provider_id from their public identifier (username).
        Example: public_identifier = 'vyaspratik'
        """
        url = f"{BASE}/users/{public_identifier}"
        params = {
            "linkedin_sections": "*",
            "account_id": self.account_id
        }

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if not resp.ok:
            raise Exception(f"Failed to retrieve provider ID ({resp.status_code}): {resp.text}")

        data = resp.json()
        provider_id = data.get("provider_id")
        if not provider_id:
            raise Exception("Provider ID not found in response")

        return provider_id


    # ------------------------------------------------------------------
    # 2️⃣ GET USER POSTS → filtered by engagement relevance
    # ------------------------------------------------------------------
    def get_user_posts(self, provider_id: str, limit: int = 30):
        """
        Retrieve recent posts from a LinkedIn user.
        Filters out low-engagement or irrelevant posts automatically.
        """
        url = f"{BASE}/users/{provider_id}/posts"
        params = {
            "account_id": self.account_id,
            "limit": limit
        }

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if not resp.ok:
            raise Exception(f"Failed to retrieve posts ({resp.status_code}): {resp.text}")

        posts_data = resp.json().get("items", [])
        
        relevant_posts = []

        for post in posts_data:
            text = post.get("text", "")
            if not text:
                continue

            try:
                completion = self.openai.responses.create(
                    model="gpt-4o-mini",
                    input=(
                        "You must answer exactly one word: true or false.\n\n"
                        "Say true ONLY if this post is about:\n"
                        "- lead generation\n"
                        "- sales\n"
                        "- business development\n"
                        "- marketing\n"
                        "- automation\n"
                        "- AI\n"
                        "Otherwise say false.\n\n"
                        f"Post content:\n{text}"
                    ),
                    max_output_tokens=20
                )

                decision = completion.output_text.strip().lower()
                if "true" in decision:
                    relevant_posts.append(post)

            except Exception as e:
                print(f"⚠️ OpenAI filtering failed for post: {e}")
                continue

        print(f"✅ Retrieved {len(relevant_posts)} relevant posts out of {len(posts_data)} total.")
        return relevant_posts

    # ------------------------------------------------------------------
    # 3️⃣ GET COMMENTS FOR A POST
    # ------------------------------------------------------------------
    def get_post_comments(self, social_id: str, limit: int = 50):
        """
        Retrieve comments from a LinkedIn post.
        """
        url = f"{BASE}/posts/{social_id}/comments"
        params = {
            "account_id": self.account_id,
            "limit": limit
        }

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if not resp.ok:
            raise Exception(f"Failed to retrieve comments ({resp.status_code}): {resp.text}")

        data = resp.json()
        comments = data.get("items", [])

        return comments

    # ------------------------------------------------------------------
    # 4️⃣ GET REACTIONS FOR A POST
    # ------------------------------------------------------------------
    def get_post_reactions(self, post_id: str, limit: int = 100):
        """
        Retrieve reactions from a LinkedIn post.
        Returns list of users who reacted with their names and profile info.
        """
        url = f"{BASE}/posts/{post_id}/reactions"
        params = {
            "account_id": self.account_id,
            "limit": limit
        }

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if not resp.ok:
            raise Exception(f"Failed to retrieve reactions ({resp.status_code}): {resp.text}")

        data = resp.json()
        reactions = data.get("items", [])
        
        print(f"✅ Retrieved {len(reactions)} reactions for post {post_id}")
        return reactions
    
    # ------------------------------------------------------------------
    # 5️⃣ EXTRACT POTENTIAL CUSTOMERS FROM COMMENTS AND REACTIONS
    # ------------------------------------------------------------------
    def extract_potential_customers(self, comments=None, reactions=None):
        leads = {}

        # Extract from comments
        if comments:
            for c in comments:
                public_id = c.get("public_identifier")
                if not public_id:
                    continue
                
                author_name = c.get("author")
                if not author_name:
                    continue

                leads[public_id] = {
                    "name": author_name,
                    "public_identifier": public_id,
                    "linkedin_url": f"https://www.linkedin.com/in/{public_id}",
                    "source": "comment",
                    "identifier": public_id
                }

        # Extract from reactions
        if reactions:
            for r in reactions:
                author = r.get("author", {})
                name = author.get("name")
                profile_url = author.get("profile_url")
                if not profile_url:
                    continue

                public_id = profile_url.rstrip("/").split("/")[-1]

                leads[public_id] = {
                    "name": name,
                    "public_identifier": public_id,
                    "linkedin_url": profile_url,
                    "reaction_type": r.get("reaction_type", "LIKE"),
                    "source": "reaction",
                    "identifier": public_id
                }

        print(f"Extracted {len(leads)} unique leads.")
        return list(leads.values())
        
    def post_linkedin_comment(self, social_id: str, message: str):
        """
        Posts a comment to a LinkedIn post via Unipile.
        """
        url = f"{BASE}/posts/{social_id}/comments"
        payload = {
            "account_id": self.account_id,
            "text": message
        }

        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if not resp.ok:
            raise Exception(f"Failed to post comment: {resp.status_code} - {resp.text}")

        print(f"💬 Comment posted to {social_id}")
        return resp.json()
    
    def post_linkedin_reaction(self, social_id: str, reaction_type: str):
        """
        Adds a reaction to a LinkedIn post.
        """
        url = f"{BASE}/posts/reaction"
        payload = {
            "account_id": self.account_id,
            "post_id": social_id,
            "reaction_type": reaction_type.lower()
        }

        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if not resp.ok:
            raise Exception(f"Failed to post reaction: {resp.status_code} - {resp.text}")

        print(f"🔥 Reaction '{reaction_type}' added to {social_id}")
        return resp.json()
    
    # ---------------------------------------------------------
    #  ENRICH PROFILE 
    # ---------------------------------------------------------
    def enrich_profile(self, linkedin_url: str = None, public_identifier: str = None):
        """
        Retrieve full LinkedIn profile data from Unipile.
        Returns FULL RAW JSON directly from Unipile.
        API layer will handle parsing.
        """

        # -----------------------------------------------
        # STEP 1 — Determine identifier
        # -----------------------------------------------
        identifier = None

        if public_identifier:
            identifier = public_identifier.strip()

        elif linkedin_url:
            try:
                identifier = linkedin_url.rstrip("/").split("/")[-1]

                # Remove tracking parameters
                if "?" in identifier:
                    identifier = identifier.split("?")[0]

                # Very malformed URL
                if not identifier or identifier in ["www.linkedin.com", "in"]:
                    print(f"⚠️ Invalid LinkedIn URL (no identifier): {linkedin_url}")
                    return {}

            except Exception as e:
                print("⚠️ Error extracting identifier from URL:", e)
                return {}

        # No identifier = cannot enrich
        if not identifier:
            print("⚠️ enrich_profile() called without linkedin_url or public_identifier")
            return {}

        # -----------------------------------------------
        # STEP 2 — Call Unipile
        # -----------------------------------------------
        url = f"{BASE}/users/{identifier}"
        params = {
            "account_id": self.account_id,
            "linkedin_sections": "*"   # FULL data
        }

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)

        if not resp.ok:
            print(f"⚠️ Unipile enrichment failed for '{identifier}': {resp.status_code}")
            print("Response:", resp.text)
            return {}

        # -----------------------------------------------
        # STEP 3 — Return FULL JSON (unchanged)
        # -----------------------------------------------
        return resp.json()

    # ---------------------------------------------------------
    # SEND LINKEDIN INVITATION WITH NOTE
    # ---------------------------------------------------------
    def send_linkedin_invitation(self, public_identifier: str, message: str):
        provider_id = self.get_provider_id(public_identifier)

        url = f"{BASE}/users/invite"
        payload = {
            "account_id": self.account_id,
            "provider_id": provider_id,
            "message": message[:300]  # LinkedIn limit
        }

        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if not resp.ok:
            raise Exception(f"LinkedIn INVITE failed: {resp.status_code} {resp.text}")

        return resp.json()

    # ---------------------------------------------------------
    # SEND EMAIL VIA UNIPILE (with optional reply_to)
    # ---------------------------------------------------------
    def send_email(self, to_email: str, subject: str, body: str, reply_to: str | None = None):
        url = f"{BASE}/emails"

        payload = {
            "account_id": MAIL_ACCOUNT_ID,
            "from": {"identifier": "dorraelkahlaa@gmail.com"},
            "to": [{"identifier": to_email}],
            "subject": subject,
            "body": body,
        }

        if reply_to:
            payload["reply_to"] = reply_to

        resp = requests.post(
            url,
            headers={**self.headers, "content-type": "application/json"},
            json=payload,
            timeout=30,
        )

        if not resp.ok:
            raise Exception(f"Email failed: {resp.status_code} {resp.text}")

        return resp.json()

    # ---------------------------------------------------------
    #  SEND LINKEDIN DM 
    # ---------------------------------------------------------
    def send_linkedin_dm(self, recipient_public_identifier: str, text: str):
        """
        Starts a new LinkedIn chat (DM) with the target user.
        """

        # First: convert public identifier → provider_id
        provider_id = self.get_provider_id(recipient_public_identifier)

        url = f"{BASE}/chats"
        payload = {
            "account_id": self.account_id,
            "text": text,
            "attendees_ids": [provider_id]  
        }

        resp = requests.post(url, headers=self.headers, json=payload, timeout=30)

        if not resp.ok:
            raise Exception(f"LinkedIn DM failed: {resp.status_code} {resp.text}")

        return resp.json()

    # ---------------------------------------------------------
    #  FETCH recent emails (inbox)
    # ---------------------------------------------------------
    def list_emails(self, limit: int = 10, any_email: str = None, to: str = None, from_email: str = None):
        url = f"{BASE}/emails"

        params = {
            "account_id": MAIL_ACCOUNT_ID,
            "limit": limit,
        }

        # Optional filters
        if any_email:
            params["any_email"] = any_email

        if to:
            params["to"] = to

        if from_email:
            params["from"] = from_email

        resp = requests.get(url, headers=self.headers, params=params, timeout=30)

        if not resp.ok:
            raise Exception(f"Email read failed: {resp.status_code} {resp.text}")

        return resp.json().get("items", [])

    # ---------------------------------------------------------
    #  FETCH email details
    # ---------------------------------------------------------
    def get_email(self, email_id: str ):
        url = f"{BASE}/emails/{email_id}"
        params = {
            "account_id": MAIL_ACCOUNT_ID,
            "meta_only": False
        }
        resp = requests.get(url, headers=self.headers, params=params, timeout=30)
        if not resp.ok:
            raise Exception(f"Email detail failed: {resp.status_code} {resp.text}")
        return resp.json()
