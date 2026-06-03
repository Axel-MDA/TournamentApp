"""
main.py

Interface en ligne de commande pour gérer un tournoi.
Permet de créer un tournoi, inscrire des participants,
ajouter des phases et saisir les résultats des matchs.
"""
from __future__ import annotations

from datetime import date

from models.config     import ParticipantType, TournamentType
from models.tournament import Tournament
from models.phase      import Phase
from models.teams      import Team
from models.players    import Player


def clear():
    print("\n" * 3)


def separator():
    print("-" * 40)


def pause():
    input("\nAppuie sur Entrée pour continuer...")


def input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """Demande un entier à l'utilisateur avec validation."""
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  Valeur minimale : {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  Valeur maximale : {max_val}")
                continue
            return val
        except ValueError:
            print("  Entrée invalide, saisis un nombre entier.")


def choose(options: list[str], prompt: str = "Ton choix : ") -> int:
    """Affiche un menu numéroté et retourne l'index choisi (0-based)."""
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    return input_int(prompt, min_val=1, max_val=len(options)) - 1


def create_tournament() -> Tournament:
    """Guide l'utilisateur pour créer un nouveau tournoi."""
    clear()
    print("=== CRÉER UN TOURNOI ===\n")

    name  = input("Nom du tournoi : ").strip()
    sport = input("Sport : ").strip()

    print("\nType de participants :")
    idx = choose(["Équipes", "Joueurs individuels"])
    participant_type = ParticipantType.TEAM if idx == 0 else ParticipantType.PLAYER

    start_date = date.today()

    tournament = Tournament(
        name             = name,
        sport            = sport,
        participant_type = participant_type,
        start_date       = start_date,
    )
    print(f"\nTournoi '{name}' créé !")
    pause()
    return tournament


def register_teams(tournament: Tournament):
    """Inscrit des équipes au tournoi."""
    clear()
    print("=== INSCRIRE DES ÉQUIPES ===\n")

    while True:
        print(f"Équipes inscrites : {len(tournament.participants)}")
        separator()
        name = input("Nom de l'équipe (ou 'stop' pour terminer) : ").strip()
        if name.lower() == "stop":
            break

        club = input("Club : ").strip()
        city = input("Ville : ").strip()

        team = Team(name=name, club=club, city=city)

        add_players = input("Ajouter des joueurs ? (o/n) : ").strip().lower()
        if add_players == "o":
            while True:
                pname = input("  Nom du joueur (ou 'stop') : ").strip()
                if pname.lower() == "stop":
                    break
                number = input_int("  Numéro de maillot : ", min_val=1)
                player = Player(
                    license_number = f"LIC-{pname[:3].upper()}-{number}",
                    name           = pname,
                    date_of_birth  = date(2000, 1, 1),
                )
                team.add_player(player, number)
                print(f"  {pname} ajouté(e) avec le numéro {number}.")

        try:
            tournament.register(team)
            print(f"Équipe '{name}' inscrite.\n")
        except (TypeError, ValueError) as e:
            print(f"Erreur : {e}\n")

    print(f"\n{len(tournament.participants)} équipe(s) inscrite(s).")
    pause()


def register_players(tournament: Tournament):
    """Inscrit des joueurs individuels au tournoi."""
    clear()
    print("=== INSCRIRE DES JOUEURS ===\n")

    while True:
        print(f"Joueurs inscrits : {len(tournament.participants)}")
        separator()
        name = input("Nom du joueur (ou 'stop' pour terminer) : ").strip()
        if name.lower() == "stop":
            break

        license_number = input("Numéro de licence : ").strip()
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
        )
        player.handed = handed

        try:
            tournament.register(player)
            print(f"Joueur '{name}' inscrit.\n")
        except (TypeError, ValueError) as e:
            print(f"Erreur : {e}\n")

    print(f"\n{len(tournament.participants)} joueur(s) inscrit(s).")
    pause()


def add_phase(tournament: Tournament):
    """Guide l'utilisateur pour ajouter une phase au tournoi."""
    clear()
    print("=== AJOUTER UNE PHASE ===\n")

    name = input("Nom de la phase (ex: Phase de poules, Quarts de finale) : ").strip()

    print("\nFormat de la phase :")
    type_options = [
        ("Poules (round-robin)",    TournamentType.POOL),
        ("Élimination directe",     TournamentType.SINGLE_ELIM),
        ("Double élimination",      TournamentType.DOUBLE_ELIM),
        ("Système suisse",          TournamentType.SWISS),
    ]
    idx              = choose([label for label, _ in type_options])
    tournament_type  = type_options[idx][1]

    num_pools = 2
    if tournament_type == TournamentType.POOL:
        num_pools = input_int("Nombre de poules : ", min_val=1)

    num_qualifiers = input_int(
        "Nombre de qualifiés pour la phase suivante (0 = phase finale) : ",
        min_val=0,
    )

    use_previous = True
    if tournament.phases:
        print("\nParticipants de cette phase :")
        p = choose([
            "Les qualifiés de la phase précédente",
            "Tous les participants inscrits",
        ])
        use_previous = (p == 0)

    try:
        phase = tournament.add_phase(
            name                         = name,
            tournament_type              = tournament_type,
            num_qualifiers               = num_qualifiers,
            num_pools                    = num_pools,
            use_qualifiers_from_previous = use_previous,
        )
        print(f"\nPhase '{name}' créée avec {len(phase.matches)} match(s).")
    except (ValueError, RuntimeError) as e:
        print(f"\nErreur : {e}")

    pause()


