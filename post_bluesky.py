"""
Poste un aphorisme aléatoire de Robert Bresson sur Bluesky.

Gère un état (state.json) pour ne jamais reposter deux fois le même
aphorisme avant d'avoir épuisé toute la liste. Une fois la liste
épuisée, elle est automatiquement remélangée.
"""

import json
import os
import random
import sys

from atproto import Client

APHORISMS_FILE = "bresson_aphorismes.json"
STATE_FILE = "state.json"


def load_aphorisms():
    with open(APHORISMS_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return data["aphorisms"]


def load_state(total):
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)
        # Sécurité : si la liste source a changé de taille, on repart à zéro
        if state.get("total") == total and state.get("remaining"):
            return state
    # Première exécution ou état invalide : on initialise et mélange
    remaining = list(range(total))
    random.shuffle(remaining)
    return {"total": total, "remaining": remaining}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def main():
    handle = os.environ["BLUESKY_HANDLE"]
    app_password = os.environ["BLUESKY_APP_PASSWORD"]

    aphorisms = load_aphorisms()
    state = load_state(len(aphorisms))

    index = state["remaining"].pop()
    text = aphorisms[index]

    if len(text) > 300:
        print(f"Aphorisme trop long ignoré ({len(text)} caractères), tentative suivante.")
        if not state["remaining"]:
            state["remaining"] = list(range(len(aphorisms)))
            random.shuffle(state["remaining"])
        index = state["remaining"].pop()
        text = aphorisms[index]

    # Si la liste est épuisée après ce tirage, on la remélange pour la
    # prochaine exécution (mais on poste bien celui tiré aujourd'hui).
    if not state["remaining"]:
        state["remaining"] = list(range(len(aphorisms)))
        random.shuffle(state["remaining"])

    client = Client()
    client.login(handle, app_password)
    client.send_post(text=text)

    save_state(state)
    print(f"Posté (index {index}, {len(text)} caractères) :\n{text}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erreur lors de la publication : {e}", file=sys.stderr)
        sys.exit(1)
