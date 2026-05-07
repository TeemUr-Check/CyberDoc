# INTENTIONALLY VULNERABLE — AI / training fixture only.

def get_document(doc_id: str, user_id: str | None):
    # doc_id from URL; user_id optional and not checked against ownership
    with open(f"vault/{doc_id}.txt") as f:
        return f.read()
