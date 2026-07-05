"""
ui/views/pool_detail_dialog.py

Fenêtre de détail pour une phase de format POOL.
Affiche chaque poule sous forme de carte dans une grille (4 colonnes max),
avec le classement interne de la poule : médailles, victoires/nuls/défaites,
average et points.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QWidget, QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QKeySequence, QShortcut

from models.phase  import Phase
from models.config import WIN_POINT, DRAW_POINT, LOOSE_POINT


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
        self._setup_fullscreen_toggle()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        # En-tête
        header_row = QHBoxLayout()
        title = QLabel(self._phase.name)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1C2833;")
        header_row.addWidget(title)
        header_row.addStretch()

        self._btn_fullscreen = QPushButton("⛶  Plein écran")
        self._btn_fullscreen.setObjectName("btn_secondary")
        self._btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_fullscreen.setFixedWidth(150)
        self._btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        header_row.addWidget(self._btn_fullscreen)

        outer.addLayout(header_row)

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

    def _setup_fullscreen_toggle(self):
        """Active le raccourci F11 pour basculer en plein écran."""
        shortcut = QShortcut(QKeySequence("F11"), self)
        shortcut.activated.connect(self._toggle_fullscreen)

        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self._exit_fullscreen_or_close)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self._btn_fullscreen.setText("⛶  Plein écran")
        else:
            self.showFullScreen()
            self._btn_fullscreen.setText("⛶  Quitter le plein écran")

    def _exit_fullscreen_or_close(self):
        """Échap quitte le plein écran s'il est actif, sinon ferme la fenêtre."""
        if self.isFullScreen():
            self._toggle_fullscreen()
        else:
            self.reject()

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
            f"{stats['wins']}W / {stats['draws']}D / {stats['losses']}L  ·  "
            f"avg {stats['average']:+.1f}  ·  {stats['points']:.0f} pts"
        )
        stats_lbl.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        stats_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(stats_lbl)

        return row_widget

    def _rank_pool(self, pool: list) -> list[tuple]:
        """
        Calcule le classement d'une poule à la volée à partir des matchs de
        cette phase, en recalculant les points depuis les résultats des
        matchs eux-mêmes (et non depuis participant.points).

        Ce choix est important : participant.points est partagé entre
        toutes les phases du tournoi et reflète l'état de la phase la
        plus récente — il serait donc remis à zéro dès qu'une nouvelle
        phase démarre. En recalculant ici depuis self._phase.matches, le
        classement de cette poule reste consultable correctement même
        après le lancement d'une phase suivante.

        L'average est calculé comme (somme des points marqués - somme des
        points encaissés) / nombre de matchs joués, sur les seuls matchs
        de cette poule.

        Returns:
            list[tuple[Participant, dict]]: Participants triés par points
            de poule décroissants, avec leurs statistiques (wins, draws,
            losses, played, points, average).
        """
        pool_ids = {id(p) for p in pool}
        stats = {
            id(p): {
                "wins": 0, "draws": 0, "losses": 0, "played": 0,
                "points": 0.0, "scored": 0, "conceded": 0,
            }
            for p in pool
        }

        for match in self._phase.matches:
            a, b = match.opponents
            if id(a) not in pool_ids or id(b) not in pool_ids:
                continue
            if match.state != "Finished":
                continue

            score_a, score_b = match.score

            stats[id(a)]["played"]   += 1
            stats[id(b)]["played"]   += 1
            stats[id(a)]["scored"]   += score_a
            stats[id(a)]["conceded"] += score_b
            stats[id(b)]["scored"]   += score_b
            stats[id(b)]["conceded"] += score_a

            winner = match.winner
            if winner is None:
                stats[id(a)]["draws"]  += 1
                stats[id(b)]["draws"]  += 1
                stats[id(a)]["points"] += DRAW_POINT
                stats[id(b)]["points"] += DRAW_POINT
            elif winner is a:
                stats[id(a)]["wins"]   += 1
                stats[id(b)]["losses"] += 1
                stats[id(a)]["points"] += WIN_POINT
                stats[id(b)]["points"] += LOOSE_POINT
            else:
                stats[id(b)]["wins"]   += 1
                stats[id(a)]["losses"] += 1
                stats[id(b)]["points"] += WIN_POINT
                stats[id(a)]["points"] += LOOSE_POINT

        for p in pool:
            s = stats[id(p)]
            s["average"] = (
                (s["scored"] - s["conceded"]) / s["played"]
                if s["played"] > 0 else 0.0
            )

        ranked = sorted(pool, key=lambda p: stats[id(p)]["points"], reverse=True)
        return [(p, stats[id(p)]) for p in ranked]