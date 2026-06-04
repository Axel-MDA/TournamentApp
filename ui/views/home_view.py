"""
ui/views/home_view.py

Vue d'accueil : création d'un nouveau tournoi.
"""
from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QButtonGroup, QRadioButton, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from models.config     import ParticipantType
from models.tournament import Tournament


class HomeView(QWidget):
    """
    Écran d'accueil permettant de créer un nouveau tournoi.

    Signals:
        tournament_created (Tournament): Émis quand un tournoi est créé.
    """

    tournament_created = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("Nouveau tournoi")
        title.setObjectName("page_title")
        subtitle = QLabel("Remplis les informations pour créer ton tournoi.")
        subtitle.setObjectName("page_subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(24, 24, 24, 24)

        # Nom
        self._name_input = self._field(card_layout, "Nom du tournoi", "ex: Championnat régional 2026")
        # Sport
        self._sport_input = self._field(card_layout, "Sport", "ex: Tennis de table, Football...")

        # Type de participants
        type_label = QLabel("Type de participants")
        type_label.setObjectName("field_label")
        card_layout.addWidget(type_label)

        radio_row = QHBoxLayout()
        self._radio_team   = QRadioButton("Équipes")
        self._radio_player = QRadioButton("Joueurs individuels")
        self._radio_player.setChecked(True)
        radio_row.addWidget(self._radio_team)
        radio_row.addWidget(self._radio_player)
        radio_row.addStretch()
        card_layout.addLayout(radio_row)

        # Bouton créer
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_create = QPushButton("Créer le tournoi")
        btn_create.setObjectName("btn_primary")
        btn_create.setFixedWidth(180)
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_create)
        btn_row.addWidget(btn_create)
        card_layout.addLayout(btn_row)

        layout.addWidget(card)

    def _field(self, parent_layout, label: str, placeholder: str) -> QLineEdit:
        lbl = QLabel(label)
        lbl.setObjectName("field_label")
        parent_layout.addWidget(lbl)
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        parent_layout.addWidget(inp)
        return inp

    def _on_create(self):
        name  = self._name_input.text().strip()
        sport = self._sport_input.text().strip()

        if not name:
            QMessageBox.warning(self, "Champ requis", "Le nom du tournoi est obligatoire.")
            return
        if not sport:
            QMessageBox.warning(self, "Champ requis", "Le sport est obligatoire.")
            return

        ptype = ParticipantType.TEAM if self._radio_team.isChecked() else ParticipantType.PLAYER

        tournament = Tournament(
            name             = name,
            sport            = sport,
            participant_type = ptype,
            start_date       = date.today(),
        )
        self.tournament_created.emit(tournament)
        self._name_input.clear()
        self._sport_input.clear()
