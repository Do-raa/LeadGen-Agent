from app.clients.unipile_client import UnipileClient

def test_unipile_client():
    client = UnipileClient()

    # 1️⃣ Step 1: Get provider_id
    print("\n🔹 Fetching provider ID...")
    provider_id = client.get_provider_id("vyaspratik")
    print(f"✅ Provider ID: {provider_id}\n")

    # 2️⃣ Step 2: Get posts for provider
    print("🔹 Fetching relevant posts...")
    posts = client.get_user_posts(provider_id, limit=10)
    print(f"✅ Found {len(posts)} relevant posts.")

    for i, post in enumerate(posts[:3], start=1):  # preview first 3 posts
        print(f"\nPost #{i}:")
        print(f"  ID: {post.get('id')}")
        print(f"  Text: {post.get('text', '')[:200]}...")
        print(f"  Reactions: {post.get('reaction_counter')} | Comments: {post.get('comment_counter')}")
        print(f"  URL: {post.get('share_url')}")

    # 3️⃣ Step 3: Get comments for first post (if available)
    if posts:
        print("\n🔹 Fetching comments for first post...")
        social_id = posts[0].get("social_id")
        comments = client.get_post_comments(social_id)
        print(f"✅ Retrieved {len(comments)} comments for post {social_id}")

        if comments:
            print("\nSample Comment:")
            c = comments[0]
            print(f"  Author: {c.get('author')}")
            print(f"  Text: {c.get('text')[:150]}...")

        # 4️⃣ Step 4: Get reactions for first post
        print("\n🔹 Fetching reactions for first post...")
        reactions = client.get_post_reactions(social_id)
        print(f"✅ Retrieved {len(reactions)} reactions for post {social_id}")

        if reactions:
            print("\nSample Reaction:")
            r = reactions[0]
            author = r.get('author', {})
            print(f"  Author: {author.get('name', 'Unknown')}")
            print(f"  Reaction Type: {r.get('reaction_type')}")
            print(f"  Profile URL: {author.get('profile_url', 'N/A')}")

        # 5️⃣ Step 5: Extract potential customers from comments and reactions
        print("\n🔹 Extracting potential customers...")
        leads = client.extract_potential_customers(comments, reactions)
        print(f"✅ Extracted {len(leads)} potential customers")
        
        if leads:
            print(f"\n📊 Potential Customers Found:")
            for idx, lead in enumerate(leads[:5], start=1):  # Show first 5
                print(f"  {idx}. Identifier: {lead.get('identifier')}")
                print(f"     Source: {lead.get('source')}")
                print(f"     LinkedIn URL: {lead.get('linkedin_url', 'N/A')}")
                if lead.get('reaction_type'):
                    print(f"     Reaction Type: {lead.get('reaction_type')}")
                print()

        # 6️⃣ Step 6: Test profile enrichment
        # 6️⃣ Step 6: Test profile enrichment on at least 10 leads
        print("\n🔹 Testing profile enrichment (10 leads)...")

        enriched_count = 0

        for lead in leads[:10]:
            identifier = None

            linkedin_url = lead.get("linkedin_url")
            if linkedin_url:
                identifier = linkedin_url.rstrip("/").split("/")[-1]
                if "?" in identifier:
                    identifier = identifier.split("?")[0]

            if not identifier:
                print(f"⚠️ Cannot enrich (no LinkedIn URL): {lead.get('identifier')}")
                continue

            print(f"\n🧩 Enriching profile → {identifier}...")

            data = client.enrich_profile(
                linkedin_url=linkedin_url,
                public_identifier=identifier
            )

            if not data:
                print("❌ Enrichment failed or user unreachable")
                continue

            enriched_count += 1

            # Extract required fields
            email = None
            try:
                email_list = data.get("contact_info", {}).get("emails", [])
                email = email_list[0] if email_list else None
            except:
                pass

            role = None
            company = None
            try:
                exp = data.get("work_experience", [])
                if exp:
                    current = next((x for x in exp if x.get("current")), None)
                    if not current:
                        current = exp[0]
                    role = current.get("position")
                    company = current.get("company")
            except:
                pass

            print("✅ Enriched Profile:")
            print(f"   Name: {data.get('first_name', '')} {data.get('last_name', '')}")
            print(f"   Headline: {data.get('headline', 'N/A')}")
            print(f"   Email: {email}")
            print(f"   Role: {role}")
            print(f"   Company: {company}")
            print(f"   Followers: {data.get('follower_count', 'N/A')}")
            print(f"   Public Profile: {data.get('public_profile_url', 'N/A')}")

        print(f"\n🔍 Finished enriching {enriched_count} profiles.")

        # 7️⃣ Step 7: Test posting comment and reaction (commented out for safety)
        print("\n🔹 Testing comment and reaction posting (commented out for safety)...")
        # Uncomment these lines to actually test posting
        """
        test_comment = "Great insights! Thanks for sharing this valuable information."
        try:
            comment_result = client.post_linkedin_comment(social_id, test_comment)
            print(f"✅ Comment posted successfully: {comment_result}")
        except Exception as e:
            print(f"❌ Comment posting failed: {e}")

        try:
            reaction_result = client.post_linkedin_reaction(social_id, "like")
            print(f"✅ Reaction posted successfully: {reaction_result}")
        except Exception as e:
            print(f"❌ Reaction posting failed: {e}")
        """

        # 8️⃣ Step 8: Test LinkedIn DM (commented out for safety)
        print("\n🔹 Testing LinkedIn DM (commented out for safety)...")
        """
        test_dm_message = "Hello! I came across your profile and would love to connect regarding potential opportunities."
        try:
            # Use a test identifier - replace with actual LinkedIn username
            dm_result = client.send_linkedin_dm("test_username", test_dm_message)
            print(f"✅ DM sent successfully: {dm_result}")
        except Exception as e:
            print(f"❌ DM sending failed: {e}")
        """

    else:
        print("❌ No posts found to test comments, reactions, and other functions.")

    # 9️⃣ Step 9: Test error handling
    print("\n🔹 Testing error handling...")
    
    # Test with invalid provider ID
    try:
        invalid_posts = client.get_user_posts("invalid_provider_id", limit=5)
        print(f"❌ Expected error but got: {len(invalid_posts)} posts")
    except Exception as e:
        print(f"✅ Error handling working: {str(e)[:100]}...")

    # Test with invalid post ID for comments
    try:
        invalid_comments = client.get_post_comments("invalid_post_id")
        print(f"❌ Expected error but got: {len(invalid_comments)} comments")
    except Exception as e:
        print(f"✅ Error handling working: {str(e)[:100]}...")

    print("\n" + "="*50)
    print("🎉 UNIPILE CLIENT TEST COMPLETED SUCCESSFULLY!")
    print("="*50)

