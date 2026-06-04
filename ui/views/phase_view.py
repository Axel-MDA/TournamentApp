"""
ui/views/phase_view.py

Vue de création et de suivi des phases du tournoi.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QSpinBox, QMessageBox,
    QScrollArea, QSizePolicy
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

        # Formulaire nouvelle phase
        form_card = QFrame()
        form_card.setObjectName("card")
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(24, 20, 24, 20)
        form_layout.setSpacing(12)

        form_title = QLabel("Nouvelle phase")
        form_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #1C2833;")
        form_layout.addWidget(form_title)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        col_name = QVBoxLayout()
        lbl_name = QLabel("Nom de la phase")
        lbl_name.setObjectName("field_label")
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("ex: Phase de poules, Quarts de finale...")
        col_name.addWidget(lbl_name)
        col_name.addWidget(self._name_input)
        row1.addLayout(col_name, 3)

        col_type = QVBoxLayout()
        lbl_type = QLabel("Format")
        lbl_type.setObjectName("field_label")
        self._type_combo = QComboBox()
        for label, _ in _PHASE_TYPES:
            self._type_combo.addItem(label)
        self._type_combo.currentIndexChanged.connect(self._on_type_changed)
        col_type.addWidget(lbl_type)
        col_type.addWidget(self._type_combo)
        row1.addLayout(col_type, 2)

        form_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)

        col_pools = QVBoxLayout()
        self._lbl_pools = QLabel("Nombre de poules")
        self._lbl_pools.setObjectName("field_label")
        self._pools_spin = QSpinBox()
        self._pools_spin.setMinimum(1)
        self._pools_spin.setMaximum(20)
        self._pools_spin.setValue(2)
        col_pools.addWidget(self._lbl_pools)
        col_pools.addWidget(self._pools_spin)
        self._pools_widget = QWidget()
        self._pools_widget.setLayout(col_pools)
        row2.addWidget(self._pools_widget)

        col_qual = QVBoxLayout()
        self._lbl_qual = QLabel("Qualifiés pour la suite (0 = phase finale)")
        self._lbl_qual.setObjectName("field_label")
        self._qual_spin = QSpinBox()
        self._qual_spin.setMinimum(0)
        self._qual_spin.setMaximum(256)
        self._qual_spin.setValue(0)
        col_qual.addWidget(self._lbl_qual)
        col_qual.addWidget(self._qual_spin)
        row2.addLayout(col_qual)

        form_layout.addLayout(row2)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_create = QPushButton("Créer la phase")
        btn_create.setObjectName("btn_primary")
        btn_create.setFixedWidth(160)
        btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_create.clicked.connect(self._on_create_phase)
        btn_row.addWidget(btn_create)
        form_layout.addLayout(btn_row)

        layout.addWidget(form_card)

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

        self._on_type_changed(0)

    def _on_type_changed(self, idx: int):
        is_pool = (_PHASE_TYPES[idx][1] == TournamentType.POOL)
        self._pools_widget.setVisible(is_pool)

    def _on_create_phase(self):
        if not self._tournament:
            QMessageBox.warning(self, "Erreur", "Aucun tournoi actif.")
            return

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
                f"Nombre de qualifiés ({num_qualifiers}) supérieur aux participants disponibles ({nb_available})."
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
            self._name_input.clear()
            self._refresh()
            QMessageBox.information(
                self, "Phase créée",
                f"Phase '{name}' créée avec {len(phase.matches)} match(s)."
            )
        except (ValueError, RuntimeError) as e:
            QMessageBox.warning(self, "Erreur", str(e))

    def _available_count(self) -> int:
        if self._tournament.phases:
            prev = self._tournament.phases[-1]
            return prev.num_qualifiers if prev.num_qualifiers > 0 else len(self._tournament.participants)
        return len(self._tournament.participants)

    def _refresh(self):
        # Vide le conteneur de phases
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
            card = QFrame()
            card.setObjectName("card")
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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

            c_layout.addWidget(badge)
            c_layout.addSpacing(12)
            c_layout.addWidget(name_lbl)
            c_layout.addStretch()
            c_layout.addWidget(progress)
            c_layout.addSpacing(16)
            c_layout.addWidget(status_lbl)

            self._phases_layout.addWidget(card)
