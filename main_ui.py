"""
main_ui.py

Point d'entrée de l'interface graphique de TournamentApp.
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window  import MainWindow


def run():
    app    = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
