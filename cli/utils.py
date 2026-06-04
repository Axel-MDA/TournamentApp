"""
cli/utils.py

Fonctions utilitaires partagées par tous les modules CLI.
Centralise la gestion des entrées utilisateur et l'affichage.
"""
from __future__ import annotations


def clear():
    """Saute quelques lignes pour simuler un écran propre."""
    print("\n" * 3)


def separator():
    """Affiche une ligne de séparation."""
    print("-" * 40)


def pause():
    """Attend que l'utilisateur appuie sur Entrée."""
    input("\nAppuie sur Entrée pour continuer...")


def input_int(prompt: str, min_val: int = None, max_val: int = None) -> int:
    """
    Demande un entier à l'utilisateur avec validation.

    Args:
        prompt  (str)       : Message affiché à l'utilisateur.
        min_val (int | None): Valeur minimale acceptée.
        max_val (int | None): Valeur maximale acceptée.

    Returns:
        int: L'entier saisi et validé.
    """
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  Valeur minimale : {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  Valeur maximale : {max_val}")
                continue
            return val
        except ValueError:
            print("  Entrée invalide, saisis un nombre entier.")


def input_str(prompt: str, allow_empty: bool = False) -> str:
    """
    Demande une chaîne non vide à l'utilisateur.

    Args:
        prompt      (str) : Message affiché à l'utilisateur.
        allow_empty (bool): Si True, accepte une chaîne vide.

    Returns:
        str: La chaîne saisie et nettoyée.
    """
    while True:
        val = input(prompt).strip()
        if val or allow_empty:
            return val
        print("  Ce champ ne peut pas être vide.")


def input_yn(prompt: str) -> bool:
    """
    Demande une confirmation oui/non à l'utilisateur.

    Args:
        prompt (str): Message affiché à l'utilisateur.

    Returns:
        bool: True pour 'o', False pour 'n'.
    """
    while True:
        val = input(prompt).strip().lower()
        if val in ("o", "n"):
            return val == "o"
        print("  Réponds par 'o' (oui) ou 'n' (non).")


def choose(options: list[str], prompt: str = "Ton choix : ") -> int:
    """
    Affiche un menu numéroté et retourne l'index choisi (0-based).

    Args:
        options (list[str]): Liste des options à afficher.
        prompt  (str)      : Message de saisie.

    Returns:
        int: Index de l'option choisie (commence à 0).
    """
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    return input_int(prompt, min_val=1, max_val=len(options)) - 1
