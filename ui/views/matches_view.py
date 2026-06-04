"""
ui/views/matches_view.py

Vue de saisie des résultats des matchs.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSpinBox, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt

from models.config     import TournamentType
from models.tournament import Tournament


class MatchesView(QWidget):
    """Vue de saisie des résultats."""

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

        title = QLabel("Matchs")
        title.setObjectName("page_title")
        self._subtitle = QLabel("")
        self._subtitle.setObjectName("page_subtitle")
        layout.addWidget(title)
        layout.addWidget(self._subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._container = QWidget()
        self._matches_layout = QVBoxLayout(self._container)
        self._matches_layout.setSpacing(8)
        self._matches_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll.setWidget(self._container)
        layout.addWidget(scroll)

    def _refresh(self):
        while self._matches_layout.count():
            item = self._matches_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self._tournament:
            return

        phase = self._tournament.current_phase
        if phase is None:
            phase = self._tournament.phases[-1] if self._tournament.phases else None

        if phase is None:
            self._subtitle.setText("Aucune phase créée.")
            return

        self._subtitle.setText(f"Phase : {phase.name}")

        # Byes
        if phase._bye_participants:
            byes_card = QFrame()
            byes_card.setObjectName("card")
            byes_card.setStyleSheet("background-color: #FEF9E7; border: 1px solid #F39C12; border-radius: 8px;")
            byes_layout = QHBoxLayout(byes_card)
            byes_layout.setContentsMargins(16, 10, 16, 10)
            byes_names = ", ".join(p.name for p in phase._bye_participants)
            byes_lbl = QLabel(f"⏳  En attente (bye) : {byes_names}")
            byes_lbl.setStyleSheet("font-size: 13px; color: #7D6608;")
            byes_layout.addWidget(byes_lbl)
            self._matches_layout.addWidget(byes_card)

        # Matchs
        for match in phase.matches:
            self._matches_layout.addWidget(self._build_match_card(match, phase))

    def _build_match_card(self, match, phase) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        a, b = match.opponents

        if match.state == "Finished":
            # Affichage résultat
            winner = match.winner
            style_a = "font-size: 14px; font-weight: 700;" if winner == a else "font-size: 14px; color: #7F8C8D;"
            style_b = "font-size: 14px; font-weight: 700;" if winner == b else "font-size: 14px; color: #7F8C8D;"

            name_a = QLabel(a.name)
            name_a.setStyleSheet(style_a)
            score  = QLabel(f"{match.score[0]}  —  {match.score[1]}")
            score.setStyleSheet("font-size: 16px; font-weight: 700; color: #1C2833; min-width: 80px;")
            score.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_b = QLabel(b.name)
            name_b.setStyleSheet(style_b)

            badge = QLabel("✅")
            badge.setFixedWidth(28)

            layout.addWidget(name_a, 2)
            layout.addWidget(score, 1)
            layout.addWidget(name_b, 2)
            layout.addStretch()
            layout.addWidget(badge)

        else:
            # Saisie du score
            name_a = QLabel(a.name)
            name_a.setStyleSheet("font-size: 14px; font-weight: 600;")

            score_a = QSpinBox()
            score_a.setMinimum(0)
            score_a.setMaximum(999)
            score_a.setFixedWidth(70)

            vs_lbl = QLabel("vs")
            vs_lbl.setStyleSheet("font-size: 13px; color: #7F8C8D;")
            vs_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            score_b = QSpinBox()
            score_b.setMinimum(0)
            score_b.setMaximum(999)
            score_b.setFixedWidth(70)

            name_b = QLabel(b.name)
            name_b.setStyleSheet("font-size: 14px; font-weight: 600;")

            btn_save = QPushButton("Valider")
            btn_save.setObjectName("btn_primary")
            btn_save.setFixedWidth(90)
            btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_save.clicked.connect(
                lambda _, m=match, sa=score_a, sb=score_b, ph=phase: self._save_result(m, sa, sb, ph)
            )

            layout.addWidget(name_a, 2)
            layout.addWidget(score_a)
            layout.addWidget(vs_lbl)
            layout.addWidget(score_b)
            layout.addWidget(name_b, 2)
            layout.addStretch()
            layout.addWidget(btn_save)

        return card

    def _save_result(self, match, score_a_spin, score_b_spin, phase):
        sa = score_a_spin.value()
        sb = score_b_spin.value()

        match.set_score(sa, sb)
        match.set_state("Finished")
        match.update_points()

        # Avancement automatique du tour
        if phase.tournament_type in (TournamentType.SINGLE_ELIM, TournamentType.SWISS):
            if phase.is_round_complete:
                generated = phase.advance_round()
                if generated:
                    new_count = sum(1 for m in phase.matches if m.state != "Finished")
                    QMessageBox.information(
                        self, "Tour suivant",
                        f"Tour suivant généré automatiquement : {new_count} nouveau(x) match(s)."
                    )

        self._refresh()
