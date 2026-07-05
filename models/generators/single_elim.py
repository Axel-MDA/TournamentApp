"""
generators/single_elim.py

Générateur de matchs pour le format élimination directe simple.

Logique :
    - L'effectif est ramené à la puissance de 2 immédiatement inférieure
      ou égale via un tour de barrage ("play-in").
        Exemple : 20 participants -> puissance de 2 inférieure = 16
                  -> 20 - 16 = 4 matchs de barrage (8 joueurs)
                  -> les 12 joueurs restants reçoivent un bye direct
                  -> le tour principal compte bien 16 participants.
    - Les byes sont attribués aux participants les mieux classés
      (triés par points décroissants). En cas d'égalité de points,
      le choix est départagé par tirage aléatoire.
    - Les barrages opposent les participants les moins bien classés,
      appariés aléatoirement entre eux.
    - Si l'effectif est déjà une puissance de 2, aucun barrage n'est
      nécessaire : comportement inchangé (premier tour direct).
    - Les tours suivants sont générés via next_round() après saisie
      des résultats.

Important : le classement (avec tirage aléatoire des égalités) doit être
calculé UNE SEULE FOIS et partagé entre la liste des participants en
barrage et celle des byes directs. Calculer ces deux listes séparément
via deux tirages aléatoires indépendants romprait leur complémentarité
et pourrait faire apparaître un même participant des deux côtés (ou
qu'un perdant du barrage soit ensuite confondu avec un bye). C'est
pourquoi build_bracket_plan() est le point d'entrée unique utilisé à la
fois par generate() et par get_direct_bye_participants().
"""
from __future__ import annotations

import random
from typing import Union, TYPE_CHECKING, NamedTuple

from ..match import Match

if TYPE_CHECKING:
    from ..teams   import Team
    from ..players import Player

Participant = Union["Team", "Player"]


class BracketPlan(NamedTuple):
    """Résultat du calcul de répartition barrage / byes pour un tirage donné."""
    playin_players: list   # participants qui disputeront le barrage
    direct_byes:    list   # participants qualifiés d'office pour le tour principal


def build_bracket_plan(participants: list[Participant]) -> BracketPlan:
    """
    Calcule, en un seul classement (un seul tirage aléatoire pour les
    égalités), la répartition entre participants de barrage et byes
    directs. C'est le point d'entrée unique à utiliser : appeler le
    classement deux fois séparément romprait la complémentarité des
    deux listes.

    Args:
        participants (list[Participant]): Participants du tournoi.

    Returns:
        BracketPlan: playin_players (liste vide si effectif déjà
                    puissance de 2) et direct_byes (liste vide si
                    effectif déjà puissance de 2).
    """
    n = len(participants)
    if n < 2:
        return BracketPlan(playin_players=[], direct_byes=[])

    lower_power = _largest_power_of_two_leq(n)
    nb_playin_matches = n - lower_power

    if nb_playin_matches == 0:
        return BracketPlan(playin_players=[], direct_byes=[])

    ranked = _rank_with_random_tiebreak(participants)
    nb_playin_players = nb_playin_matches * 2

    # Les moins bien classés (fin de liste) disputent le barrage.
    playin_players = ranked[len(ranked) - nb_playin_players:]
    # Les mieux classés (début de liste) reçoivent un bye direct.
    direct_byes = ranked[: len(ranked) - nb_playin_players]

    return BracketPlan(playin_players=playin_players, direct_byes=direct_byes)


def generate(participants: list[Participant]) -> list[Match]:
    """
    Génère le tour de barrage (play-in) de l'élimination directe, si
    nécessaire, en ramenant l'effectif à la puissance de 2 inférieure.

    Si l'effectif est déjà une puissance de 2, retourne directement les
    matchs du tour principal (aucun barrage nécessaire).

    Args:
        participants (list[Participant]): Participants du tournoi.

    Returns:
        list[Match]: Les matchs du tour de barrage, ou directement ceux
                    du tour principal si l'effectif est une puissance de 2.

    Raises:
        ValueError: Si le nombre de participants est inférieur à 2.
    """
    n = len(participants)
    if n < 2:
        raise ValueError("L'élimination directe nécessite au moins 2 participants.")

    plan = build_bracket_plan(participants)

    if not plan.playin_players:
        # Effectif déjà une puissance de 2 : pas de barrage, tour direct.
        shuffled = participants[:]
        random.shuffle(shuffled)
        return _pair_up(shuffled)

    shuffled_playin = plan.playin_players[:]
    random.shuffle(shuffled_playin)
    return _pair_up(shuffled_playin)


def get_direct_bye_participants(
    participants: list[Participant],
    plan: BracketPlan | None = None,
) -> list[Participant]:
    """
    Retourne les participants qui reçoivent un bye direct pour le tour
    principal (pas de barrage), c'est-à-dire les mieux classés une fois
    l'effectif ramené à la puissance de 2 inférieure.

    Args:
        participants (list[Participant]): Participants du tournoi.
        plan (BracketPlan | None): Plan déjà calculé par
                    build_bracket_plan(), à réutiliser pour garantir la
                    cohérence avec les matchs de barrage déjà générés.
                    Si None, un nouveau plan est recalculé (avec un
                    nouveau tirage aléatoire des égalités — à éviter si
                    generate() a déjà été appelé séparément).

    Returns:
        list[Participant]: Liste vide si l'effectif est déjà une
                           puissance de 2 (aucun bye nécessaire).
    """
    if plan is None:
        plan = build_bracket_plan(participants)
    return plan.direct_byes


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

    return _pair_up(winners)


def _pair_up(participants: list[Participant]) -> list[Match]:
    """Apparie une liste de participants deux par deux dans l'ordre donné."""
    matches: list[Match] = []
    for i in range(0, len(participants) - 1, 2):
        matches.append(Match([participants[i], participants[i + 1]]))
    return matches


def _largest_power_of_two_leq(n: int) -> int:
    """Retourne la plus grande puissance de 2 inférieure ou égale à n."""
    power = 1
    while power * 2 <= n:
        power *= 2
    return power


def _rank_with_random_tiebreak(participants: list[Participant]) -> list[Participant]:
    """
    Trie les participants par points décroissants. En cas d'égalité de
    points, l'ordre relatif est départagé par tirage aléatoire.

    Args:
        participants (list[Participant]): Participants à classer.

    Returns:
        list[Participant]: Participants triés, du mieux classé au moins
                           bien classé.
    """
    shuffled = participants[:]
    random.shuffle(shuffled)  # casse les égalités de façon aléatoire
    return sorted(shuffled, key=lambda p: p.points, reverse=True)