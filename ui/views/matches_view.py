"""
ui/views/matches_view.py

Vue de saisie des résultats des matchs.

Pour les phases de format POOL, les matchs sont regroupés et affichés
par poule (Poule 1, Poule 2, ...), dans l'ordre naturel de la poule
(round-robin), plutôt que dans l'ordre brut de génération — ce qui
rend le suivi du tournoi directement lisible sans avoir à chercher
les matchs d'une même poule éparpillés dans la liste.

Les matchs déjà terminés peuvent être édités (correction d'un score
saisi par erreur) via un bouton dédié.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QSpinBox, QMessageBox, QSizePolicy,
    QDialog
)
from PyQt6.QtCore import Qt

from models.config     import TournamentType
from models.tournament import Tournament


_POOL_ACCENT_COLORS = [
    "#2980B9", "#27AE60", "#8E44AD", "#F39C12",
    "#E74C3C", "#16A085", "#D35400", "#2C3E50",
]


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

        if phase.tournament_type == TournamentType.POOL and phase.pools:
            self._render_matches_by_pool(phase)
        else:
            self._render_byes(phase)
            self._render_matches_flat(phase)

    # ------------------------------------------------------------------
    # Affichage groupé par poule (format POOL)
    # ------------------------------------------------------------------

    def _render_matches_by_pool(self, phase):
        """
        Affiche les matchs regroupés par poule, dans l'ordre naturel du
        round-robin de chaque poule (ex: A vs B, C vs D, A vs C, ...),
        plutôt que dans l'ordre brut de génération (qui regroupait tous
        les matchs d'un même joueur d'affilée).
        """
        for idx, pool in enumerate(phase.pools):
            accent = _POOL_ACCENT_COLORS[idx % len(_POOL_ACCENT_COLORS)]
            pool_ids = {id(p) for p in pool}
            pool_matches = [
                m for m in phase.matches
                if id(m.opponents[0]) in pool_ids and id(m.opponents[1]) in pool_ids
            ]

            header = QLabel(f"Poule {idx + 1}")
            header.setStyleSheet(
                f"font-size: 14px; font-weight: 700; color: {accent}; "
                f"margin-top: 8px;"
            )
            self._matches_layout.addWidget(header)

            for match in pool_matches:
                self._matches_layout.addWidget(self._build_match_card(match, phase, accent))

    def _render_byes(self, phase):
        """Affiche les participants en attente d'un bye (le cas échéant)."""
        bye_participants = getattr(phase, "_bye_participants", [])
        if not bye_participants:
            return

        byes_card = QFrame()
        byes_card.setObjectName("card")
        byes_card.setStyleSheet(
            "background-color: #FEF9E7; border: 1px solid #F39C12; border-radius: 8px;"
        )
        byes_layout = QHBoxLayout(byes_card)
        byes_layout.setContentsMargins(16, 10, 16, 10)
        byes_names = ", ".join(p.name for p in bye_participants)
        byes_lbl = QLabel(f"⏳  En attente (bye) : {byes_names}")
        byes_lbl.setStyleSheet("font-size: 13px; color: #7D6608;")
        byes_layout.addWidget(byes_lbl)
        self._matches_layout.addWidget(byes_card)

    def _render_matches_flat(self, phase):
        """Affiche les matchs dans l'ordre de génération (formats hors POOL)."""
        for match in phase.matches:
            self._matches_layout.addWidget(self._build_match_card(match, phase))

    # ------------------------------------------------------------------
    # Carte de match
    # ------------------------------------------------------------------

    def _build_match_card(self, match, phase, accent: str | None = None) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if accent:
            card.setStyleSheet(f"QFrame#card {{ border-left: 3px solid {accent}; }}")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(16)

        a, b = match.opponents

        if match.state == "Finished":
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

            btn_edit = QPushButton("✎  Modifier")
            btn_edit.setObjectName("btn_secondary")
            btn_edit.setFixedWidth(110)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.clicked.connect(
                lambda _, m=match, ph=phase: self._on_edit_match(m, ph)
            )

            layout.addWidget(name_a, 2)
            layout.addWidget(score, 1)
            layout.addWidget(name_b, 2)
            layout.addStretch()
            layout.addWidget(badge)
            layout.addWidget(btn_edit)

        else:
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

    # ------------------------------------------------------------------
    # Saisie et édition
    # ------------------------------------------------------------------

    def _save_result(self, match, score_a_spin, score_b_spin, phase):
        sa = score_a_spin.value()
        sb = score_b_spin.value()

        match.set_score(sa, sb)
        match.set_state("Finished")
        match.update_points()

        self._advance_if_needed(phase)
        self._refresh()

    def _on_edit_match(self, match, phase):
        """
        Ouvre une mini-modale permettant de corriger le score d'un match
        déjà terminé. Annule les points précédemment attribués avant de
        réappliquer le nouveau résultat, pour ne pas fausser le classement.
        """
        dialog = _EditMatchDialog(match, parent=self)
        if dialog.exec():
            new_a, new_b = dialog.result_scores
            self._revert_points(match)
            match.set_score(new_a, new_b)
            match.update_points()
            self._refresh()

    def _revert_points(self, match):
        """
        Annule l'effet de update_points() pour ce match avant de
        réappliquer un nouveau score corrigé, afin que l'édition d'un
        match ne double-compte pas les points au classement.
        """
        from models.config import WIN_POINT, DRAW_POINT, LOOSE_POINT

        a, b = match.opponents
        old_winner = match.winner  # basé sur l'ancien score, avant correction

        if old_winner is None:
            a.points -= DRAW_POINT
            b.points -= DRAW_POINT
        elif old_winner is a:
            a.points -= WIN_POINT
            b.points -= LOOSE_POINT
        else:
            b.points -= WIN_POINT
            a.points -= LOOSE_POINT

    def _advance_if_needed(self, phase):
        """Avance automatiquement au tour suivant si le format le permet et que le tour est complet."""
        if phase.tournament_type in (TournamentType.SINGLE_ELIM, TournamentType.SWISS):
            if phase.is_round_complete:
                generated = phase.advance_round()
                if generated:
                    new_count = sum(1 for m in phase.matches if m.state != "Finished")
                    QMessageBox.information(
                        self, "Tour suivant",
                        f"Tour suivant généré automatiquement : {new_count} nouveau(x) match(s)."
                    )