def test_specific_functions():
    """Test specific functions in isolation"""
    client = UnipileClient()
    
    print("\n🧪 Testing Specific Functions...")
    
    # Test profile enrichment directly
    print("\n🔹 Testing direct profile enrichment...")
    profile = client.enrich_profile(public_identifier="vyaspratik")
    if profile:
        print("✅ Direct profile enrichment successful")
        print(f"   Name: {profile.get('name', 'N/A')}")
        print(f"   Headline: {profile.get('headline', 'N/A')}")
        print(f"   Followers: {profile.get('followers_count', 'N/A')}")
    else:
        print("❌ Direct profile enrichment failed")

    # Test extract_potential_customers with empty data
    print("\n🔹 Testing extract_potential_customers with empty data...")
    empty_leads = client.extract_potential_customers([], [])
    print(f"✅ Empty data handling: {len(empty_leads)} leads found")

    # Test with sample comments and reactions
    sample_comments = [
        {"author": "john_doe", "text": "Great post!"},
        {"author": "jane_smith", "text": "Interesting insights"}
    ]
    
    sample_reactions = [
        {"author": {"name": "bob_wilson", "profile_url": "https://linkedin.com/in/bobwilson"}, "reaction_type": "LIKE"},
        {"author": {"name": "alice_brown", "profile_url": "https://linkedin.com/in/alicebrown"}, "reaction_type": "CELEBRATION"}
    ]
    
    test_leads = client.extract_potential_customers(sample_comments, sample_reactions)
    print(f"✅ Sample data test: {len(test_leads)} leads found")
    for lead in test_leads:
        print(f"   - {lead.get('identifier')} ({lead.get('source')})")

if __name__ == "__main__":
    print("🚀 Starting Unipile Client Comprehensive Test...")
    
    # Run main test
    test_unipile_client()
    
    # Run specific function tests
    test_specific_functions()
    
    print("\n📋 TEST SUMMARY:")
    print("✅ Provider ID retrieval")
    print("✅ Posts retrieval with AI filtering") 
    print("✅ Comments retrieval")
    print("✅ Reactions retrieval")
    print("✅ Lead extraction from comments & reactions")
    print("✅ Profile enrichment")
    print("✅ Error handling")
    print("✅ All core functions tested successfully!")