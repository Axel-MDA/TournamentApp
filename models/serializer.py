"""
models/serializer.py

Sérialisation et désérialisation complète d'un tournoi au format JSON.

Structure du JSON produit :
{
  "version": "1.0",
  "tournament": {
    "name": ..., "sport": ..., "participant_type": ...,
    "start_date": ..., "end_date": ..., "status": ...,
    "participants": [ {player/team} ... ],
    "phases": [ {phase} ... ]
  }
}

Les participants sont stockés dans une liste racine avec un id unique (index),
et référencés par cet id dans les matchs — pour éviter toute duplication
et reconstruire les références d'objets correctement à l'import.
"""
from __future__ import annotations

import json
from datetime import date
from typing   import Any

from .config     import ParticipantType, TournamentType
from .players    import Player
from .teams      import Team
from .match      import Match
from .phase      import Phase
from .tournament import Tournament


# ---------------------------------------------------------------------------
# EXPORT
# ---------------------------------------------------------------------------

def to_dict(tournament: Tournament) -> dict:
    """
    Convertit un Tournament en dictionnaire sérialisable JSON.

    Args:
        tournament (Tournament): Le tournoi à exporter.

    Returns:
        dict: Représentation complète du tournoi.
    """
    # Construit un index id → participant (toutes phases confondues)
    all_participants = _collect_all_participants(tournament)
    pid_map: dict[int, int] = {id(p): i for i, p in enumerate(all_participants)}

    return {
        "version": "1.0",
        "tournament": {
            "name":             tournament.name,
            "sport":            tournament.sport,
            "participant_type": tournament.participant_type.value,
            "start_date":       tournament.start_date.isoformat(),
            "end_date":         tournament.end_date.isoformat() if tournament.end_date else None,
            "status":           tournament.status,
            "participants":     [_participant_to_dict(p, pid_map) for p in all_participants],
            "phases":           [_phase_to_dict(ph, pid_map) for ph in tournament.phases],
        }
    }


def to_json(tournament: Tournament, indent: int = 2) -> str:
    """Sérialise un tournoi en chaîne JSON."""
    return json.dumps(to_dict(tournament), ensure_ascii=False, indent=indent)


def _collect_all_participants(tournament: Tournament) -> list:
    """
    Retourne la liste dédupliquée de tous les participants
    (inscrits au tournoi + présents dans les phases).
    """
    seen = set()
    result = []
    for p in tournament.participants:
        if id(p) not in seen:
            seen.add(id(p))
            result.append(p)
    for phase in tournament.phases:
        for p in phase.participants:
            if id(p) not in seen:
                seen.add(id(p))
                result.append(p)
    return result


def _participant_to_dict(p, pid_map: dict) -> dict:
    """Convertit un Player ou Team en dict."""
    if isinstance(p, Player):
        return {
            "kind":           "player",
            "id":             pid_map[id(p)],
            "name":           p.name,
            "license_number": p.license_number,
            "date_of_birth":  p.date_of_birth.isoformat(),
            "handed":         p.handed,
            "points":         p.points,
        }
    else:  # Team
        return {
            "kind":    "team",
            "id":      pid_map[id(p)],
            "name":    p.name,
            "club":    p.club,
            "city":    p.city,
            "points":  p.points,
            "players": [
                {
                    "number":         number,
                    "name":           player.name,
                    "license_number": player.license_number,
                    "date_of_birth":  player.date_of_birth.isoformat(),
                    "handed":         player.handed,
                    "points":         player.points,
                }
                for number, player in sorted(p.mates.items())
            ],
        }


def _phase_to_dict(phase: Phase, pid_map: dict) -> dict:
    """Convertit une Phase en dict."""
    pools_ids = [
        [pid_map[id(p)] for p in pool]
        for pool in phase.pools
    ]
    participant_ids = [pid_map[id(p)] for p in phase.participants]

    return {
        "name":            phase.name,
        "tournament_type": phase.tournament_type.value,
        "num_qualifiers":  phase.num_qualifiers,
        "participant_ids": participant_ids,
        "pools":           pools_ids,
        "matches":         [_match_to_dict(m, pid_map) for m in phase.matches],
    }


def _match_to_dict(match: Match, pid_map: dict) -> dict:
    """Convertit un Match en dict."""
    a, b = match.opponents
    return {
        "opponent_ids": [pid_map[id(a)], pid_map[id(b)]],
        "score":        list(match.score),
        "state":        match.state,
    }


# ---------------------------------------------------------------------------
# IMPORT
# ---------------------------------------------------------------------------

