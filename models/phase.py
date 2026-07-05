"""
phase.py

Définit la classe Phase représentant une étape d'un tournoi.

Une phase possède son propre format (poules, élimination, suisse...),
ses propres participants et ses propres matchs. Les phases sont chaînées
dans un Tournament — la suivante reçoit les qualifiés de la précédente.
"""
from __future__ import annotations

import random
from typing import Union, TYPE_CHECKING

from .config import TournamentType
from .match  import Match
from .generators import pool        as gen_pool
from .generators import single_elim as gen_single_elim
from .generators import double_elim as gen_double_elim
from .generators import swiss       as gen_swiss

if TYPE_CHECKING:
    from .teams   import Team
    from .players import Player

Participant = Union["Team", "Player"]


class Phase:
    """
    Représente une phase d'un tournoi.

    Attributes:
        name             (str)                    : Nom de la phase.
        tournament_type  (TournamentType)          : Format de cette phase.
        participants     (list[Participant])       : Participants engagés.
        matches          (list[Match])             : Matchs générés.
        num_qualifiers   (int)                     : Qualifiés pour la phase suivante.
                                                     0 = phase finale.
        pools            (list[list[Participant]]) : Poules constituées (format POOL uniquement).
        rounds_sizes     (list[int])                : Nombre de matchs prévu à chaque tour
                                                      déjà généré (SINGLE_ELIM), dans l'ordre
                                                      chronologique. Permet de découper
                                                      correctement self.matches par tour
                                                      même quand le premier tour (barrage)
                                                      a une taille différente de n // 2.
    """

    def __init__(
        self,
        name: str,
        tournament_type: TournamentType,
        participants: list[Participant],
        num_qualifiers: int = 0,
        num_pools: int = 2,
    ):
        """
        Initialise une phase et génère automatiquement ses matchs.

        Args:
            name             (str)               : Nom de la phase.
            tournament_type  (TournamentType)    : Format de la phase.
            participants     (list[Participant]) : Participants de la phase.
            num_qualifiers   (int)               : Nombre de qualifiés pour la suite.
                                                   0 signifie phase finale.
            num_pools        (int)               : Nombre de poules (format POOL uniquement).

        Raises:
            ValueError: Si la liste de participants est vide.
            ValueError: Si num_qualifiers dépasse le nombre de participants.
        """
        if not participants:
            raise ValueError("Une phase doit avoir au moins un participant.")
        if num_qualifiers > len(participants):
            raise ValueError(
                f"num_qualifiers ({num_qualifiers}) ne peut pas dépasser "
                f"le nombre de participants ({len(participants)})."
            )

        self.name            = name
        self.tournament_type = tournament_type
        self.participants    = participants
        self.num_qualifiers  = num_qualifiers
        self.matches: list[Match]             = []
        self.pools:   list[list[Participant]] = []
        self._bye_participants: list[Participant] = []
        self._round_sizes: list[int] = []

        for p in self.participants:
            p.points = 0.0

        self._generate_matches(num_pools)
        self._update_byes()

    def _generate_matches(self, num_pools: int) -> None:
        """
        Délègue la génération des matchs au générateur correspondant au format.

        Args:
            num_pools (int): Nombre de poules (utilisé uniquement pour POOL).
        """
        if self.tournament_type == TournamentType.POOL:
            self.pools, self.matches = gen_pool.generate(self.participants, num_pools)

        elif self.tournament_type == TournamentType.SINGLE_ELIM:
            # Le plan (barrage / byes) est calculé une seule fois ici et
            # partagé entre les matchs générés et les byes directs, pour
            # garantir qu'un même participant ne puisse jamais se
            # retrouver à la fois en barrage et en bye (ce qui se
            # produisait quand chaque liste était calculée séparément
            # avec son propre tirage aléatoire des égalités).
            plan = gen_single_elim.build_bracket_plan(self.participants)

            if plan.playin_players:
                shuffled_playin = plan.playin_players[:]
                random.shuffle(shuffled_playin)
                self.matches = gen_single_elim._pair_up(shuffled_playin)
            else:
                shuffled = self.participants[:]
                random.shuffle(shuffled)
                self.matches = gen_single_elim._pair_up(shuffled)

            self._round_sizes = [len(self.matches)]
            self._direct_byes = list(plan.direct_byes)

        elif self.tournament_type == TournamentType.DOUBLE_ELIM:
            self.matches, _ = gen_double_elim.generate(self.participants)

        elif self.tournament_type == TournamentType.SWISS:
            self.matches = gen_swiss.generate(self.participants)

    def next_round(self) -> list[Match]:
        """
        Génère le tour suivant pour les formats multi-tours (SWISS, élimination directe).
        Pour POOL, tous les matchs sont générés dès le départ.

        Pour SINGLE_ELIM, si le tour qui vient de se terminer était un tour
        de barrage (play-in), les vainqueurs sont complétés par les
        participants ayant reçu un bye direct avant de constituer le tour
        principal.

        Returns:
            list[Match]: Les nouveaux matchs générés pour ce tour
                        (liste vide pour POOL ou DOUBLE_ELIM, non gérés ici).

        Raises:
            RuntimeError: Si des matchs du tour en cours ne sont pas encore terminés.
            RuntimeError: Si le format est POOL.
        """
        new_matches: list[Match] = []

        if self.tournament_type == TournamentType.POOL:
            raise RuntimeError("Le format POOL génère tous les matchs dès le départ.")

        elif self.tournament_type == TournamentType.SINGLE_ELIM:
            current_tour = self._current_tour_matches()

            if not current_tour:
                raise RuntimeError("Aucun tour en cours à clôturer.")

            unfinished = [m for m in current_tour if m.state != "Finished"]
            if unfinished:
                raise RuntimeError(
                    f"{len(unfinished)} match(s) du tour précédent ne sont pas encore terminés."
                )

            # Garde anti double-génération : si le nombre de matchs déjà
            # générés correspond exactement à un tournoi terminé (un seul
            # vainqueur final), on ne doit plus jamais regénérer de tour.
            if self.is_complete and len(current_tour) == 1:
                raise RuntimeError("Le tournoi est terminé, il ne reste qu'un seul participant.")

            # Calcule les vainqueurs UNIQUEMENT à partir des matchs de ce
            # tour précis (current_tour), jamais de l'ensemble self.matches,
            # pour garantir qu'aucun joueur éliminé à un tour antérieur ne
            # puisse être réintégré par erreur.
            current_tour_ids = {id(m) for m in current_tour}
            winners = [
                m.winner for m in self.matches
                if id(m) in current_tour_ids and m.winner is not None
            ]

            # Si des byes directs sont en attente (premier tour = barrage
            # qui vient de se terminer), on les intègre maintenant pour
            # constituer le tour principal au complet. Ces byes ne sont
            # consommés qu'une seule fois (vidés immédiatement après usage),
            # ce qui empêche toute réintégration lors d'un appel ultérieur.
            pending_byes = list(getattr(self, "_direct_byes", []))
            if pending_byes:
                pool = winners + pending_byes
                self._direct_byes = []
            else:
                pool = winners

            if len(pool) < 2:
                raise RuntimeError("Le tournoi est terminé, il ne reste qu'un seul participant.")

            new_matches = gen_single_elim._pair_up(pool)
            self.matches.extend(new_matches)
            self._round_sizes.append(len(new_matches))

        elif self.tournament_type == TournamentType.SWISS:
            new_matches = gen_swiss.next_round(self.participants, self.matches)
            self.matches.extend(new_matches)

        self._update_byes()
        return new_matches

    def _current_tour_matches(self) -> list[Match]:
        """
        Retourne les matchs du tour en cours.

        Pour SINGLE_ELIM, s'appuie sur self._round_sizes (qui connaît la
        vraie taille de chaque tour généré, y compris un éventuel premier
        tour de barrage dont la taille diffère de n // 2). Pour les autres
        formats, retombe sur l'ancienne heuristique (derniers matchs non
        terminés, ou découpage par n // 2).

        Returns:
            list[Match]: Matchs du tour en cours.
        """
        if self.tournament_type == TournamentType.SINGLE_ELIM and self._round_sizes:
            last_size = self._round_sizes[-1]
            return self.matches[-last_size:] if last_size else []

        unfinished = [m for m in self.matches if m.state != "Finished"]
        if unfinished:
            return unfinished
        tour_size = len(self.participants) // 2
        return self.matches[-tour_size:]

    @property
    def is_round_complete(self) -> bool:
        """
        Retourne True si tous les matchs du tour en cours sont terminés
        (utile pour les formats multi-tours : SINGLE_ELIM, SWISS).
        Pour POOL et DOUBLE_ELIM, équivaut à is_complete.
        """
        if not self.matches:
            return False
        current_tour = self._current_tour_matches()
        if not current_tour:
            return True
        return all(m.state == "Finished" for m in current_tour)

    def advance_round(self) -> list[Match]:
        """
        Génère automatiquement le tour suivant si le tour en cours est terminé
        et que le format le permet (SINGLE_ELIM, SWISS).
        Ne fait rien et retourne une liste vide pour POOL, DOUBLE_ELIM,
        ou si le tournoi de ce format est déjà arrivé à son terme.

        Returns:
            list[Match]: Les nouveaux matchs générés, ou liste vide si aucun
                        tour supplémentaire n'a été généré.
        """
        if self.tournament_type not in (TournamentType.SINGLE_ELIM, TournamentType.SWISS):
            return []

        if not self.is_round_complete:
            return []

        try:
            return self.next_round()
        except RuntimeError:
            # Le tournoi est terminé (single_elim : un seul gagnant restant)
            # ou autre cas non bloquant — on n'avance simplement pas.
            return []

    def _update_byes(self) -> None:
        """
        Met à jour la liste des participants actuellement en attente
        d'un bye (qualifiés sans avoir à jouer le tour en cours).

        Pour SINGLE_ELIM, reflète les byes directs déterminés à la
        création de la phase (self._direct_byes), tant qu'ils n'ont pas
        été intégrés au tour principal par next_round(). Pour les autres
        formats, conserve l'ancienne heuristique par déduction.
        """
        if self.tournament_type == TournamentType.POOL:
            self._bye_participants = []
            return

        if self.tournament_type == TournamentType.SINGLE_ELIM:
            self._bye_participants = list(getattr(self, "_direct_byes", []))
            return

        current_tour = self._current_tour_matches() if self.matches else []
        in_current_tour = set()
        for m in current_tour:
            for p in m.opponents:
                in_current_tour.add(id(p))

        if self.tournament_type == TournamentType.DOUBLE_ELIM:
            # Tous les participants engagés dans n'importe quel match
            engaged = set()
            for m in self.matches:
                for p in m.opponents:
                    engaged.add(id(p))
            self._bye_participants = [p for p in self.participants if id(p) not in engaged]
        else:
            self._bye_participants = [p for p in self.participants if id(p) not in in_current_tour]

    def standings(self) -> list[Participant]:
        """
        Retourne le classement des participants triés par points décroissants.

        Returns:
            list[Participant]: Participants du premier au dernier.
        """
        return sorted(self.participants, key=lambda p: p.points, reverse=True)

    def qualifiers(self) -> list[Participant]:
        """
        Retourne les participants qualifiés pour la phase suivante.

        Returns:
            list[Participant]: Les num_qualifiers premiers du classement.
                               Liste vide si num_qualifiers == 0 (phase finale).
        """
        if self.num_qualifiers == 0:
            return []
        return self.standings()[: self.num_qualifiers]

    @property
    def is_complete(self) -> bool:
        """Retourne True si tous les matchs de la phase sont terminés."""
        return bool(self.matches) and all(m.state == "Finished" for m in self.matches)

    def __repr__(self) -> str:
        finished = sum(1 for m in self.matches if m.state == "Finished")
        return (
            f"Phase(name={self.name!r}, type={self.tournament_type.value}, "
            f"participants={len(self.participants)}, "
            f"matches={finished}/{len(self.matches)})"
        )

    def summary(self) -> str:
        """
        Retourne un résumé lisible de la phase : classement et liste des matchs.

        Returns:
            str: Résumé formaté.
        """
        lines = [
            f"\n{'='*40}",
            f"  {self.name}  ({self.tournament_type.value})",
            f"{'='*40}",
            "\nClassement :",
        ]
        for i, p in enumerate(self.standings(), start=1):
            lines.append(f"  {i:>2}. {p.name:<20} {p.points} pts")

        lines.append("\nMatchs :")
        for m in self.matches:
            lines.append(f"  {m}")

        return "\n".join(lines)