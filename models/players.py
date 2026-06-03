"""
players.py

Définit les classes liées aux joueurs :
    - Player : représente un joueur avec ses informations personnelles
               et son appartenance à une équipe.
"""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.teams import Team


class Player:
    """
    Représente un joueur inscrit dans le tournoi.

    Attributes:
        license_number (str)  : Numéro de licence unique du joueur.
        name           (str)  : Nom complet du joueur.
        date_of_birth  (date) : Date de naissance (objet datetime.date).
        handed         (str)  : Latéralité du joueur ('left', 'right', ou None).
        _team          (Team) : Référence privée vers l'équipe du joueur (None si sans équipe).
    """

    def __init__(
        self,
        license_number: str,
        name: str,
        date_of_birth: date,
        handed: str = None,
    ):
        """
        Initialise un joueur.

        Args:
            license_number (str)  : Numéro de licence unique.
            name           (str)  : Nom complet du joueur.
            date_of_birth  (date) : Date de naissance (datetime.date).
            handed         (str)  : Latéralité ('left', 'right', ou None).
        """
        self.license_number = license_number
        self.name           = name
        self.date_of_birth  = date_of_birth
        self.handed         = handed
        self.points         = 0.0
        self._team: Team | None = None

    # ------------------------------------------------------------------
    # Propriétés
    # ------------------------------------------------------------------

    @property
    def team(self) -> Team | None:
        """Retourne l'équipe à laquelle appartient le joueur, ou None."""
        return self._team

    @team.setter
    def team(self, team: Team | None) -> None:
        """
        Affecte le joueur à une équipe.

        Args:
            team (Team | None): L'équipe cible, ou None pour désaffecter.
        """
        self._team = team

    @property
    def age(self) -> int:
        """Calcule et retourne l'âge du joueur en années."""
        today = date.today()
        dob   = self.date_of_birth
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # ------------------------------------------------------------------
    # Représentation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        team_name = self._team.name if self._team else "No team"
        return (
            f"Player(name={self.name!r}, license={self.license_number!r}, "
            f"age={self.age}, team={team_name!r})"
        )