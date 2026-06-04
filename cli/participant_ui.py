"""
cli/participant_ui.py

Interface CLI pour l'inscription des participants (joueurs ou équipes).
"""
from __future__ import annotations

from datetime import date

from models.config     import ParticipantType
from models.players    import Player
from models.teams      import Team
from models.tournament import Tournament
from .utils import clear, pause, separator, input_str, input_int, input_yn, choose


def register_participants(tournament: Tournament):
    """
    Redirige vers l'inscription d'équipes ou de joueurs selon le type du tournoi.

    Args:
        tournament (Tournament): Le tournoi cible.
    """
    if tournament.participant_type == ParticipantType.TEAM:
        _register_teams(tournament)
    else:
        _register_players(tournament)


def _register_players(tournament: Tournament):
    """
    Interface d'inscription de joueurs individuels.

    Args:
        tournament (Tournament): Le tournoi cible.
    """
    clear()
    print("=== INSCRIRE DES JOUEURS ===\n")

    while True:
        print(f"Joueurs inscrits : {len(tournament.participants)}")
        separator()

        name = input("Nom du joueur (ou 'stop' pour terminer) : ").strip()
        if name.lower() == "stop":
            break
        if not name:
            print("  Le nom ne peut pas être vide.")
            continue

        license_number = input("Numéro de licence (optionnel) : ").strip() or f"LIC-{name[:3].upper()}"

        handed = None
        h = input("Latéralité — (g)auche / (d)roite / (entrée pour passer) : ").strip().lower()
        if h == "g":
            handed = "left"
        elif h == "d":
            handed = "right"

        player = Player(
            license_number = license_number,
            name           = name,
            date_of_birth  = date(2000, 1, 1),
            handed         = handed,
        )

        try:
            tournament.register(player)
            print(f"Joueur '{name}' inscrit.\n")
        except (TypeError, ValueError) as e:
            print(f"  Erreur : {e}\n")

    print(f"\n{len(tournament.participants)} joueur(s) inscrit(s).")
    pause()


def _register_teams(tournament: Tournament):
    """
    Interface d'inscription d'équipes.

    Args:
        tournament (Tournament): Le tournoi cible.
    """
    clear()
    print("=== INSCRIRE DES ÉQUIPES ===\n")

    while True:
        print(f"Équipes inscrites : {len(tournament.participants)}")
        separator()

        name = input("Nom de l'équipe (ou 'stop' pour terminer) : ").strip()
        if name.lower() == "stop":
            break
        if not name:
            print("  Le nom ne peut pas être vide.")
            continue

        club = input_str("Club : ")
        city = input_str("Ville : ")
        team = Team(name=name, club=club, city=city)

        if input_yn("Ajouter des joueurs maintenant ? (o/n) : "):
            _add_players_to_team(team)

        try:
            tournament.register(team)
            print(f"Équipe '{name}' inscrite.\n")
        except (TypeError, ValueError) as e:
            print(f"  Erreur : {e}\n")

    print(f"\n{len(tournament.participants)} équipe(s) inscrite(s).")
    pause()


def _add_players_to_team(team: Team):
    """
    Interface d'ajout de joueurs à une équipe.

    Args:
        team (Team): L'équipe cible.
    """
    while True:
        pname = input("  Nom du joueur (ou 'stop') : ").strip()
        if pname.lower() == "stop":
            break
        if not pname:
            print("  Le nom ne peut pas être vide.")
            continue

        number = input_int("  Numéro de maillot : ", min_val=1)
        player = Player(
            license_number = f"LIC-{pname[:3].upper()}-{number}",
            name           = pname,
            date_of_birth  = date(2000, 1, 1),
        )
        try:
            team.add_player(player, number)
            print(f"  {pname} ajouté(e) avec le numéro {number}.")
        except ValueError as e:
            print(f"  Erreur : {e}")
