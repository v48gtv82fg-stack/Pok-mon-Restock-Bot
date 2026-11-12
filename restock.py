import os
import json
import urllib.request

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]

def send_discord(message):
    data = json.dumps({
        "username": "Pokémon Restock Radar",
        "content": message
    }).encode("utf-8")

    request = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "PokemonRestock/1.0"
        },
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        print("Discord:", response.status)

if __name__ == "__main__":
    send_discord(
        "🟢 **Pokémon Restock Radar**\n"
        "TEST: Discord-Verbindung erfolgreich!\n"
        "Noch keine Live-Bestandsüberwachung."
    )
