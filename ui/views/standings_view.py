"""
ui/views/standings_view.py

Vue du classement de la phase en cours.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QColor, QFont

from models.tournament import Tournament


class StandingsView(QWidget):
    """Vue du classement."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tournament: Tournament | None = None
        self._build()

    def set_tournament(self, tournament: Tournament):
        self._tournament = tournament
        self._refresh()

    def refresh(self):
        self._refresh()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)

        title = QLabel("Classement")
        title.setObjectName("page_title")
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("page_subtitle")
        layout.addWidget(title)
        layout.addWidget(self._subtitle)

        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Position", "Nom", "Points"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 90)
        self._table.setColumnWidth(2, 90)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        layout.addWidget(self._table)

    def _refresh(self):
        self._table.setRowCount(0)

        if not self._tournament:
            return

        phase = self._tournament.current_phase
        if phase is None:
            phase = self._tournament.phases[-1] if self._tournament.phases else None

        if phase is None:
            self._subtitle.setText("Aucune phase créée.")
            return

        self._subtitle.setText(f"Phase : {phase.name}")

        _MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
        _ROW_COLORS = {
            1: QColor("#FEF9E7"),
            2: QColor("#F8F9FA"),
            3: QColor("#F0F3F4"),
        }

        for i, p in enumerate(phase.standings(), start=1):
            row = self._table.rowCount()
            self._table.insertRow(row)

            medal = _MEDALS.get(i, "")
            pos_item = QTableWidgetItem(f"{medal}  {i}")
            pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            name_item = QTableWidgetItem(p.name)
            name_font = QFont()
            if i == 1:
                name_font.setBold(True)
            name_item.setFont(name_font)

            pts_item = QTableWidgetItem(str(int(p.points)))
            pts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self._table.setItem(row, 0, pos_item)
            self._table.setItem(row, 1, name_item)
            self._table.setItem(row, 2, pts_item)
            self._table.setRowHeight(row, 44)

            if i in _ROW_COLORS:
                for col in range(3):
                    self._table.item(row, col).setBackground(_ROW_COLORS[i])
