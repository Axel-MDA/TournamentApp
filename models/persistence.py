"""
models/persistence.py

Fonctions de haut niveau pour sauvegarder et charger un tournoi
depuis un fichier JSON sur le disque.

Usage :
    from models.persistence import save_tournament, load_tournament

    save_tournament(tournament, "mon_tournoi.json")
    tournament = load_tournament("mon_tournoi.json")
"""
from __future__ import annotations

import json
from pathlib import Path

from .tournament import Tournament
from .serializer import to_dict, from_dict


def save_tournament(tournament: Tournament, filepath: str | Path) -> None:
    """
    Sauvegarde un tournoi dans un fichier JSON.

    Args:
        tournament (Tournament) : Le tournoi à sauvegarder.
        filepath   (str | Path) : Chemin du fichier de destination.

    Raises:
        OSError: Si l'écriture échoue (permissions, disque plein…).
    """
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = to_dict(tournament)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_tournament(filepath: str | Path) -> Tournament:
    """
    Charge un tournoi depuis un fichier JSON.

    Args:
        filepath (str | Path): Chemin du fichier à lire.

    Returns:
        Tournament: Le tournoi reconstruit.

    Raises:
        FileNotFoundError : Si le fichier n'existe pas.
        ValueError        : Si le fichier est invalide ou d'une version incompatible.
        json.JSONDecodeError: Si le fichier n'est pas un JSON valide.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Fichier introuvable : {filepath}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    return from_dict(data)


def default_save_path(tournament_name: str) -> Path:
    """
    Retourne un chemin de sauvegarde par défaut dans le répertoire courant.

    Args:
        tournament_name (str): Nom du tournoi (utilisé pour le nom de fichier).

    Returns:
        Path: Chemin suggéré, ex: ./saves/championnat_regional.json
    """
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in tournament_name)
    safe_name = safe_name.strip().replace(" ", "_").lower()
    return Path("saves") / f"{safe_name}.json"
