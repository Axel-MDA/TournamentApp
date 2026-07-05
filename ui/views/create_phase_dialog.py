"""
ui/views/create_phase_dialog.py

Modal de création d'une nouvelle phase de tournoi.
Reprend le formulaire qui était auparavant intégré directement dans PhaseView.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QMessageBox, QWidget
)
from PyQt6.QtCore import Qt

from models.config     import TournamentType
from models.tournament import Tournament


_PHASE_TYPES = [
    ("Poules (round-robin)",    TournamentType.POOL),
    ("Élimination directe",     TournamentType.SINGLE_ELIM),
    ("Double élimination",      TournamentType.DOUBLE_ELIM),
    ("Système suisse",          TournamentType.SWISS),
]


class CreatePhaseDialog(QDialog):
    """
    Boîte de dialogue modale pour créer une nouvelle phase.

    Usage:
        dialog = CreatePhaseDialog(tournament, parent=self)
        if dialog.exec():
            phase = dialog.created_phase
    """

    def __init__(self, tournament: Tournament, parent=None):
        super().__init__(parent)
        self._tournament    = tournament
        self.created_phase  = None  # rempli si la création réussit

        self.setWindowTitle("Créer une phase")
        self.setMinimumWidth(480)
        self.setModal(True)
        self._build()
        self._on_type_changed(0)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Nouvelle phase")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #1C2833;")
        layout.addWidget(title)

        # Nom
        lbl_name = QLabel("Nom de la phase")
        lbl_name.setObjectName("field_label")
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("ex: Phase de poules, Quarts de finale...")
        layout.addWidget(lbl_name)
        layout.addWidget(self._name_input)

        # Format
        lbl_type = QLabel("Format")
        lbl_type.setObjectName("field_label")
        self._type_combo = QComboBox()
        for label, _ in _PHASE_TYPES:
            self._type_combo.addItem(label)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(lbl_type)
        layout.addWidget(self._type_combo)

        # Nombre de poules (visible seulement si POOL)
        self._lbl_pools = QLabel("Nombre de poules")
        self._lbl_pools.setObjectName("field_label")
        self._pools_spin = QSpinBox()
        self._pools_spin.setMinimum(1)
        self._pools_spin.setMaximum(20)
        self._pools_spin.setValue(2)
        layout.addWidget(self._lbl_pools)
        layout.addWidget(self._pools_spin)

        # Qualifiés
        lbl_qual = QLabel("Qualifiés pour la suite (0 = phase finale)")
        lbl_qual.setObjectName("field_label")
        self._qual_spin = QSpinBox()
        self._qual_spin.setMinimum(0)
        self._qual_spin.setMaximum(256)
        self._qual_spin.setValue(0)
        layout.addWidget(lbl_qual)
        layout.addWidget(self._qual_spin)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_create = QPushButton("Créer la phase")
        btn_create.setObjectName("btn_primary")
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_create_phase)
        btn_row.addWidget(btn_create)

        layout.addLayout(btn_row)

    def _on_type_changed(self, idx: int):
        is_pool = (_PHASE_TYPES[idx][1] == TournamentType.POOL)
        self._lbl_pools.setVisible(is_pool)
        self._pools_spin.setVisible(is_pool)

    def _available_count(self) -> int:
        if self._tournament.phases:
            prev = self._tournament.phases[-1]
            return prev.num_qualifiers if prev.num_qualifiers > 0 else len(self._tournament.participants)
        return len(self._tournament.participants)

    def _on_create_phase(self):
        name = self._name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Champ requis", "Le nom de la phase est obligatoire.")
            return

        idx             = self._type_combo.currentIndex()
        tournament_type = _PHASE_TYPES[idx][1]
        num_pools       = self._pools_spin.value()
        num_qualifiers  = self._qual_spin.value()

        nb_available = self._available_count()
        if num_qualifiers > nb_available:
            QMessageBox.warning(
                self, "Erreur",
                f"Nombre de qualifiés ({num_qualifiers}) supérieur aux participants "
                f"disponibles ({nb_available})."
            )
            return

        use_previous = bool(self._tournament.phases)
        seeded = self._tournament.phases[-1].qualifiers() if self._tournament.phases else None

        try:
            phase = self._tournament.add_phase(
                name                         = name,
                tournament_type              = tournament_type,
                num_qualifiers               = num_qualifiers,
                num_pools                    = num_pools,
                use_qualifiers_from_previous = use_previous,
                seeded                       = seeded,
            )
            self.created_phase = phase
            QMessageBox.information(
                self, "Phase créée",
                f"Phase '{name}' créée avec {len(phase.matches)} match(s)."
            )
            self.accept()
        except (ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Erreur", str(e))