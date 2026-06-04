"""
generators/swiss.py

Générateur de matchs pour le système suisse.

Logique :
    - Le premier tour est tiré au sort aléatoirement.
    - Les tours suivants apparient les participants aux scores les plus proches.
    - Un participant ne peut pas affronter deux fois le même adversaire.
      Si un appariement idéal est impossible, on décale d'un rang.
    - Le nombre de tours est libre — c'est l'organisateur qui décide quand arrêter.
"""
from __future__ import annotations

import random
from typing import Union, TYPE_CHECKING

from ..match import Match

if TYPE_CHECKING:
    from ..teams   import Team
    from ..players import Player

Participant = Union["Team", "Player"]


def generate(participants: list[Participant]) -> list[Match]:
    """
    Génère le premier tour du système suisse (tirage aléatoire).

    Args:
        participants (list[Participant]): Participants du tournoi.

    Returns:
        list[Match]: Les matchs du premier tour.

    Raises:
        ValueError: Si le nombre de participants est inférieur à 2.
    """
    if len(participants) < 2:
        raise ValueError("Le système suisse nécessite au moins 2 participants.")

    shuffled = participants[:]
    random.shuffle(shuffled)

    matches: list[Match] = []
    for i in range(0, len(shuffled) - 1, 2):
        matches.append(Match([shuffled[i], shuffled[i + 1]]))

    return matches


def next_round(
    participants: list[Participant],
    all_previous_matches: list[Match],
) -> list[Match]:
    """
    Génère le prochain tour du système suisse.

    Apparie les participants par scores décroissants en évitant les rematches.
    Si un appariement idéal est impossible, on décale d'un rang.

    Args:
        participants         (list[Participant]) : Tous les participants de la phase.
        all_previous_matches (list[Match])       : Tous les matchs déjà joués.

    Returns:
        list[Match]: Les matchs du prochain tour.

    Raises:
        RuntimeError: Si des matchs précédents ne sont pas encore terminés.
    """
    unfinished = [m for m in all_previous_matches if m.state != "Finished"]
    if unfinished:
        raise RuntimeError(
            f"{len(unfinished)} match(s) du tour précédent ne sont pas encore terminés."
        )

    already_played      = _build_history(all_previous_matches)
    sorted_participants = sorted(participants, key=lambda p: p.points, reverse=True)
    remaining           = sorted_participants[:]
    matches: list[Match] = []

    while len(remaining) >= 2:
        p1     = remaining.pop(0)
        paired = False

        for i, p2 in enumerate(remaining):
            if p2 not in already_played.get(p1, set()):
                remaining.pop(i)
                matches.append(Match([p1, p2]))
                paired = True
                break

        if not paired:
            p2 = remaining.pop(0)
            matches.append(Match([p1, p2]))

    return matches


def _build_history(matches: list[Match]) -> dict[Participant, set[Participant]]:
    """
    Construit un dictionnaire des adversaires déjà rencontrés pour chaque participant.

    Args:
        matches (list[Match]): Historique des matchs joués.

    Returns:
        dict[Participant, set[Participant]]: {participant: {adversaires déjà rencontrés}}.
    """
    history: dict[Participant, set[Participant]] = {}
    for m in matches:
        a, b = m.opponents
        history.setdefault(a, set()).add(b)
        history.setdefault(b, set()).add(a)
    return history