class _EditMatchDialog(QDialog):
    """Mini-modale de correction de score pour un match déjà terminé."""

    def __init__(self, match, parent=None):
        super().__init__(parent)
        self._match = match
        self.result_scores = tuple(match.score)

        a, b = match.opponents
        self.setWindowTitle(f"Modifier — {a.name} vs {b.name}")
        self.setMinimumWidth(360)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"{a.name}  vs  {b.name}")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1C2833;")
        layout.addWidget(title)

        note = QLabel("Le classement sera recalculé avec le nouveau score.")
        note.setStyleSheet("font-size: 11px; color: #7F8C8D;")
        note.setWordWrap(True)
        layout.addWidget(note)

        row = QHBoxLayout()
        col_a = QVBoxLayout()
        col_a.addWidget(QLabel(a.name))
        self._spin_a = QSpinBox()
        self._spin_a.setRange(0, 999)
        self._spin_a.setValue(match.score[0])
        col_a.addWidget(self._spin_a)
        row.addLayout(col_a)

        col_b = QVBoxLayout()
        col_b.addWidget(QLabel(b.name))
        self._spin_b = QSpinBox()
        self._spin_b.setRange(0, 999)
        self._spin_b.setValue(match.score[1])
        col_b.addWidget(self._spin_b)
        row.addLayout(col_b)

        layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Enregistrer")
        btn_save.setObjectName("btn_primary")
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _on_save(self):
        self.result_scores = (self._spin_a.value(), self._spin_b.value())
        self.accept()