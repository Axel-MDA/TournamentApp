"""
ui/views/phase_view.py

Vue de suivi des phases du tournoi.
Le formulaire de création a été déplacé dans une modale (CreatePhaseDialog)
pour alléger la page. Cliquer sur une phase ouvre une fenêtre de détail
(actuellement implémentée pour le format POOL).
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QMessageBox,
    QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt

from models.config     import TournamentType
from models.tournament import Tournament
from .create_phase_dialog import CreatePhaseDialog
from .pool_detail_dialog  import PoolDetailDialog


_TYPE_COLORS = {
    TournamentType.POOL:        ("#E8F5E9", "#27AE60"),
    TournamentType.SINGLE_ELIM: ("#EBF5FB", "#2980B9"),
    TournamentType.DOUBLE_ELIM: ("#FEF9E7", "#F39C12"),
    TournamentType.SWISS:       ("#F5EEF8", "#8E44AD"),
}


class PhaseView(QWidget):
    """Vue de gestion des phases."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tournament: Tournament | None = None
        self._build()

    def set_tournament(self, tournament: Tournament):
        self._tournament = tournament
        self._refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("Phases")
        title.setObjectName("page_title")
        subtitle = QLabel("Crée et gère les phases de ton tournoi.")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Bouton de création — ouvre la modale, alignée à gauche
        btn_row = QHBoxLayout()
        btn_create = QPushButton("+ Créer une phase")
        btn_create.setObjectName("btn_primary")
        btn_create.setFixedWidth(180)
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_open_create_dialog)
        btn_row.addWidget(btn_create)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Liste des phases existantes
        phases_label = QLabel("Phases du tournoi")
        phases_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #1C2833; margin-top: 8px;")
        layout.addWidget(phases_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._phases_container = QWidget()
        self._phases_layout    = QVBoxLayout(self._phases_container)
        self._phases_layout.setSpacing(8)
        self._phases_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._phases_container)
        layout.addWidget(scroll)

    # ------------------------------------------------------------------
    # Création de phase (modale)
    # ------------------------------------------------------------------

    def _on_open_create_dialog(self):
        if not self._tournament:
            QMessageBox.warning(self, "Erreur", "Aucun tournoi actif.")
            return

        dialog = CreatePhaseDialog(self._tournament, parent=self)
        if dialog.exec():
            self._refresh()

    # ------------------------------------------------------------------
    # Détail d'une phase (au clic)
    # ------------------------------------------------------------------

    def _on_phase_clicked(self, phase):
        if phase.tournament_type == TournamentType.POOL:
            dialog = PoolDetailDialog(phase, parent=self)
            dialog.exec()
        else:
            QMessageBox.information(
                self, "Détail indisponible",
                f"La vue détaillée pour le format "
                f"'{phase.tournament_type.value.replace('_', ' ')}' "
                f"arrive bientôt."
            )

    # ------------------------------------------------------------------
    # Rafraîchissement
    # ------------------------------------------------------------------

    def _refresh(self):
        while self._phases_layout.count():
            item = self._phases_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._tournament or not self._tournament.phases:
            empty = QLabel("Aucune phase créée.")
            empty.setStyleSheet("color: #7F8C8D; font-size: 13px;")
            self._phases_layout.addWidget(empty)
            return

        for phase in self._tournament.phases:
            self._phases_layout.addWidget(self._build_phase_card(phase))

    def _build_phase_card(self, phase) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet(
            "QFrame#card:hover { border: 1.5px solid #2980B9; background-color: #FAFCFE; }"
        )

        c_layout = QHBoxLayout(card)
        c_layout.setContentsMargins(16, 12, 16, 12)

        bg, accent = _TYPE_COLORS.get(phase.tournament_type, ("#F5F6FA", "#7F8C8D"))
        badge = QLabel(phase.tournament_type.value.replace("_", " ").title())
        badge.setStyleSheet(
            f"background-color: {bg}; color: {accent}; border: 1px solid {accent};"
            f"border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600;"
        )
        badge.setFixedHeight(22)

        name_lbl = QLabel(phase.name)
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 600; color: #1C2833;")

        finished  = sum(1 for m in phase.matches if m.state == "Finished")
        total     = len(phase.matches)
        progress  = QLabel(f"{finished}/{total} matchs")
        progress.setStyleSheet("font-size: 12px; color: #7F8C8D;")

        status_text = "✅ Terminée" if phase.is_complete else "🔄 En cours"
        status_lbl  = QLabel(status_text)
        status_lbl.setStyleSheet("font-size: 12px; font-weight: 600;")

        hint_lbl = QLabel("Voir détail →")
        hint_lbl.setStyleSheet("font-size: 11px; color: #2980B9; font-weight: 600;")

        c_layout.addWidget(badge)
        c_layout.addSpacing(12)
        c_layout.addWidget(name_lbl)
        c_layout.addStretch()
        c_layout.addWidget(progress)
        c_layout.addSpacing(16)
        c_layout.addWidget(status_lbl)
        c_layout.addSpacing(16)
        c_layout.addWidget(hint_lbl)

        # Rend toute la carte cliquable
        card.mousePressEvent = lambda event, p=phase: self._on_phase_clicked(p)

        return card
