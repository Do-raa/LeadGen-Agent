from app.clients.unipile_client import UnipileClient

u = UnipileClient()

try:
    r = u.send_linkedin_dm("dorra-e-8272701b7", "Test DM")
    print("OK:", r)
except Exception as e:
    print("ERROR:", e)