def enter_results(tournament: Tournament):
    """Permet de saisir les résultats des matchs de la phase en cours."""
    clear()
    phase = tournament.current_phase

    if phase is None:
        print("Aucune phase en cours.")
        pause()
        return

    print(f"=== SAISIR LES RÉSULTATS — {phase.name} ===\n")

    pending = [m for m in phase.matches if m.state != "Finished"]
    if not pending:
        print("Tous les matchs de cette phase sont terminés.")
        pause()
        return

    print(f"{len(pending)} match(s) à saisir :\n")

    for i, match in enumerate(pending, start=1):
        a, b = match.opponents
        separator()
        print(f"Match {i}/{len(pending)} : {a.name}  vs  {b.name}")
        skip = input("Passer ce match ? (o/n) : ").strip().lower()
        if skip == "o":
            continue

        score_a = input_int(f"  Score de {a.name} : ", min_val=0)
        score_b = input_int(f"  Score de {b.name} : ", min_val=0)

        match.set_score(score_a, score_b)
        match.set_state("Finished")
        match.update_points()

    print("\nRésultats enregistrés.")
    pause()


def next_round(tournament: Tournament):
    """Génère le tour suivant pour les formats multi-tours (suisse, élimination)."""
    clear()
    phase = tournament.current_phase

    if phase is None:
        print("Aucune phase en cours.")
        pause()
        return

    if phase.tournament_type == TournamentType.POOL:
        print("Le format Poules n'a pas de tours suivants à générer.")
        pause()
        return

    try:
        phase.next_round()
        new_matches = [m for m in phase.matches if m.state == "About to start"]
        print(f"Tour suivant généré : {len(new_matches)} nouveau(x) match(s).")
    except RuntimeError as e:
        print(f"Erreur : {e}")

    pause()


def show_standings(tournament: Tournament):
    """Affiche le classement de la phase en cours."""
    clear()
    phase = tournament.current_phase

    if phase is None:
        if tournament.phases:
            phase = tournament.phases[-1]
        else:
            print("Aucune phase créée.")
            pause()
            return

    print(f"=== CLASSEMENT — {phase.name} ===\n")
    for i, p in enumerate(phase.standings(), start=1):
        print(f"  {i:>2}. {p.name:<25} {p.points} pts")

    pause()


def show_matches(tournament: Tournament):
    """Affiche tous les matchs de la phase en cours."""
    clear()
    phase = tournament.current_phase

    if phase is None:
        if tournament.phases:
            phase = tournament.phases[-1]
        else:
            print("Aucune phase créée.")
            pause()
            return

    print(f"=== MATCHS — {phase.name} ===\n")

    for match in phase.matches:
        a, b = match.opponents
        if match.state == "Finished":
            print(f"  [TERMINÉ]  {a.name} {match.score[0]} - {match.score[1]} {b.name}")
        else:
            print(f"  [EN ATTENTE]  {a.name}  vs  {b.name}")

    pause()


def show_summary(tournament: Tournament):
    """Affiche le résumé complet du tournoi."""
    clear()
    print(tournament.summary())
    pause()


def main_menu(tournament: Tournament) -> bool:
    """
    Affiche le menu principal et exécute l'action choisie.

    Returns:
        bool: False pour quitter, True pour continuer.
    """
    clear()
    print(f"=== TOURNOI : {tournament.name} ({tournament.sport}) ===")
    print(f"    Statut : {tournament.status} | "
          f"Participants : {len(tournament.participants)} | "
          f"Phases : {len(tournament.phases)}")
    separator()

    options = [
        "Inscrire des participants",
        "Ajouter une phase",
        "Saisir des résultats",
        "Générer le tour suivant",
        "Classement",
        "Voir les matchs",
        "Résumé complet",
        "Quitter",
    ]
    idx = choose(options)

    actions = {
        0: lambda: (
            register_teams(tournament)
            if tournament.participant_type == ParticipantType.TEAM
            else register_players(tournament)
        ),
        1: lambda: add_phase(tournament),
        2: lambda: enter_results(tournament),
        3: lambda: next_round(tournament),
        4: lambda: show_standings(tournament),
        5: lambda: show_matches(tournament),
        6: lambda: show_summary(tournament),
        7: None,
    }

    action = actions[idx]
    if action is None:
        return False
    action()
    return True


def main():
    print("╔══════════════════════════════╗")
    print("║      TOURNAMENT APP          ║")
    print("╚══════════════════════════════╝\n")

    tournament = create_tournament()

    while main_menu(tournament):
        pass

    print("\nÀ bientôt !")


if __name__ == "__main__":
    main()