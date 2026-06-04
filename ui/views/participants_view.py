"""
ui/views/participants_view.py

Vue d'inscription des participants (joueurs ou équipes).
"""
from __future__ import annotations

from datetime import date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QTableWidget, QTableWidgetItem,
    QMessageBox, QHeaderView
)
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QColor

from models.config     import ParticipantType
from models.players    import Player
from models.teams      import Team
from models.tournament import Tournament


class ParticipantsView(QWidget):
    """Vue d'inscription des participants."""

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

        title = QLabel("Participants")
        title.setObjectName("page_title")
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("page_subtitle")
        layout.addWidget(title)
        layout.addWidget(self._subtitle)

        # Formulaire d'ajout
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QHBoxLayout(form_card)
        form_layout.setContentsMargins(20, 16, 20, 16)
        form_layout.setSpacing(12)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Nom du participant...")
        self._name_input.returnPressed.connect(self._on_add)
        form_layout.addWidget(self._name_input)

        self._license_input = QLineEdit()
        self._license_input.setPlaceholderText("Licence (optionnel)")
        self._license_input.setFixedWidth(160)
        form_layout.addWidget(self._license_input)

        btn_add = QPushButton("+ Ajouter")
        btn_add.setObjectName("btn_primary")
        btn_add.setFixedWidth(120)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._on_add)
        form_layout.addWidget(btn_add)

        layout.addWidget(form_card)

        # Tableau
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["#", "Nom", "Licence"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(2, 160)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        layout.addWidget(self._table)

        # Bouton supprimer
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._btn_remove = QPushButton("Retirer le sélectionné")
        self._btn_remove.setObjectName("btn_danger")
        self._btn_remove.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_remove.clicked.connect(self._on_remove)
        btn_row.addWidget(self._btn_remove)
        layout.addLayout(btn_row)

    def _refresh(self):
        if not self._tournament:
            return
        ptype = self._tournament.participant_type
        self._subtitle.setText(
            f"{'Équipes' if ptype == ParticipantType.TEAM else 'Joueurs'} inscrits : "
            f"{len(self._tournament.participants)}"
        )
        self._table.setRowCount(0)
        for i, p in enumerate(self._tournament.participants):
            self._table.insertRow(i)
            self._table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table.setItem(i, 1, QTableWidgetItem(p.name))
            license_val = getattr(p, 'license_number', '-')
            self._table.setItem(i, 2, QTableWidgetItem(license_val or '-'))
            self._table.setRowHeight(i, 42)

    def _on_add(self):
        if not self._tournament:
            QMessageBox.warning(self, "Erreur", "Aucun tournoi actif.")
            return

        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Champ requis", "Le nom ne peut pas être vide.")
            return

        license_number = self._license_input.text().strip() or f"LIC-{name[:3].upper()}"
        ptype = self._tournament.participant_type

        try:
            if ptype == ParticipantType.PLAYER:
                participant = Player(
                    license_number = license_number,
                    name           = name,
                    date_of_birth  = date(2000, 1, 1),
                )
            else:
                participant = Team(name=name, club="", city="")

            self._tournament.register(participant)
            self._name_input.clear()
            self._license_input.clear()
            self._name_input.setFocus()
            self._refresh()

        except (TypeError, ValueError) as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def _on_remove(self):
        if not self._tournament:
            return
        row = self._table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Sélection", "Sélectionne un participant à retirer.")
            return
        participant = self._tournament.participants[row]
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Retirer {participant.name} du tournoi ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._tournament.unregister(participant)
            self._refresh()
