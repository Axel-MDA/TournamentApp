"""
cli/tournament_ui.py

Interface CLI pour la création d'un tournoi et l'affichage de son résumé.
"""
from __future__ import annotations

from datetime import date

from models.config     import ParticipantType
from models.tournament import Tournament
from .utils import clear, pause, choose, input_str


def create_tournament() -> Tournament:
    """
    Guide l'utilisateur pour créer un nouveau tournoi.

    Returns:
        Tournament: Le tournoi créé.
    """
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


def show_summary(tournament: Tournament):
    """
    Affiche le résumé complet du tournoi.

    Args:
        tournament (Tournament): Le tournoi à afficher.
    """
    clear()
    print(tournament.summary())
    pause()
