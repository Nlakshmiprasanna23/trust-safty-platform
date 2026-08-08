import hashlib

def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return "***"
    name, domain = email.split("@", 1)
    return f"{name[:2]}{'*' * max(len(name) - 2, 2)}@{domain}"

def mask_phone(phone: str) -> str:
    if not phone:
        return "***"
    return f"{'*' * max(len(phone) - 4, 0)}{phone[-4:]}"

def hash_identifier(value: str) -> str:
    return hashlib.sha256((value or "").encode()).hexdigest()[:16]
