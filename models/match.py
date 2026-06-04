"""
match.py

Définit la classe Match représentant une rencontre entre deux participants.
Un participant peut être une équipe (Team) ou un joueur individuel (Player).
"""
from __future__ import annotations

from typing import Union, TYPE_CHECKING
from . import config as cfg

if TYPE_CHECKING:
    from .teams   import Team
    from .players import Player

Participant = Union["Team", "Player"]


class Match:
    """
    Représente un match entre deux participants (équipes ou joueurs individuels).

    Attributes:
        opponents (list[Participant]) : Les deux participants [a, b].
        score     (list[int])         : Score de chaque participant [score_a, score_b].
        state     (str)               : État du match parmi STATES.
    """

    STATES = ("About to start", "In progress", "Finished")

    def __init__(self, opponents: list[Participant]):
        """
        Initialise un match entre deux participants.

        Args:
            opponents (list[Participant]): Liste de deux participants s'affrontant.

        Raises:
            ValueError: Si le nombre de participants n'est pas exactement 2.
        """
        if len(opponents) != 2:
            raise ValueError("Un match doit opposer exactement 2 participants.")
        self.opponents = opponents
        self.score     = [0, 0]
        self.state     = "About to start"

    def set_score(self, score_a: int, score_b: int) -> None:
        """
        Définit le score du match.

        Args:
            score_a (int): Score du premier participant.
            score_b (int): Score du deuxième participant.

        Raises:
            ValueError: Si un score est négatif.
        """
        if score_a < 0 or score_b < 0:
            raise ValueError("Un score ne peut pas être négatif.")
        self.score = [score_a, score_b]

    def set_state(self, state: str) -> None:
        """
        Met à jour l'état du match.

        Args:
            state (str): Nouvel état parmi STATES.

        Raises:
            ValueError: Si l'état fourni n'est pas valide.
        """
        if state not in self.STATES:
            raise ValueError(f"État invalide : {state!r}. Valeurs acceptées : {self.STATES}")
        self.state = state

    def update_points(self) -> None:
        """
        Met à jour les points des deux participants selon le résultat du match.
        Ne fait rien si le match n'est pas terminé.

        Les points sont définis dans config.py :
            - Victoire : WIN_POINT
            - Défaite  : LOOSE_POINT
            - Égalité  : DRAW_POINT
        """
        if self.state == "About to start":
            print("Le match n'a pas encore commencé.")
            return
        if self.state == "In progress":
            print("Le match est en cours.")
            return

        a, b             = self.opponents
        score_a, score_b = self.score

        if score_a > score_b:
            print(f"{a.name} a gagné.")
            a.points += cfg.WIN_POINT
            b.points += cfg.LOOSE_POINT
        elif score_b > score_a:
            print(f"{b.name} a gagné.")
            a.points += cfg.LOOSE_POINT
            b.points += cfg.WIN_POINT
        else:
            print(f"Match nul entre {a.name} et {b.name}.")
            a.points += cfg.DRAW_POINT
            b.points += cfg.DRAW_POINT

    @property
    def winner(self) -> Participant | None:
        """
        Retourne le participant gagnant si le match est terminé.

        Returns:
            Participant | None: Le gagnant, ou None en cas de nul ou match non terminé.
        """
        if self.state != "Finished":
            return None
        if self.score[0] > self.score[1]:
            return self.opponents[0]
        if self.score[1] > self.score[0]:
            return self.opponents[1]
        return None

    def __repr__(self) -> str:
        a, b = self.opponents
        return (
            f"Match({a.name} {self.score[0]} - {self.score[1]} {b.name}, "
            f"state={self.state!r})"
        )