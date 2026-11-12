import os
import json
import re
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
STATE = Path("stock_state.json")

PRODUCTS = [
    {
        "shop": "Smyths Toys",
        "name": "Pokemon 30 Jahre Top-Trainer-Box",
        "url": "https://www.smythstoys.com/de/de-de/spielzeug/action-spielzeug/pokemon/pokemon-karten/pokemon-karten-top-trainer-box-30-jahre-edition/p/264148",
        "max_price": 54.99
    },
    {
        "shop": "Smyths Toys",
        "name": "Mega Entwicklung Booster 3er Set",
        "url": "https://www.smythstoys.com/de/de-de/spielzeug/action-spielzeug/pokemon/pokemon-karten/pokemon-mega-entwicklung-booster-3er-set-mit-promokarte-sortiert/p/265613",
        "max_price": 16.99
    }
]

def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "PokemonRestock/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def notify(title, description, url, color):
    payload = {
        "username": "Pokemon Restock Radar",
        "allowed_mentions": {"parse": []},
        "embeds": [{
            "title": title,
            "description": description,
            "url": url,
            "color": color,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
    }
    req = urllib.request.Request(
        WEBHOOK,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PokemonRestock/1.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30):
        pass

def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)

def check(product):
    html = fetch(product["url"])
    blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.I | re.S
    )

    for block in blocks:
        try:
            data = json.loads(block)
        except ValueError:
            continue

        for item in walk(data):
            if item.get("@type") != "Offer":
                continue

            if item.get("priceCurrency") != "EUR":
                continue

            status = str(
                item.get("availability", "")
            ).split("/")[-1]

            if status not in (
                "InStock", "OutOfStock",
                "PreOrder", "SoldOut"
            ):
                continue

            try:
                price = float(item["price"])
            except (KeyError, ValueError, TypeError):
                continue

            return {
                "status": status,
                "price": price
            }

    return None

def main():
    old = json.loads(STATE.read_text()) if STATE.exists() else {}
    new = dict(old)
    checked = 0

    for product in PRODUCTS:
        url = product["url"]
        name = product["name"]

        try:
            current = check(product)

            if current is None:
                print("Unbekannter Bestand:", name)
                continue

            checked += 1
            previous = old.get(url, {})
            status = current["status"]
            price = current["price"]

            print(name, status, price)

            if current != previous:
                if (
                    status == "InStock"
                    and price <= product["max_price"]
                ):
                    notify(
                        "RESTOCK: " + name,
                        f"Händler: {product['shop']}\n"
                        f"Online verfügbar\n"
                        f"Preis: {price:.2f} EUR\n"
                        "Stückzahl: unbekannt",
                        url, 3066993
                    )

                elif (
                    status in ("OutOfStock", "SoldOut")
                    and previous.get("status") == "InStock"
                ):
                    notify(
                        "AUSVERKAUFT: " + name,
                        "Online nicht mehr verfügbar.",
                        url, 15158332
                    )

            new[url] = current

        except Exception as error:
            print(name, type(error).__name__)

    STATE.write_text(
        json.dumps(new, indent=2, ensure_ascii=False)
    )

    if checked == 0:
        raise RuntimeError(
            "Keine verifizierbaren Produktdaten gefunden"
        )

if __name__ == "__main__":
    main()
