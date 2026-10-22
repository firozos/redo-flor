"""
Single-run script to fetch Redo Telegram Gift floor price and send it to a chat.
Designed for serverless execution like GitHub Actions (requires standard library only).
"""

import os
import json
import urllib.request
import urllib.parse
import sys

BOT_TOKEN = os.getenv("BOT_TOKEN", "8672901866:AAFztg88kYpAozWlvBSD-S99e1oMQh9Svaw")
CHAT_ID = os.getenv("CHAT_ID")  # Chat ID of Taha or your group

REDO_COLLECTION_ADDRESS = "EQAkEAkvhMTc0Ch7tsW9wlOxHewpsIV7Vc7uboakVviVSZ31"


def fetch_floor_price():
    """Fetch floor price from TonAPI with fallback to Getgems."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # 1. Try TonAPI
    try:
        url = f"https://tonapi.io/v2/nfts/collections/{REDO_COLLECTION_ADDRESS}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_floor = data.get("floor_price") or data.get("approximate_floor_price")
            if raw_floor:
                floor_ton = float(raw_floor) / 1e9 if float(raw_floor) > 1000 else float(raw_floor)
                return {
                    "name": data.get("metadata", {}).get("name", "Resistance Dog (Redo)"),
                    "floor_ton": round(floor_ton, 2),
                    "source": "TonAPI / TON Ecosystem"
                }
    except Exception as e:
        print(f"TonAPI attempt failed: {e}", file=sys.stderr)

    # 2. Fallback to Getgems GraphQL
    try:
        graphql_url = "https://api.getgems.io/graphql"
        query = {
            "query": """
            query GetFloor($address: String!) {
                alphaNftCollection(address: $address) {
                    name
                    approximateFloorPrice
                }
            }
            """,
            "variables": {"address": REDO_COLLECTION_ADDRESS}
        }
        post_data = json.dumps(query).encode("utf-8")
        req = urllib.request.Request(
            graphql_url,
            data=post_data,
            headers={**headers, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_json = json.loads(resp.read().decode("utf-8"))
            col = res_json.get("data", {}).get("alphaNftCollection")
            if col and col.get("approximateFloorPrice"):
                floor_ton = float(col["approximateFloorPrice"]) / 1e9
                return {
                    "name": col.get("name", "Resistance Dog (Redo)"),
                    "floor_ton": round(floor_ton, 2),
                    "source": "Getgems Marketplace"
                }
    except Exception as e:
        print(f"Getgems attempt failed: {e}", file=sys.stderr)

    return None


def send_telegram_message(token: str, chat_id: str, text: str):
    """Send message via Telegram Bot HTTP API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    if not CHAT_ID:
        print("ERROR: CHAT_ID environment variable is missing!", file=sys.stderr)
        sys.exit(1)

    print("Fetching Redo floor price...")
    price_info = fetch_floor_price()

    if price_info:
        msg = (
            f"🐕 **قیمت روزانه گیفت تلگرام: {price_info['name']}**\n\n"
            f"💰 **قیمت کف (Floor):** `{price_info['floor_ton']} TON`\n"
            f"📊 **مرجع:** {price_info['source']}\n\n"
            f"🤖 *ارسال خودکار توسط GitHub Actions*"
        )
    else:
        msg = "⚠️ در استعلام خودکار امروز قیمت فلور Redo خطایی رخ داد. لطفاً دستی بررسی کنید."

    print(f"Sending message to chat: {CHAT_ID}...")
    res = send_telegram_message(BOT_TOKEN, CHAT_ID, msg)
    if res.get("ok"):
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {res}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
