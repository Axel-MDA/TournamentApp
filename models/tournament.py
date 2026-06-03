"""
tournament.py

Définit la classe Tournament, point d'entrée principal de l'application.

Un tournoi regroupe des participants (équipes ou joueurs individuels)
et orchestre une succession de phases chaînées. La transition entre phases
est gérée automatiquement : la phase suivante reçoit les qualifiés
de la phase précédente.
"""
from __future__ import annotations

from datetime import date
from typing import Union, TYPE_CHECKING

from models.config import ParticipantType, TournamentType
from models.phase  import Phase

if TYPE_CHECKING:
    from models.teams   import Team
    from models.players import Player

Participant = Union["Team", "Player"]


class Tournament:
    """
    Représente un tournoi complet composé d'une ou plusieurs phases chaînées.

    Attributes:
        name             (str)               : Nom du tournoi.
        sport            (str)               : Sport pratiqué.
        participant_type (ParticipantType)   : TEAM ou PLAYER.
        start_date       (date)              : Date de début.
        end_date         (date | None)       : Date de fin (optionnelle).
        participants     (list[Participant]) : Participants inscrits.
        phases           (list[Phase])       : Phases dans l'ordre chronologique.
        status           (str)               : 'upcoming', 'ongoing' ou 'finished'.
    """

    def __init__(
        self,
        name: str,
        sport: str,
        participant_type: ParticipantType,
        start_date: date,
        end_date: date = None,
    ):
        """
        Initialise un tournoi.

        Args:
            name             (str)             : Nom du tournoi.
            sport            (str)             : Sport pratiqué.
            participant_type (ParticipantType) : Type de participants (TEAM ou PLAYER).
            start_date       (date)            : Date de début.
            end_date         (date | None)     : Date de fin (optionnelle).
        """
        self.name             = name
        self.sport            = sport
        self.participant_type = participant_type
        self.start_date       = start_date
        self.end_date         = end_date
        self.participants:    list[Participant] = []
        self.phases:          list[Phase]       = []
        self.status           = "upcoming"

    def register(self, participant: Participant) -> None:
        """
        Inscrit un participant au tournoi.

        Args:
            participant (Participant): L'équipe ou le joueur à inscrire.

        Raises:
            TypeError : Si le type du participant ne correspond pas à participant_type.
            ValueError: Si le participant est déjà inscrit.
        """
        from teams   import Team
        from players import Player

        expected = Team if self.participant_type == ParticipantType.TEAM else Player
        if not isinstance(participant, expected):
            raise TypeError(
                f"Ce tournoi accepte uniquement des {expected.__name__}. "
                f"Reçu : {type(participant).__name__}."
            )
        if participant in self.participants:
            raise ValueError(f"{participant.name} est déjà inscrit au tournoi.")

        self.participants.append(participant)

    def unregister(self, participant: Participant) -> None:
        """
        Désinscrit un participant du tournoi.

        Args:
            participant (Participant): Le participant à retirer.

        Raises:
            ValueError: Si le participant n'est pas inscrit.
        """
        if participant not in self.participants:
            raise ValueError(f"{participant.name} n'est pas inscrit au tournoi.")
        self.participants.remove(participant)

    def add_phase(
        self,
        name: str,
        tournament_type: TournamentType,
        num_qualifiers: int = 0,
        num_pools: int = 2,
        use_qualifiers_from_previous: bool = True,
    ) -> Phase:
        """
        Ajoute une nouvelle phase au tournoi et génère ses matchs.

        Par défaut, la phase utilise les qualifiés de la phase précédente.
        Pour la première phase, tous les participants inscrits sont utilisés.

        Args:
            name                         (str)            : Nom de la phase.
            tournament_type              (TournamentType) : Format de la phase.
            num_qualifiers               (int)            : Qualifiés pour la phase suivante. 0 = phase finale.
            num_pools                    (int)            : Nombre de poules (format POOL).
            use_qualifiers_from_previous (bool)           : Si True, utilise les qualifiés de la phase précédente. Si False, utilise tous les inscrits.

        Returns:
            Phase: La phase créée et ajoutée au tournoi.

        Raises:
            ValueError:   Si aucun participant n'est inscrit au tournoi.
            RuntimeError: Si la phase précédente n'est pas encore terminée.
            RuntimeError: Si la phase précédente n'a défini aucun qualifié.
        """
        if not self.participants:
            raise ValueError("Aucun participant inscrit au tournoi.")

        if self.phases and use_qualifiers_from_previous:
            previous = self.phases[-1]
            if not previous.is_complete:
                raise RuntimeError(
                    f"La phase '{previous.name}' n'est pas encore terminée."
                )
            phase_participants = previous.qualifiers()
            if not phase_participants:
                raise RuntimeError(
                    f"La phase '{previous.name}' n'a défini aucun qualifié (num_qualifiers=0)."
                )
        else:
            phase_participants = self.participants[:]

        phase = Phase(
            name            = name,
            tournament_type = tournament_type,
            participants    = phase_participants,
            num_qualifiers  = num_qualifiers,
            num_pools       = num_pools,
        )
        self.phases.append(phase)
        self.status = "ongoing"
        return phase

    @property
    def current_phase(self) -> Phase | None:
        """Retourne la phase en cours (dernière phase non terminée)."""
        for phase in reversed(self.phases):
            if not phase.is_complete:
                return phase
        return None

    @property
    def is_complete(self) -> bool:
        """Retourne True si toutes les phases du tournoi sont terminées."""
        return bool(self.phases) and all(p.is_complete for p in self.phases)

    def finish(self) -> None:
        """
        Clôture le tournoi.

        Raises:
            RuntimeError: Si toutes les phases ne sont pas encore terminées.
        """
        if not self.is_complete:
            raise RuntimeError("Impossible de clôturer : des phases sont encore en cours.")
        self.status = "finished"

    def winner(self) -> Participant | None:
        """
        Retourne le vainqueur du tournoi (premier du classement de la dernière phase).

        Returns:
            Participant | None: Le vainqueur, ou None si le tournoi n'est pas terminé.
        """
        if not self.is_complete or not self.phases:
            return None
        return self.phases[-1].standings()[0]

    def __repr__(self) -> str:
        return (
            f"Tournament(name={self.name!r}, sport={self.sport!r}, "
            f"status={self.status!r}, "
            f"participants={len(self.participants)}, phases={len(self.phases)})"
        )

    def summary(self) -> str:
        """
        Retourne un résumé complet du tournoi : infos générales et résumé de chaque phase.

        Returns:
            str: Résumé formaté.
        """
        lines = [
            f"\n{'#'*40}",
            f"  TOURNOI : {self.name}",
            f"  Sport   : {self.sport}",
            f"  Statut  : {self.status}",
            f"  Début   : {self.start_date}",
            f"  Fin     : {self.end_date or 'Non définie'}",
            f"  Participants inscrits : {len(self.participants)}",
            f"{'#'*40}",
        ]
        for phase in self.phases:
            lines.append(phase.summary())

        w = self.winner()
        if w:
            lines.append(f"\nVainqueur : {w.name}")

        return "\n".join(lines)