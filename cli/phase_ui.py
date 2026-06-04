"""
cli/phase_ui.py

Interface CLI pour la création et la gestion des phases de tournoi.
"""
from __future__ import annotations

from models.config     import TournamentType
from models.tournament import Tournament
from .utils import clear, pause, separator, input_int, input_str, choose


_PHASE_TYPES = [
    ("Poules (round-robin)",  TournamentType.POOL),
    ("Élimination directe",   TournamentType.SINGLE_ELIM),
    ("Double élimination",    TournamentType.DOUBLE_ELIM),
    ("Système suisse",        TournamentType.SWISS),
]


def add_phase(tournament: Tournament):
    """
    Guide l'utilisateur pour ajouter une nouvelle phase au tournoi.

    Args:
        tournament (Tournament): Le tournoi cible.
    """
    clear()
    print("=== AJOUTER UNE PHASE ===\n")

    name = input_str("Nom de la phase (ex: Phase de poules, Finale) : ")

    print("\nFormat de la phase :")
    idx             = choose([label for label, _ in _PHASE_TYPES])
    tournament_type = _PHASE_TYPES[idx][1]

    num_pools = 2
    if tournament_type == TournamentType.POOL:
        num_pools = input_int("Nombre de poules : ", min_val=1)

    nb_available = _available_participants_count(tournament)
    print(f"\n{nb_available} participant(s) disponible(s) pour cette phase.")
    num_qualifiers = input_int(
        "Nombre de qualifiés pour la phase suivante (0 = phase finale) : ",
        min_val=0,
        max_val=nb_available,
    )

    use_previous = True
    if tournament.phases:
        print("\nParticipants de cette phase :")
        use_previous = choose([
            "Les qualifiés de la phase précédente",
            "Tous les participants inscrits",
        ]) == 0

    try:
        seeded = tournament.phases[-1].qualifiers() if tournament.phases else None
        phase = tournament.add_phase(
            name                         = name,
            tournament_type              = tournament_type,
            num_qualifiers               = num_qualifiers,
            num_pools                    = num_pools,
            use_qualifiers_from_previous = use_previous,
            seeded                       = seeded,
        )
        print(f"\nPhase '{name}' créée avec {len(phase.matches)} match(s).")
    except (ValueError, RuntimeError) as e:
        print(f"\nErreur : {e}")

    pause()


def next_round(tournament: Tournament):
    """
    Génère le tour suivant pour les formats multi-tours (suisse, élimination directe).

    Args:
        tournament (Tournament): Le tournoi en cours.
    """
    clear()
    phase = tournament.current_phase

    if phase is None:
        print("Aucune phase en cours.")
        pause()
        return

    if phase.tournament_type == TournamentType.POOL:
        print("Le format Poules génère tous les matchs dès le départ, pas de tour suivant.")
        pause()
        return

    try:
        phase.next_round()
        pending = [m for m in phase.matches if m.state == "About to start"]
        print(f"Tour suivant généré : {len(pending)} nouveau(x) match(s).")
    except RuntimeError as e:
        print(f"Erreur : {e}")

    pause()


def _available_participants_count(tournament: Tournament) -> int:
    """
    Retourne le nombre de participants disponibles pour la prochaine phase.
    Si une phase précédente existe, c'est le nombre de qualifiés.
    Sinon, c'est le nombre total d'inscrits.

    Args:
        tournament (Tournament): Le tournoi concerné.

    Returns:
        int: Nombre de participants disponibles.
    """
    if tournament.phases:
        previous = tournament.phases[-1]
        return previous.num_qualifiers if previous.num_qualifiers > 0 else len(tournament.participants)
    return len(tournament.participants)