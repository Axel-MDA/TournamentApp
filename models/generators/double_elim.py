"""
generators/double_elim.py

Générateur de matchs pour le format double élimination.

Logique :
    - Deux brackets coexistent : le winner bracket et le loser bracket.
    - Un participant est éliminé seulement après deux défaites.
    - Les perdants du winner bracket tombent dans le loser bracket.
    - Le vainqueur du loser bracket affronte le vainqueur du winner bracket
      en grande finale.

Structure interne :
    - winner_matches : matchs du bracket gagnants.
    - loser_matches  : matchs du bracket perdants.
    - Les deux listes sont gérées séparément et progressent en parallèle.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

from models.match import Match

if TYPE_CHECKING:
    from models.match import Participant


def generate(participants: list[Participant]) -> tuple[list[Match], list[Match]]:
    """
    Génère le premier tour du winner bracket.
    Le loser bracket est vide au départ — il se peuple via next_round().

    Args:
        participants (list[Participant]): Participants du tournoi.

    Returns:
        tuple:
            - list[Match] : Matchs du winner bracket (premier tour).
            - list[Match] : Matchs du loser bracket (vide au départ).

    Raises:
        ValueError: Si le nombre de participants est inférieur à 2.
    """
    if len(participants) < 2:
        raise ValueError("La double élimination nécessite au moins 2 participants.")

    shuffled = participants[:]
    random.shuffle(shuffled)

    winner_matches: list[Match] = []
    for i in range(0, len(shuffled) - 1, 2):
        winner_matches.append(Match([shuffled[i], shuffled[i + 1]]))

    return winner_matches, []


def next_winner_round(current_winner_matches: list[Match]) -> list[Match]:
    """
    Génère le tour suivant du winner bracket à partir des gagnants.

    Args:
        current_winner_matches (list[Match]): Matchs du winner bracket, tous terminés.

    Returns:
        list[Match]: Matchs du prochain tour du winner bracket.

    Raises:
        RuntimeError: Si des matchs ne sont pas encore terminés.
    """
    _check_all_finished(current_winner_matches)

    winners = [m.winner for m in current_winner_matches if m.winner is not None]

    matches: list[Match] = []
    for i in range(0, len(winners) - 1, 2):
        matches.append(Match([winners[i], winners[i + 1]]))

    return matches


def next_loser_round(
    current_winner_matches: list[Match],
    current_loser_matches: list[Match],
) -> list[Match]:
    """
    Génère le prochain tour du loser bracket.
    Les perdants du winner bracket rejoignent les survivants du loser bracket.

    Args:
        current_winner_matches (list[Match]): Matchs du winner bracket terminés.
        current_loser_matches  (list[Match]): Matchs du loser bracket terminés.

    Returns:
        list[Match]: Matchs du prochain tour du loser bracket.

    Raises:
        RuntimeError: Si des matchs ne sont pas encore terminés.
    """
    _check_all_finished(current_winner_matches)
    _check_all_finished(current_loser_matches)

    losers_from_winner = [
        (m.opponents[0] if m.winner == m.opponents[1] else m.opponents[1])
        for m in current_winner_matches
        if m.winner is not None
    ]
    survivors_from_loser = [m.winner for m in current_loser_matches if m.winner is not None]

    pool = losers_from_winner + survivors_from_loser
    random.shuffle(pool)

    matches: list[Match] = []
    for i in range(0, len(pool) - 1, 2):
        matches.append(Match([pool[i], pool[i + 1]]))

    return matches


def grand_final(winner_bracket_champion: Participant, loser_bracket_champion: Participant) -> Match:
    """
    Crée le match de grande finale entre les champions des deux brackets.

    Args:
        winner_bracket_champion (Participant): Vainqueur du winner bracket.
        loser_bracket_champion  (Participant): Vainqueur du loser bracket.

    Returns:
        Match: Le match de grande finale.
    """
    return Match([winner_bracket_champion, loser_bracket_champion])


def _check_all_finished(matches: list[Match]) -> None:
    """
    Vérifie que tous les matchs d'une liste sont terminés.

    Args:
        matches (list[Match]): Liste de matchs à vérifier.

    Raises:
        RuntimeError: Si au moins un match n'est pas terminé.
    """
    unfinished = [m for m in matches if m.state != "Finished"]
    if unfinished:
        raise RuntimeError(
            f"{len(unfinished)} match(s) ne sont pas encore terminés."
        )