def from_dict(data: dict) -> Tournament:
    """
    Reconstruit un Tournament depuis un dictionnaire (issu du JSON).

    Args:
        data (dict): Données désérialisées.

    Returns:
        Tournament: Le tournoi reconstruit avec tous ses objets liés.

    Raises:
        ValueError: Si la version est incompatible ou les données corrompues.
    """
    version = data.get("version", "1.0")
    if not version.startswith("1."):
        raise ValueError(f"Version de fichier non supportée : {version!r}")

    td = data["tournament"]

    # --- Reconstruit les participants dans un registre id → objet ---
    registry: dict[int, Any] = {}
    for p_data in td["participants"]:
        obj = _participant_from_dict(p_data)
        registry[p_data["id"]] = obj

    # --- Tournoi ---
    ptype = ParticipantType(td["participant_type"])
    tournament = Tournament(
        name             = td["name"],
        sport            = td["sport"],
        participant_type = ptype,
        start_date       = date.fromisoformat(td["start_date"]),
        end_date         = date.fromisoformat(td["end_date"]) if td.get("end_date") else None,
    )
    tournament.status = td.get("status", "upcoming")

    # Participants inscrits au tournoi (dans l'ordre original)
    # On les identifie par leur ordre dans la liste participants du JSON
    # Les ids 0..N correspondent aux participants inscrits dans tournament.participants
    # On se base sur participant_ids de la première phase pour retrouver l'ordre,
    # mais on repart de la liste brute pour le registre.
    for p_data in td["participants"]:
        obj = registry[p_data["id"]]
        # Seuls les participants vraiment inscrits au tournoi sont ajoutés
        # (on les distingue car ils apparaissent dans tournament.participants)
    # Pour retrouver les participants inscrits au tournoi (vs ceux juste dans des phases),
    # on utilise le fait que l'export met tournament.participants en premier dans la liste.
    # Le nombre exact est reconstitué via les ids qui ne correspondent à aucune phase seule.
    # Solution propre : on sauvegarde les ids inscrits explicitement.
    # → Ici on prend tous les participants de la liste (ordre de collect_all_participants)
    # Les premiers sont ceux de tournament.participants. On relit l'ordre tel quel.
    for p_data in td["participants"]:
        tournament.participants.append(registry[p_data["id"]])

    # --- Phases ---
    for ph_data in td["phases"]:
        phase = _phase_from_dict(ph_data, registry)
        tournament.phases.append(phase)

    return tournament


def from_json(json_str: str) -> Tournament:
    """Désérialise un tournoi depuis une chaîne JSON."""
    return from_dict(json.loads(json_str))


def _participant_from_dict(data: dict):
    """Reconstruit un Player ou Team depuis un dict."""
    if data["kind"] == "player":
        p = Player(
            license_number = data["license_number"],
            name           = data["name"],
            date_of_birth  = date.fromisoformat(data["date_of_birth"]),
            handed         = data.get("handed"),
        )
        p.points = data.get("points", 0.0)
        return p
    else:  # team
        team = Team(name=data["name"], club=data["club"], city=data["city"])
        team.points = data.get("points", 0.0)
        for pm in data.get("players", []):
            player = Player(
                license_number = pm["license_number"],
                name           = pm["name"],
                date_of_birth  = date.fromisoformat(pm["date_of_birth"]),
                handed         = pm.get("handed"),
            )
            player.points = pm.get("points", 0.0)
            team.add_player(player, pm["number"])
        return team


def _phase_from_dict(data: dict, registry: dict) -> Phase:
    """
    Reconstruit une Phase depuis un dict sans passer par le constructeur
    (qui régénèrerait les matchs) — on injecte directement l'état sauvegardé.
    """
    tournament_type = TournamentType(data["tournament_type"])
    participants    = [registry[pid] for pid in data["participant_ids"]]

    # Crée un objet Phase "vide" sans générer de matchs
    phase = Phase.__new__(Phase)
    phase.name            = data["name"]
    phase.tournament_type = tournament_type
    phase.participants    = participants
    phase.num_qualifiers  = data["num_qualifiers"]
    phase.pools           = [
        [registry[pid] for pid in pool]
        for pool in data.get("pools", [])
    ]

    # Reconstruit les matchs
    phase.matches = [
        _match_from_dict(m_data, registry)
        for m_data in data.get("matches", [])
    ]

    # Recalcule les byes à partir de l'état réel des matchs rechargés
    # (plutôt que de mettre une liste vide en dur)
    phase._update_byes()

    return phase


def _match_from_dict(data: dict, registry: dict) -> Match:
    """Reconstruit un Match depuis un dict."""
    a, b  = registry[data["opponent_ids"][0]], registry[data["opponent_ids"][1]]
    match = Match([a, b])
    match.score = list(data["score"])
    match.state = data["state"]
    return match