"""
cli/app.py

Boucle principale de l'application et menu principal.
Orchestre les différents modules CLI.
"""
from __future__ import annotations

from models.tournament import Tournament
from .tournament_ui  import create_tournament, show_summary
from .participant_ui import register_participants
from .phase_ui       import add_phase, next_round
from .match_ui       import enter_results, show_standings, show_matches
from .utils          import clear, separator, choose


_MENU_OPTIONS = [
    ("Inscrire des participants",  register_participants),
    ("Ajouter une phase",          add_phase),
    ("Saisir des résultats",       enter_results),
    ("Générer le tour suivant",    next_round),
    ("Classement",                 show_standings),
    ("Voir les matchs",            show_matches),
    ("Résumé complet",             show_summary),
]


def run():
    """
    Point d'entrée de l'application.
    Crée le tournoi puis lance la boucle principale.
    """
    _print_banner()
    tournament = create_tournament()

    while _main_menu(tournament):
        pass

    print("\nÀ bientôt !")


def _main_menu(tournament: Tournament) -> bool:
    """
    Affiche le menu principal et exécute l'action choisie.

    Args:
        tournament (Tournament): Le tournoi en cours.

    Returns:
        bool: False pour quitter, True pour continuer.
    """
    clear()
    _print_status(tournament)
    separator()

    labels  = [label for label, _ in _MENU_OPTIONS] + ["Quitter"]
    idx     = choose(labels)

    if idx == len(_MENU_OPTIONS):
        return False

    _, action = _MENU_OPTIONS[idx]
    action(tournament)
    return True


def _print_banner():
    """Affiche le bandeau de démarrage."""
    print("╔══════════════════════════════╗")
    print("║      TOURNAMENT APP          ║")
    print("╚══════════════════════════════╝\n")


def _print_status(tournament: Tournament):
    """
    Affiche la ligne de statut du tournoi en haut du menu.

    Args:
        tournament (Tournament): Le tournoi en cours.
    """
    phase_info = ""
    if tournament.current_phase:
        phase_info = f" | Phase : {tournament.current_phase.name}"

    print(f"=== {tournament.name} ({tournament.sport}) ===")
    print(
        f"    Statut : {tournament.status}"
        f" | Participants : {len(tournament.participants)}"
        f" | Phases : {len(tournament.phases)}"
        f"{phase_info}"
    )
