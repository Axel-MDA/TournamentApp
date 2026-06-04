"""
generators/pool.py

Générateur de matchs pour le format poules (round-robin).

Logique :
    - Les participants sont mélangés aléatoirement puis répartis en poules équilibrées.
    - Si le nombre de participants n'est pas divisible par num_pools,
      les premières poules reçoivent un participant supplémentaire.
    - Dans chaque poule, chaque participant affronte tous les autres une fois.
"""
from __future__ import annotations

import random
from typing import Union, TYPE_CHECKING

from ..match import Match

if TYPE_CHECKING:
    from ..teams   import Team
    from ..players import Player

Participant = Union["Team", "Player"]


def generate(
    participants: list[Participant],
    num_pools: int = 2,
) -> tuple[list[list[Participant]], list[Match]]:
    """
    Répartit les participants en poules et génère les matchs round-robin.

    Args:
        participants (list[Participant]) : Participants à répartir.
        num_pools    (int)               : Nombre de poules souhaitées.

    Returns:
        tuple:
            - list[list[Participant]] : Les poules constituées.
            - list[Match]             : Tous les matchs générés.

    Raises:
        ValueError: Si num_pools est inférieur à 1.
        ValueError: Si une poule se retrouverait avec moins de 2 participants.
    """
    if num_pools < 1:
        raise ValueError("Le nombre de poules doit être au moins 1.")

    n = len(participants)
    if n // num_pools < 2:
        raise ValueError(
            f"Impossible de créer {num_pools} poules avec seulement "
            f"{n} participants (minimum 2 par poule)."
        )

    shuffled  = participants[:]
    random.shuffle(shuffled)

    base_size = n // num_pools
    extra     = n % num_pools
    pools: list[list[Participant]] = []
    idx = 0

    for i in range(num_pools):
        size = base_size + (1 if i < extra else 0)
        pools.append(shuffled[idx : idx + size])
        idx += size

    matches: list[Match] = []
    for pool in pools:
        for i in range(len(pool)):
            for j in range(i + 1, len(pool)):
                matches.append(Match([pool[i], pool[j]]))

    return pools, matches