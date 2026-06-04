"""
ui/widgets/sidebar.py

Composant sidebar fixe avec navigation et infos du tournoi en cours.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore    import Qt, pyqtSignal


class Sidebar(QWidget):
    """
    Sidebar de navigation fixe à gauche.

    Signals:
        nav_clicked (str): Émis quand un bouton de navigation est cliqué.
                           Valeur : identifiant de la vue ('home', 'participants', ...).
    """

    nav_clicked = pyqtSignal(str)

    _NAV_ITEMS = [
        ("home",         "🏠  Accueil"),
        ("participants", "👥  Participants"),
        ("phases",       "🏆  Phases"),
        ("matches",      "⚔️   Matchs"),
        ("standings",    "📊  Classement"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._buttons: dict[str, QPushButton] = {}
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tête
        header = QWidget()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: #162435; border-bottom: 1px solid #16202E;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(2)

        title = QLabel("TOURNAMENT")
        title.setObjectName("app_title")
        subtitle = QLabel("APP")
        subtitle.setObjectName("app_subtitle")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Section navigation
        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("section_label")
        layout.addWidget(nav_label)

        for key, label in self._NAV_ITEMS:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setProperty("active", False)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, k=key: self.nav_clicked.emit(k))
            self._buttons[key] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Infos tournoi en bas
        self._separator = QFrame()
        self._separator.setFrameShape(QFrame.Shape.HLine)
        self._separator.setStyleSheet("color: #2C3E55;")
        layout.addWidget(self._separator)

        self._tournament_label = QLabel("Aucun tournoi actif")
        self._tournament_label.setObjectName("tournament_info")
        self._tournament_label.setWordWrap(True)
        layout.addWidget(self._tournament_label)

        self._status_label = QLabel("")
        self._status_label.setObjectName("tournament_info")
        layout.addWidget(self._status_label)

        spacer = QWidget()
        spacer.setFixedHeight(16)
        layout.addWidget(spacer)

    def set_active(self, key: str):
        """Met en surbrillance le bouton de navigation actif."""
        for k, btn in self._buttons.items():
            btn.setProperty("active", k == key)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def update_tournament_info(self, name: str, sport: str, status: str, nb_participants: int):
        """Met à jour les infos du tournoi affichées en bas de la sidebar."""
        self._tournament_label.setText(f"📌 {name} — {sport}")
        self._status_label.setText(
            f"   {nb_participants} participants · {status}"
        )
