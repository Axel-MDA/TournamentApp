"""
cli/match_ui.py

Interface CLI pour la saisie des résultats et l'affichage des matchs.
"""
from __future__ import annotations

from models.tournament import Tournament
from .utils import clear, pause, separator, input_int


def enter_results(tournament: Tournament):
    """
    Permet de saisir les résultats des matchs en attente de la phase en cours.

    Args:
        tournament (Tournament): Le tournoi en cours.
    """
    clear()
    phase = tournament.current_phase

    if phase is None:
        print("Aucune phase en cours.")
        pause()
        return

    print(f"=== SAISIR LES RÉSULTATS — {phase.name} ===\n")

    pending = [m for m in phase.matches if m.state != "Finished"]
    if not pending:
        print("Tous les matchs de cette phase sont déjà terminés.")
        pause()
        return

    print(f"{len(pending)} match(s) en attente.\n")

    for i, match in enumerate(pending, start=1):
        a, b = match.opponents
        separator()
        print(f"Match {i}/{len(pending)} : {a.name}  vs  {b.name}")

        while True:
            skip = input("Passer ce match ? (o/n) : ").strip().lower()
            if skip in ("o", "n"):
                break
            print("  Réponds par 'o' (oui) ou 'n' (non).")

        if skip == "o":
            continue

        score_a = input_int(f"  Score de {a.name} : ", min_val=0)
        score_b = input_int(f"  Score de {b.name} : ", min_val=0)

        match.set_score(score_a, score_b)
        match.set_state("Finished")
        match.update_points()

    print("\nRésultats enregistrés.")
    pause()


def show_standings(tournament: Tournament):
    """
    Affiche le classement de la phase en cours (ou de la dernière phase).

    Args:
        tournament (Tournament): Le tournoi concerné.
    """
    clear()
    phase = tournament.current_phase or (tournament.phases[-1] if tournament.phases else None)

    if phase is None:
        print("Aucune phase créée.")
        pause()
        return

    print(f"=== CLASSEMENT — {phase.name} ===\n")
    for i, p in enumerate(phase.standings(), start=1):
        print(f"  {i:>2}. {p.name:<25} {p.points} pts")

    pause()


def show_matches(tournament: Tournament):
    """
    Affiche tous les matchs de la phase en cours (ou de la dernière phase).

    Args:
        tournament (Tournament): Le tournoi concerné.
    """
    clear()
    phase = tournament.current_phase or (tournament.phases[-1] if tournament.phases else None)

    if phase is None:
        print("Aucune phase créée.")
        pause()
        return

    print(f"=== MATCHS — {phase.name} ===\n")

    if phase.pools:
        for idx, pool in enumerate(phase.pools, start=1):
            names = ", ".join(p.name for p in pool)
            print(f"Poule {idx} : {names}")
        print()

    for match in phase.matches:
        a, b = match.opponents
        if match.state == "Finished":
            winner_tag = f"  ← {match.winner.name}" if match.winner else "  (nul)"
            print(f"  [TERMINÉ]    {a.name} {match.score[0]} - {match.score[1]} {b.name}{winner_tag}")
        else:
            print(f"  [EN ATTENTE] {a.name}  vs  {b.name}")

    pause()
