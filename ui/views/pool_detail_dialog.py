"""
ui/views/pool_detail_dialog.py

Fenêtre de détail pour une phase de format POOL.
Affiche chaque poule sous forme de carte dans une grille (4 colonnes max),
avec le classement interne de la poule : médailles, victoires, matchs joués, points.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QWidget, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt

from models.phase import Phase


_MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

_POOL_ACCENT_COLORS = [
    "#2980B9", "#27AE60", "#8E44AD", "#F39C12",
    "#E74C3C", "#16A085", "#D35400", "#2C3E50",
]

_GRID_COLUMNS = 4


class PoolDetailDialog(QDialog):
    """
    Fenêtre modale affichant le détail d'une phase de poules.

    Pour chaque poule : les participants triés par points décroissants,
    avec médaille (top 3), nombre de victoires, nombre de matchs joués,
    et points au classement de la poule.
    """

    def __init__(self, phase: Phase, parent=None):
        super().__init__(parent)
        self._phase = phase

        self.setWindowTitle(f"Détail — {phase.name}")
        self.setMinimumSize(900, 600)
        self.setModal(True)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        # En-tête
        title = QLabel(self._phase.name)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1C2833;")
        outer.addWidget(title)

        nb_pools = len(self._phase.pools)
        subtitle = QLabel(f"{nb_pools} poule(s) — format round-robin")
        subtitle.setStyleSheet("font-size: 13px; color: #7F8C8D;")
        outer.addWidget(subtitle)

        # Zone scrollable contenant la grille de poules
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignmentFlag.AlignTop)

        for idx, pool in enumerate(self._phase.pools):
            row = idx // _GRID_COLUMNS
            col = idx % _GRID_COLUMNS
            accent = _POOL_ACCENT_COLORS[idx % len(_POOL_ACCENT_COLORS)]
            card = self._build_pool_card(idx + 1, pool, accent)
            grid.addWidget(card, row, col)

        scroll.setWidget(container)
        outer.addWidget(scroll)

        # Bouton fermer
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        outer.addLayout(btn_row)

        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("btn_secondary")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedWidth(120)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

    def _build_pool_card(self, pool_number: int, pool: list, accent: str) -> QFrame:
        """Construit la carte d'une poule : en-tête + classement interne."""
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumWidth(200)
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        card.setStyleSheet(
            f"QFrame#card {{ border-top: 3px solid {accent}; }}"
        )

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        header = QLabel(f"Poule {pool_number}")
        header.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {accent};")
        layout.addWidget(header)

        ranked = self._rank_pool(pool)

        for position, (participant, stats) in enumerate(ranked, start=1):
            layout.addWidget(self._build_participant_row(position, participant, stats))

        return card

    def _build_participant_row(self, position: int, participant, stats: dict) -> QWidget:
        """Construit une ligne de classement pour un participant de la poule."""
        row_widget = QFrame()
        row_widget.setStyleSheet(
            "background-color: #F8F9FB; border-radius: 6px;"
            if position > 3 else
            "background-color: #FFFDF5; border-radius: 6px;"
        )
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(8)

        medal = _MEDALS.get(position, "")
        medal_lbl = QLabel(medal if medal else str(position))
        medal_lbl.setFixedWidth(22)
        medal_lbl.setStyleSheet(
            "font-size: 14px;" if medal else
            "font-size: 12px; color: #7F8C8D; font-weight: 600;"
        )
        row.addWidget(medal_lbl)

        name_lbl = QLabel(participant.name)
        name_lbl.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #1C2833;" if position == 1 else
            "font-size: 13px; font-weight: 500; color: #1C2833;"
        )
        name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        row.addWidget(name_lbl, 1)

        stats_lbl = QLabel(
            f"{stats['wins']}V / {stats['played']}J  ·  {stats['points']:.0f} pts"
        )
        stats_lbl.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        stats_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(stats_lbl)

        return row_widget

    def _rank_pool(self, pool: list) -> list[tuple]:
        """
        Calcule le classement d'une poule à la volée à partir des matchs de la phase.

        Pour chaque participant de la poule, ne considère que les matchs de
        cette phase qui l'opposent à un autre membre de la même poule.

        Returns:
            list[tuple[Participant, dict]]: Participants triés par points
            décroissants, avec leurs statistiques (wins, played, points).
        """
        pool_ids = {id(p) for p in pool}
        stats = {id(p): {"wins": 0, "played": 0, "points": 0.0} for p in pool}

        for match in self._phase.matches:
            a, b = match.opponents
            if id(a) not in pool_ids or id(b) not in pool_ids:
                continue
            if match.state != "Finished":
                continue

            stats[id(a)]["played"] += 1
            stats[id(b)]["played"] += 1

            winner = match.winner
            if winner is not None:
                stats[id(winner)]["wins"] += 1

        # Les points utilisés sont ceux déjà accumulés sur le participant
        # (cohérents avec le classement global de la phase, mis à jour
        # par Match.update_points() lors de la saisie des résultats).
        for p in pool:
            stats[id(p)]["points"] = p.points

        ranked = sorted(pool, key=lambda p: stats[id(p)]["points"], reverse=True)
        return [(p, stats[id(p)]) for p in ranked]
