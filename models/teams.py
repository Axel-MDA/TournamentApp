"""
teams.py

Définit la classe Team représentant une équipe dans le tournoi.
"""
from __future__ import annotations

from models.players import Player


class Team:
    """
    Représente une équipe participant au tournoi.

    Attributes:
        name   (str)               : Nom de l'équipe.
        club   (str)               : Club d'appartenance.
        city   (str)               : Ville de l'équipe.
        mates  (dict[int, Player]) : Joueurs indexés par leur numéro de maillot.
        points (float)             : Points accumulés dans le tournoi.
    """

    def __init__(self, name: str, club: str, city: str, mates: dict[int, Player] = None):
        """
        Initialise une équipe.

        Args:
            name   (str)                        : Nom de l'équipe.
            club   (str)                        : Club d'appartenance.
            city   (str)                        : Ville de l'équipe.
            mates  (dict[int, Player] | None)   : Joueurs initiaux sous la forme {numéro_maillot: Player}. Dictionnaire vide par défaut.
        """
        self.name   = name
        self.club   = club
        self.city   = city
        self.mates  = mates if mates is not None else {}
        self.points = 0.0

        # Affecte la référence d'équipe à chaque joueur déjà présent
        for player in self.mates.values():
            player.team = self

    def add_player(self, player: Player, number: int) -> None:
        """
        Ajoute un joueur à l'équipe avec son numéro de maillot.
        Met automatiquement à jour la référence team du joueur.

        Args:
            player (Player) : Le joueur à ajouter.
            number (int)    : Numéro de maillot à lui attribuer.

        Raises:
            ValueError: Si le joueur est déjà dans l'équipe.
            ValueError: Si le numéro de maillot est déjà pris.
        """
        if player in self.mates.values():
            raise ValueError(f"{player.name} est déjà dans l'équipe {self.name}.")
        if number in self.mates:
            raise ValueError(f"Le numéro {number} est déjà attribué dans l'équipe {self.name}.")
        self.mates[number] = player
        player.team = self

    def remove_player(self, player: Player) -> None:
        """
        Retire un joueur de l'équipe.
        Réinitialise la référence team du joueur à None.

        Args:
            player (Player): Le joueur à retirer.

        Raises:
            ValueError: Si le joueur n'est pas dans l'équipe.
        """
        number = self.get_number(player)
        if number is None:
            raise ValueError(f"{player.name} n'est pas dans l'équipe {self.name}.")
        del self.mates[number]
        player.team = None

    def get_player_by_number(self, number: int) -> Player | None:
        """
        Retourne le joueur portant un numéro de maillot donné.

        Args:
            number (int): Numéro de maillot recherché.

        Returns:
            Player | None: Le joueur correspondant, ou None si le numéro est libre.
        """
        return self.mates.get(number, None)

    def get_player_by_name(self, name: str) -> Player | None:
        """
        Recherche un joueur dans l'équipe par son nom.

        Args:
            name (str): Nom du joueur recherché.

        Returns:
            Player | None: Le joueur trouvé, ou None.
        """
        for player in self.mates.values():
            if player.name == name:
                return player
        return None

    def get_number(self, player: Player) -> int | None:
        """
        Retourne le numéro de maillot d'un joueur dans l'équipe.

        Args:
            player (Player): Le joueur dont on cherche le numéro.

        Returns:
            int | None: Le numéro de maillot, ou None si le joueur est absent.
        """
        for number, p in self.mates.items():
            if p == player:
                return number
        return None

    def change_number(self, player: Player, new_number: int) -> None:
        """
        Change le numéro de maillot d'un joueur.

        Args:
            player     (Player) : Le joueur concerné.
            new_number (int)    : Le nouveau numéro souhaité.

        Raises:
            ValueError: Si le joueur n'est pas dans l'équipe.
            ValueError: Si le nouveau numéro est déjà pris.
        """
        old_number = self.get_number(player)
        if old_number is None:
            raise ValueError(f"{player.name} n'est pas dans l'équipe {self.name}.")
        if new_number in self.mates:
            raise ValueError(f"Le numéro {new_number} est déjà attribué dans l'équipe {self.name}.")
        del self.mates[old_number]
        self.mates[new_number] = player

    @property
    def num_players(self) -> int:
        """Retourne le nombre de joueurs dans l'équipe."""
        return len(self.mates)

    def __repr__(self) -> str:
        return (
            f"Team(name={self.name!r}, club={self.club!r}, "
            f"players={self.num_players}, points={self.points})"
        )

    def roster(self) -> str:
        """
        Retourne la composition de l'équipe sous forme lisible,
        triée par numéro de maillot.

        Returns:
            str: La liste des joueurs avec leur numéro, un par ligne.
        """
        lines = [f"=== {self.name} ==="]
        for number, player in sorted(self.mates.items()):
            lines.append(f"  #{number:>2}  {player.name}")
        return "\n".join(lines)