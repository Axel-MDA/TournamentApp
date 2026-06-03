"""
generators/single_elim.py

Générateur de matchs pour le format élimination directe simple.

Logique :
    - Les participants sont mélangés aléatoirement (tirage au sort).
    - Ils sont appariés deux par deux pour constituer le premier tour.
    - Si le nombre de participants est impair, le dernier reçoit un bye
      (qualification automatique au tour suivant sans jouer).
    - Les tours suivants sont générés via next_round() après saisie
      des résultats du tour précédent.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from models.match import Match

if TYPE_CHECKING:
    from models.match import Participant


def generate(participants: list[Participant]) -> list[Match]:
    """
    Génère le premier tour de l'élimination directe.

    Args:
        participants (list[Participant]): Participants du tournoi.

    Returns:
        list[Match]: Les matchs du premier tour.

    Raises:
        ValueError: Si le nombre de participants est inférieur à 2.
    """
    if len(participants) < 2:
        raise ValueError("L'élimination directe nécessite au moins 2 participants.")

    shuffled = participants[:]
    random.shuffle(shuffled)

    matches: list[Match] = []
    for i in range(0, len(shuffled) - 1, 2):
        matches.append(Match([shuffled[i], shuffled[i + 1]]))

    return matches


def next_round(current_matches: list[Match]) -> list[Match]:
    """
    Génère le tour suivant à partir des gagnants du tour précédent.

    Args:
        current_matches (list[Match]): Matchs du tour précédent, tous terminés.

    Returns:
        list[Match]: Les matchs du tour suivant.

    Raises:
        RuntimeError: Si des matchs du tour précédent ne sont pas terminés.
        RuntimeError: Si le tournoi est déjà terminé (un seul gagnant restant).
    """
    unfinished = [m for m in current_matches if m.state != "Finished"]
    if unfinished:
        raise RuntimeError(
            f"{len(unfinished)} match(s) du tour précédent ne sont pas encore terminés."
        )

    winners = [m.winner for m in current_matches if m.winner is not None]

    if len(winners) < 2:
        raise RuntimeError("Le tournoi est terminé, il ne reste qu'un seul participant.")

    matches: list[Match] = []
    for i in range(0, len(winners) - 1, 2):
        matches.append(Match([winners[i], winners[i + 1]]))

    return matches