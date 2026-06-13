import urllib.parse

def generate_whatsapp_url(phone_number: str, message: str) -> str:
    """
    Generates a wa.me link as shown in the Notifications UI tip.
    Example: https://wa.me/254712345678?text=Hi%20...
    """
    cleaned = ''.join(ch for ch in phone_number if ch.isdigit())
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    if cleaned.startswith('0') and len(cleaned) == 10:
        # Kenyan local format -> 254...
        cleaned = '254' + cleaned[1:]
    encoded = urllib.parse.quote(message)
    return f"https://wa.me/{cleaned}?text={encoded}"