"""
ui/views/bracket_detail_dialog.py

Fenêtre de détail pour une phase de format SINGLE_ELIM (élimination directe).
Affiche un arbre de tournoi classique (bracket) avec :
    - les matchs déjà générés, organisés en colonnes par tour
    - TBD pour les futurs participants pas encore déterminés
    - BYE pour les participants qualifiés sans adversaire (effectif impair)
    - saisie du score directement au clic sur un match jouable
    - un mode "Vue globale" qui réduit l'échelle pour faire tenir
      tout l'arbre à l'écran sans scroll
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QScrollArea, QWidget, QSizePolicy,
    QPushButton, QSpinBox, QMessageBox,
    QGraphicsView, QGraphicsScene, QGraphicsProxyWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QKeySequence, QShortcut

from models.phase import Phase
from models.config import TournamentType


_COL_WIDTH    = 220
_CARD_HEIGHT  = 64
_ROW_GAP      = 24
_COL_GAP      = 56

_COLOR_PENDING  = "#7F8C8D"
_COLOR_FINISHED = "#1C2833"
_COLOR_TBD      = "#BDC3C7"
_COLOR_BYE_BG   = "#FEF9E7"
_COLOR_BYE_TEXT = "#B7950B"
_COLOR_ACCENT   = "#2980B9"


class _Slot:
    """
    Représente un emplacement dans l'arbre : soit un match réel déjà
    généré, soit un emplacement futur (TBD) en attente de vainqueurs,
    soit un bye.
    """

    def __init__(self, round_index: int, slot_index: int):
        self.round_index = round_index
        self.slot_index  = slot_index
        self.match       = None       # Match réel si déjà généré
        self.is_bye      = False
        self.bye_player  = None       # participant qualifié d'office


class BracketDetailDialog(QDialog):
    """
    Fenêtre modale affichant l'arbre de tournoi (bracket) d'une phase
    en élimination directe simple.
    """

    def __init__(self, phase: Phase, parent=None):
        super().__init__(parent)
        self._phase        = phase
        self._global_view  = False
        self._scale_factor = 1.0

        self.setWindowTitle(f"Détail — {phase.name}")
        self.setMinimumSize(1000, 650)
        self.setModal(True)
        self._build()
        self._setup_shortcuts()
        self._refresh_bracket()

    # ------------------------------------------------------------------
    # Construction de la fenêtre
    # ------------------------------------------------------------------

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        header_row = QHBoxLayout()
        title = QLabel(self._phase.name)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1C2833;")
        header_row.addWidget(title)
        header_row.addStretch()

        self._btn_global = QPushButton("🌐  Vue globale")
        self._btn_global.setObjectName("btn_secondary")
        self._btn_global.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_global.setFixedWidth(160)
        self._btn_global.clicked.connect(self._toggle_global_view)
        header_row.addWidget(self._btn_global)

        self._btn_fullscreen = QPushButton("⛶  Plein écran")
        self._btn_fullscreen.setObjectName("btn_secondary")
        self._btn_fullscreen.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_fullscreen.setFixedWidth(150)
        self._btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        header_row.addWidget(self._btn_fullscreen)

        outer.addLayout(header_row)

        subtitle = QLabel(
            f"{len(self._phase.participants)} participant(s) — "
            f"élimination directe"
        )
        subtitle.setStyleSheet("font-size: 13px; color: #7F8C8D;")
        outer.addWidget(subtitle)

        # Zone scrollable contenant l'arbre
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(self._scroll, 1)

        # Bouton fermer
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("Fermer")
        btn_close.setObjectName("btn_secondary")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setFixedWidth(120)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        outer.addLayout(btn_row)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("F11"), self).activated.connect(self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_escape)

    def _on_escape(self):
        if self.isFullScreen():
            self._toggle_fullscreen()
        elif self._global_view:
            self._toggle_global_view()
        else:
            self.reject()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self._btn_fullscreen.setText("⛶  Plein écran")
        else:
            self.showFullScreen()
            self._btn_fullscreen.setText("⛶  Quitter le plein écran")
        self._refresh_bracket()

    def _toggle_global_view(self):
        self._global_view = not self._global_view
        self._btn_global.setText(
            "🔍  Vue détaillée" if self._global_view else "🌐  Vue globale"
        )
        self._refresh_bracket()

    # ------------------------------------------------------------------
    # Construction de la structure du bracket
    # ------------------------------------------------------------------

    def _build_bracket_structure(self) -> list[list[_Slot]]:
        """
        Construit la structure de l'arbre à partir des matchs réellement
        générés dans la phase, organisés en tours successifs.

        S'appuie sur Phase._round_sizes, qui connaît la vraie taille de
        chaque tour déjà généré — y compris un éventuel premier tour de
        barrage ("play-in") dont la taille diffère de n // 2 lorsque
        l'effectif n'est pas une puissance de 2 (cf. models/generators/
        single_elim.py). Les participants ayant reçu un bye direct pour
        le tour principal (Phase._bye_participants) sont affichés à part,
        dans une colonne dédiée, tant qu'ils n'ont pas rejoint le tour
        principal.

        Returns:
            list[list[_Slot]]: liste de tours, chaque tour étant une liste
            de slots (matchs réels ou TBD).
        """
        if not self._phase.matches:
            return []

        round_sizes = list(getattr(self._phase, "_round_sizes", []))
        if not round_sizes:
            # Filet de sécurité si la phase n'a pas (encore) cette info —
            # ne devrait pas arriver avec la version actuelle de Phase.
            round_sizes = [len(self._phase.matches)]

        remaining = list(self._phase.matches)
        rounds_matches: list[list] = []
        idx = 0
        for size in round_sizes:
            chunk = remaining[idx: idx + size]
            rounds_matches.append(chunk)
            idx += size

        rounds: list[list[_Slot]] = []
        for r, matches in enumerate(rounds_matches):
            round_slots = []
            for i, m in enumerate(matches):
                slot = _Slot(r, i)
                slot.match = m
                round_slots.append(slot)
            rounds.append(round_slots)

        # Ajoute un tour TBD anticipé après le dernier tour connu,
        # pour donner une perspective sur la suite, sauf si on est déjà
        # à la finale (1 seul match) ou si le tournoi est entièrement joué.
        last_round = rounds[-1]
        if len(last_round) > 1:
            next_size = max(1, len(last_round) // 2)
            tbd_round = [_Slot(len(rounds), i) for i in range(next_size)]
            rounds.append(tbd_round)
        elif len(last_round) == 1 and last_round[0].match.state != "Finished":
            # Finale pas encore jouée : rien à ajouter, c'est le dernier tour.
            pass

        return rounds

    def _get_current_round_byes(self) -> list:
        """
        Retourne tous les participants actuellement en attente d'un bye
        (qualifiés directement pour le tour principal, sans barrage).
        Basé sur Phase._bye_participants, recalculé par Phase._update_byes().
        """
        return list(getattr(self._phase, "_bye_participants", []))

    # ------------------------------------------------------------------
    # Rendu
    # ------------------------------------------------------------------

    def _refresh_bracket(self):
        rounds = self._build_bracket_structure()

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(_COL_GAP)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if not rounds:
            empty = QLabel("Pas assez de participants pour générer un arbre.")
            empty.setStyleSheet("color: #7F8C8D; font-size: 13px;")
            layout.addWidget(empty)
        else:
            byes = self._get_current_round_byes()

            for round_idx, round_slots in enumerate(rounds):
                col = self._build_round_column(round_idx, round_slots, len(rounds))
                layout.addWidget(col)

                # La colonne des byes directs s'intercale juste après le
                # tour de barrage (tour 0) : visuellement, elle montre les
                # participants qui rejoindront le tour principal sans avoir
                # eu à jouer ce premier tour.
                if round_idx == 0 and byes:
                    layout.addWidget(self._build_byes_column(byes))

        if self._global_view:
            self._scroll.setWidget(self._build_scaled_view(container))
        else:
            self._scroll.setWidget(container)

    def _build_scaled_view(self, content_widget: QWidget) -> QWidget:
        """
        Encapsule content_widget dans un QGraphicsView et applique une
        échelle calculée pour que tout l'arbre tienne dans la zone
        visible, sans scroll (vue globale).
        """
        content_widget.adjustSize()
        natural = content_widget.sizeHint()
        nat_w   = max(natural.width(), 1)
        nat_h   = max(natural.height(), 1)

        available = self._scroll.viewport().size()
        target_w  = max(available.width() - 4, 1)
        target_h  = max(available.height() - 4, 1)
        scale     = min(target_w / nat_w, target_h / nat_h, 1.0)
        self._scale_factor = scale

        scene = QGraphicsScene()
        proxy = QGraphicsProxyWidget()
        proxy.setWidget(content_widget)
        scene.addItem(proxy)
        scene.setSceneRect(0, 0, nat_w, nat_h)

        view = QGraphicsView(scene)
        view.scale(scale, scale)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setDragMode(QGraphicsView.DragMode.NoDrag)
        view.setRenderHints(view.renderHints())
        return view

    def _build_round_column(self, round_idx: int, slots: list[_Slot], total_rounds: int) -> QWidget:
        """Construit une colonne de l'arbre pour un tour donné, avec espacement croissant."""
        col = QWidget()
        col.setFixedWidth(_COL_WIDTH)

        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = self._round_label(round_idx, total_rounds)
        header = QLabel(label)
        header.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {_COLOR_ACCENT}; "
            f"letter-spacing: 1px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        layout.addSpacing(16)

        layout.addStretch(1)
        for i, slot in enumerate(slots):
            layout.addWidget(self._build_slot_card(slot))
            if i < len(slots) - 1:
                layout.addSpacing(_ROW_GAP * (2 ** round_idx))
        layout.addStretch(1)

        return col

    def _build_byes_column(self, byes: list) -> QWidget:
        """Construit une colonne dédiée affichant tous les participants en bye direct."""
        col = QWidget()
        col.setFixedWidth(_COL_WIDTH)
        layout = QVBoxLayout(col)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(f"Qualifié(e)s d'office ({len(byes)})")
        header.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {_COLOR_BYE_TEXT}; letter-spacing: 1px;"
        )
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setWordWrap(True)
        layout.addWidget(header)
        layout.addSpacing(16)
        layout.addStretch(1)

        for i, bye_player in enumerate(byes):
            slot = _Slot(0, i)
            slot.is_bye     = True
            slot.bye_player = bye_player
            layout.addWidget(self._build_bye_card(slot))
            if i < len(byes) - 1:
                layout.addSpacing(10)

        layout.addStretch(1)
        return col

    def _round_label(self, round_idx: int, total_rounds: int) -> str:
        is_playin_round = (
            round_idx == 0
            and len(self._phase.participants) > 0
            and self._get_current_round_byes()
        )
        if is_playin_round:
            return "Barrage"

        remaining = total_rounds - round_idx
        if remaining == 1:
            return "Finale"
        if remaining == 2:
            return "Demi-finales"
        if remaining == 3:
            return "Quarts de finale"
        return f"Tour {round_idx + 1}"

    def _build_slot_card(self, slot: _Slot) -> QFrame:
        if slot.is_bye:
            return self._build_bye_card(slot)
        if slot.match is not None:
            return self._build_match_card(slot.match)
        return self._build_tbd_card()

    def _build_bye_card(self, slot: _Slot) -> QFrame:
        card = QFrame()
        card.setFixedHeight(_CARD_HEIGHT)
        card.setStyleSheet(
            f"background-color: {_COLOR_BYE_BG}; border: 1px dashed {_COLOR_BYE_TEXT}; "
            f"border-radius: 6px;"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        name = QLabel(slot.bye_player.name if slot.bye_player else "—")
        name.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {_COLOR_BYE_TEXT};")
        layout.addWidget(name)

        tag = QLabel("BYE — qualifié(e) d'office")
        tag.setStyleSheet(f"font-size: 10px; color: {_COLOR_BYE_TEXT};")
        layout.addWidget(tag)

        return card

    def _build_tbd_card(self) -> QFrame:
        card = QFrame()
        card.setFixedHeight(_CARD_HEIGHT)
        card.setStyleSheet(
            f"background-color: #F5F6FA; border: 1px dashed {_COLOR_TBD}; border-radius: 6px;"
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        for _ in range(2):
            lbl = QLabel("TBD")
            lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {_COLOR_TBD};")
            layout.addWidget(lbl)

        return card

    def _build_match_card(self, match) -> QFrame:
        a, b = match.opponents
        is_finished = match.state == "Finished"

        card = QFrame()
        card.setFixedHeight(_CARD_HEIGHT)
        border_color = "#27AE60" if is_finished else "#DDE1E7"
        card.setStyleSheet(
            f"QFrame {{ background-color: white; border: 1.5px solid {border_color}; "
            f"border-radius: 6px; }}"
        )
        if not is_finished:
            card.setCursor(Qt.CursorShape.PointingHandCursor)
            card.mousePressEvent = lambda event, m=match: self._on_match_clicked(m)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        winner = match.winner if is_finished else None

        for participant, score in zip((a, b), match.score):
            row = QHBoxLayout()
            row.setSpacing(6)

            is_winner = (participant == winner)
            name = QLabel(participant.name)
            name.setStyleSheet(
                f"font-size: 12px; font-weight: {'700' if is_winner else '500'}; "
                f"color: {'#27AE60' if is_winner else _COLOR_FINISHED if is_finished else _COLOR_PENDING};"
            )
            name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            row.addWidget(name)

            if is_finished:
                score_lbl = QLabel(str(score))
                score_lbl.setStyleSheet(
                    f"font-size: 12px; font-weight: 700; "
                    f"color: {'#27AE60' if is_winner else _COLOR_PENDING};"
                )
                row.addWidget(score_lbl)

            layout.addLayout(row)

        if not is_finished:
            hint = QLabel("Cliquer pour saisir le score")
            hint.setStyleSheet(f"font-size: 9px; color: {_COLOR_ACCENT};")
            layout.addWidget(hint)

        return card

    # ------------------------------------------------------------------
    # Saisie de score au clic
    # ------------------------------------------------------------------

    def _on_match_clicked(self, match):
        if self._global_view:
            # En vue globale on désactive la saisie (lecture seule, vue d'ensemble)
            return

        dialog = _ScoreInputDialog(match, parent=self)
        if dialog.exec():
            score_a, score_b = dialog.result_scores
            match.set_score(score_a, score_b)
            match.set_state("Finished")
            match.update_points()

            # Avance automatiquement le tour si complet
            if self._phase.is_round_complete:
                generated = self._phase.advance_round()
                if generated:
                    QMessageBox.information(
                        self, "Tour suivant",
                        f"Tour suivant généré : {len(generated)} nouveau(x) match(s)."
                    )

            self._refresh_bracket()


class _ScoreInputDialog(QDialog):
    """Petite modale de saisie du score d'un match, depuis le bracket."""

    def __init__(self, match, parent=None):
        super().__init__(parent)
        self._match = match
        self.result_scores = (0, 0)

        a, b = match.opponents
        self.setWindowTitle(f"{a.name} vs {b.name}")
        self.setMinimumWidth(360)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"{a.name}  vs  {b.name}")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1C2833;")
        layout.addWidget(title)

        row = QHBoxLayout()
        col_a = QVBoxLayout()
        col_a.addWidget(QLabel(a.name))
        self._spin_a = QSpinBox()
        self._spin_a.setRange(0, 999)
        col_a.addWidget(self._spin_a)
        row.addLayout(col_a)

        col_b = QVBoxLayout()
        col_b.addWidget(QLabel(b.name))
        self._spin_b = QSpinBox()
        self._spin_b.setRange(0, 999)
        col_b.addWidget(self._spin_b)
        row.addLayout(col_b)

        layout.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Valider")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _on_save(self):
        self.result_scores = (self._spin_a.value(), self._spin_b.value())
        self.accept()