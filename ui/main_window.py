"""
ui/main_window.py  (version avec sauvegarde / chargement JSON)

Fenêtre principale de TournamentApp.
Ajoute un menu Fichier avec Sauvegarder (Ctrl+S) et Ouvrir (Ctrl+O).
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QStackedWidget,
    QMessageBox, QFileDialog, QMenuBar
)
from PyQt6.QtCore import Qt, QStandardPaths
from PyQt6.QtGui  import QIcon, QKeySequence, QAction

from models.tournament  import Tournament
from models.persistence import save_tournament, load_tournament
from .style             import STYLESHEET
from .widgets.sidebar   import Sidebar
from .views.home_view         import HomeView
from .views.participants_view import ParticipantsView
from .views.phase_view        import PhaseView
from .views.matches_view      import MatchesView
from .views.standings_view    import StandingsView


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""

    def __init__(self):
        super().__init__()
        self._tournament:   Tournament | None = None
        self._current_file: Path | None       = None   # dernier fichier utilisé
        self._setup_window()
        self._build()
        self._build_menu()
        self._connect_signals()
        self._navigate("home")

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

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

        self._sidebar = Sidebar()
        root.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        root.addWidget(self._stack)

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

    def _build_menu(self):
        """Crée la barre de menu Fichier avec Ouvrir / Sauvegarder / Sauvegarder sous."""
        menubar = self.menuBar()

        file_menu = menubar.addMenu("Fichier")

        act_open = QAction("Ouvrir un tournoi…", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._on_open)
        file_menu.addAction(act_open)

        file_menu.addSeparator()

        act_save = QAction("Sauvegarder", self)
        act_save.setShortcut(QKeySequence("Ctrl+S"))
        act_save.triggered.connect(self._on_save)
        file_menu.addAction(act_save)

        act_save_as = QAction("Sauvegarder sous…", self)
        act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        act_save_as.triggered.connect(self._on_save_as)
        file_menu.addAction(act_save_as)

    def _connect_signals(self):
        self._sidebar.nav_clicked.connect(self._navigate)
        self._home_view.tournament_created.connect(self._on_tournament_created)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _navigate(self, key: str):
        if key != "home" and self._tournament is None:
            QMessageBox.information(
                self, "Aucun tournoi",
                "Crée ou ouvre d'abord un tournoi."
            )
            key = "home"

        view = self._views.get(key)
        if view is None:
            return

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

    # ------------------------------------------------------------------
    # Création de tournoi
    # ------------------------------------------------------------------

    def _on_tournament_created(self, tournament: Tournament):
        self._tournament   = tournament
        self._current_file = None
        self._update_sidebar()
        self._update_title()
        QMessageBox.information(
            self, "Tournoi créé",
            f"Tournoi '{tournament.name}' créé avec succès !\n"
            f"Tu peux maintenant inscrire des participants."
        )
        self._navigate("participants")

    # ------------------------------------------------------------------
    # Sauvegarde
    # ------------------------------------------------------------------

    def _on_save(self):
        if not self._tournament:
            QMessageBox.warning(self, "Aucun tournoi", "Aucun tournoi à sauvegarder.")
            return
        if self._current_file:
            self._save_to(self._current_file)
        else:
            self._on_save_as()

    def _on_save_as(self):
        if not self._tournament:
            QMessageBox.warning(self, "Aucun tournoi", "Aucun tournoi à sauvegarder.")
            return

        default_dir  = _default_save_dir()
        default_name = _safe_filename(self._tournament.name) + ".json"
        filepath, _  = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le tournoi",
            str(default_dir / default_name),
            "Tournoi JSON (*.json);;Tous les fichiers (*)",
        )
        if filepath:
            self._save_to(Path(filepath))

    def _save_to(self, path: Path):
        try:
            save_tournament(self._tournament, path)
            self._current_file = path
            self._update_title()
            self.statusBar().showMessage(f"Sauvegardé : {path}", 4000)
        except Exception as e:
            QMessageBox.critical(self, "Erreur de sauvegarde", str(e))

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def _on_open(self):
        default_dir = _default_save_dir()
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Ouvrir un tournoi",
            str(default_dir),
            "Tournoi JSON (*.json);;Tous les fichiers (*)",
        )
        if not filepath:
            return

        try:
            tournament = load_tournament(filepath)
        except Exception as e:
            QMessageBox.critical(self, "Erreur de chargement", str(e))
            return

        self._tournament   = tournament
        self._current_file = Path(filepath)
        self._update_sidebar()
        self._update_title()

        QMessageBox.information(
            self, "Tournoi chargé",
            f"Tournoi '{tournament.name}' chargé !\n"
            f"  Participants : {len(tournament.participants)}\n"
            f"  Phases       : {len(tournament.phases)}\n"
            f"  Statut       : {tournament.status}"
        )
        self._navigate("participants")

    # ------------------------------------------------------------------
    # Helpers UI
    # ------------------------------------------------------------------

    def _update_sidebar(self):
        if self._tournament:
            self._sidebar.update_tournament_info(
                name            = self._tournament.name,
                sport           = self._tournament.sport,
                status          = self._tournament.status,
                nb_participants = len(self._tournament.participants),
            )

    def _update_title(self):
        base = "Tournament App"
        if self._tournament:
            base = f"{self._tournament.name} — Tournament App"
            if self._current_file:
                base += f" [{self._current_file.name}]"
        self.setWindowTitle(base)


# ------------------------------------------------------------------
# Utilitaires
# ------------------------------------------------------------------

def _default_save_dir() -> Path:
    """Retourne le dossier ./saves/, le crée si besoin."""
    saves = Path("saves")
    saves.mkdir(exist_ok=True)
    return saves


def _safe_filename(name: str) -> str:
    """Convertit un nom de tournoi en nom de fichier sûr."""
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)
    return safe.strip().replace(" ", "_").lower()