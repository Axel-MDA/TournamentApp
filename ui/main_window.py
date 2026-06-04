"""
ui/main_window.py

Fenêtre principale de TournamentApp.
Contient la sidebar et la zone de contenu avec les différentes vues.
"""
from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QMessageBox
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QIcon

from models.tournament import Tournament
from .style            import STYLESHEET
from .widgets.sidebar  import Sidebar
from .views.home_view         import HomeView
from .views.participants_view import ParticipantsView
from .views.phase_view        import PhaseView
from .views.matches_view      import MatchesView
from .views.standings_view    import StandingsView


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self._tournament: Tournament | None = None
        self._setup_window()
        self._build()
        self._connect_signals()
        self._navigate("home")

    def _setup_window(self):
        self.setWindowTitle("Tournament App")
        self.setMinimumSize(1000, 650)
        self.resize(1200, 720)
        self.setStyleSheet(STYLESHEET)

    def _build(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        root.addWidget(self._sidebar)

        # Zone de contenu
        self._stack = QStackedWidget()
        root.addWidget(self._stack)

        # Vues
        self._home_view         = HomeView()
        self._participants_view = ParticipantsView()
        self._phase_view        = PhaseView()
        self._matches_view      = MatchesView()
        self._standings_view    = StandingsView()

        self._views = {
            "home":         self._home_view,
            "participants": self._participants_view,
            "phases":       self._phase_view,
            "matches":      self._matches_view,
            "standings":    self._standings_view,
        }

        for view in self._views.values():
            self._stack.addWidget(view)

    def _connect_signals(self):
        self._sidebar.nav_clicked.connect(self._navigate)
        self._home_view.tournament_created.connect(self._on_tournament_created)

    def _navigate(self, key: str):
        if key != "home" and self._tournament is None:
            QMessageBox.information(
                self, "Aucun tournoi",
                "Crée d'abord un tournoi depuis l'accueil."
            )
            key = "home"

        view = self._views.get(key)
        if view is None:
            return

        # Rafraîchit les vues qui en ont besoin
        if key == "participants" and self._tournament:
            self._participants_view.set_tournament(self._tournament)
        elif key == "phases" and self._tournament:
            self._phase_view.set_tournament(self._tournament)
        elif key == "matches" and self._tournament:
            self._matches_view.set_tournament(self._tournament)
        elif key == "standings" and self._tournament:
            self._standings_view.set_tournament(self._tournament)

        self._stack.setCurrentWidget(view)
        self._sidebar.set_active(key)

    def _on_tournament_created(self, tournament: Tournament):
        self._tournament = tournament
        self._sidebar.update_tournament_info(
            name           = tournament.name,
            sport          = tournament.sport,
            status         = tournament.status,
            nb_participants= len(tournament.participants),
        )
        QMessageBox.information(
            self, "Tournoi créé",
            f"Tournoi '{tournament.name}' créé avec succès !\n"
            f"Tu peux maintenant inscrire des participants."
        )
        self._navigate("participants")
