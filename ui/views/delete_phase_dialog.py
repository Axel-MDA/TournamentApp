"""
ui/views/delete_phase_dialog.py

Modal de confirmation pour la suppression d'une phase.
Demande à l'utilisateur de retaper le nom de la phase en MAJUSCULES
pour valider la suppression, afin d'éviter les fausses manipulations.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame
)
from PyQt6.QtCore import Qt


class DeletePhaseDialog(QDialog):
    """
    Boîte de dialogue de confirmation de suppression d'une phase.

    L'utilisateur doit retaper le nom de la phase intégralement en
    majuscules pour activer le bouton de suppression.

    Usage:
        dialog = DeletePhaseDialog(phase.name, parent=self)
        if dialog.exec():
            # confirmé, supprimer la phase
    """

    def __init__(self, phase_name: str, parent=None):
        super().__init__(parent)
        self._phase_name      = phase_name
        self._expected_input  = phase_name.upper()

        self.setWindowTitle("Supprimer la phase")
        self.setMinimumWidth(440)
        self.setModal(True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        warning_card = QFrame()
        warning_card.setStyleSheet(
            "background-color: #FDEDEC; border: 1px solid #E74C3C; border-radius: 6px;"
        )
        warning_layout = QVBoxLayout(warning_card)
        warning_layout.setContentsMargins(16, 12, 16, 12)

        title = QLabel("⚠️  Suppression irréversible")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #C0392B;")
        warning_layout.addWidget(title)

        message = QLabel(
            f"Tu es sur le point de supprimer la phase « {self._phase_name} » "
            f"ainsi que tous ses matchs et résultats. Cette action ne peut pas être annulée."
        )
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 12px; color: #922B21;")
        warning_layout.addWidget(message)

        layout.addWidget(warning_card)

        instruction = QLabel(
            f"Pour confirmer, tape le nom de la phase en MAJUSCULES : "
            f"<b>{self._expected_input}</b>"
        )
        instruction.setWordWrap(True)
        instruction.setStyleSheet("font-size: 13px; color: #1C2833;")
        layout.addWidget(instruction)

        self._confirm_input = QLineEdit()
        self._confirm_input.setPlaceholderText(self._expected_input)
        self._confirm_input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._confirm_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        self._btn_delete = QPushButton("Supprimer définitivement")
        self._btn_delete.setObjectName("btn_danger")
        self._btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self.accept)
        btn_row.addWidget(self._btn_delete)

        layout.addLayout(btn_row)

    def _on_text_changed(self, text: str):
        self._btn_delete.setEnabled(text == self._expected_input)