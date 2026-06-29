"""
cli/tournament_ui.py  (version avec sauvegarde / chargement)

Interface CLI pour la création d'un tournoi, l'affichage de son résumé,
la sauvegarde JSON et le chargement depuis un fichier JSON.
"""
from __future__ import annotations

from datetime import date
from pathlib  import Path

from models.config       import ParticipantType
from models.tournament   import Tournament
from models.persistence  import save_tournament, load_tournament, default_save_path
from .utils import clear, pause, choose, input_str


def create_tournament() -> Tournament:
    """
    Guide l'utilisateur pour créer un nouveau tournoi ou en charger un existant.

    Returns:
        Tournament: Le tournoi créé ou chargé.
    """
    clear()
    print("=== TOURNAMENT APP ===\n")

    idx = choose(["Créer un nouveau tournoi", "Charger un tournoi existant (JSON)"])

    if idx == 1:
        tournament = _load_from_file()
        if tournament:
            return tournament
        print("\nChargement annulé. Création d'un nouveau tournoi.\n")

    return _create_new()


def _create_new() -> Tournament:
    clear()
    print("=== CRÉER UN TOURNOI ===\n")

    name  = input_str("Nom du tournoi : ")
    sport = input_str("Sport : ")

    print("\nType de participants :")
    idx              = choose(["Équipes", "Joueurs individuels"])
    participant_type = ParticipantType.TEAM if idx == 0 else ParticipantType.PLAYER

    tournament = Tournament(
        name             = name,
        sport            = sport,
        participant_type = participant_type,
        start_date       = date.today(),
    )

    print(f"\nTournoi '{name}' créé !")
    pause()
    return tournament


def _load_from_file() -> Tournament | None:
    clear()
    print("=== CHARGER UN TOURNOI ===\n")

    saves_dir = Path("saves")
    json_files = sorted(saves_dir.glob("*.json")) if saves_dir.exists() else []

    if json_files:
        print("Fichiers disponibles dans ./saves/ :")
        for i, f in enumerate(json_files, 1):
            print(f"  {i}. {f.name}")
        print()

    filepath = input("Chemin du fichier JSON (ou Entrée pour annuler) : ").strip()
    if not filepath:
        return None

    try:
        tournament = load_tournament(filepath)
        print(f"\nTournoi '{tournament.name}' chargé avec succès !")
        print(f"  Participants : {len(tournament.participants)}")
        print(f"  Phases       : {len(tournament.phases)}")
        print(f"  Statut       : {tournament.status}")
        pause()
        return tournament
    except FileNotFoundError:
        print(f"\nErreur : fichier '{filepath}' introuvable.")
    except Exception as e:
        print(f"\nErreur lors du chargement : {e}")

    pause()
    return None


def save_current_tournament(tournament: Tournament):
    """
    Sauvegarde le tournoi dans un fichier JSON.
    Propose un chemin par défaut et permet à l'utilisateur de le modifier.

    Args:
        tournament (Tournament): Le tournoi à sauvegarder.
    """
    clear()
    print("=== SAUVEGARDER LE TOURNOI ===\n")

    default = default_save_path(tournament.name)
    print(f"Chemin suggéré : {default}")
    filepath = input("Chemin de sauvegarde (Entrée pour utiliser le chemin suggéré) : ").strip()
    if not filepath:
        filepath = str(default)

    try:
        save_tournament(tournament, filepath)
        print(f"\nTournoi sauvegardé dans : {filepath}")
    except Exception as e:
        print(f"\nErreur lors de la sauvegarde : {e}")

    pause()


def show_summary(tournament: Tournament):
    """
    Affiche le résumé complet du tournoi.

    Args:
        tournament (Tournament): Le tournoi à afficher.
    """
    clear()
    print(tournament.summary())
    pause()
