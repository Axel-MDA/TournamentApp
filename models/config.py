"""
config.py

Fichier de configuration global du tournoi.
Contient les constantes de points et les types de tournois disponibles.
"""
from __future__ import annotations

from enum import Enum


WIN_POINT   = 2
LOOSE_POINT = 0
DRAW_POINT  = 1

class TournamentType(Enum):
    """
    Enumération des formats de phase de tournoi supportés.
    Un tournoi peut enchaîner plusieurs phases de formats différents.

    Values:
        POOL        : Phase de poules — chaque participant affronte tous les autres
                      de sa poule. Les participants sont répartis automatiquement
                      en poules équilibrées.
        SWISS       : Système suisse — les participants aux scores proches
                      s'affrontent à chaque ronde.
        SINGLE_ELIM : Élimination directe — perdre = être éliminé.
        DOUBLE_ELIM : Double élimination — deux défaites pour être éliminé.
    """
    POOL        = "pool"
    SWISS       = "swiss"
    SINGLE_ELIM = "single_elimination"
    DOUBLE_ELIM = "double_elimination"

class ParticipantType(Enum):
    """
    Indique si un tournoi oppose des équipes ou des joueurs individuels.

    Values:
        TEAM   : Les participants sont des équipes (classe Team).
        PLAYER : Les participants sont des joueurs individuels (classe Player).
    """
    TEAM   = "team"
    PLAYER = "player"