"""
ui/style.py

Palette de couleurs et feuille de style globale de l'application.
Sobre et professionnel : blanc cassé, gris anthracite, bleu acier.
"""

COLORS = {
    "bg_main":       "#F5F6FA",
    "bg_sidebar":    "#1E2A3A",
    "bg_card":       "#FFFFFF",
    "bg_hover":      "#2C3E55",
    "bg_selected":   "#2980B9",
    "accent":        "#2980B9",
    "accent_light":  "#5DADE2",
    "accent_dark":   "#1A5276",
    "text_primary":  "#1C2833",
    "text_secondary":"#7F8C8D",
    "text_sidebar":  "#BDC3C7",
    "text_white":    "#FFFFFF",
    "border":        "#DDE1E7",
    "success":       "#27AE60",
    "warning":       "#E67E22",
    "danger":        "#E74C3C",
}

STYLESHEET = f"""
/* === Fenêtre principale === */
QMainWindow, QWidget#central {{
    background-color: {COLORS['bg_main']};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
}}

/* === Sidebar === */
QWidget#sidebar {{
    background-color: {COLORS['bg_sidebar']};
    border-right: 1px solid #16202E;
}}

QLabel#app_title {{
    color: {COLORS['text_white']};
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 8px 0px;
}}

QLabel#app_subtitle {{
    color: {COLORS['text_sidebar']};
    font-size: 11px;
    letter-spacing: 2px;
    padding-bottom: 4px;
}}

QPushButton#nav_btn {{
    background-color: transparent;
    color: {COLORS['text_sidebar']};
    border: none;
    text-align: left;
    padding: 12px 20px;
    font-size: 13px;
    border-radius: 0px;
}}

QPushButton#nav_btn:hover {{
    background-color: {COLORS['bg_hover']};
    color: {COLORS['text_white']};
}}

QPushButton#nav_btn[active=true] {{
    background-color: {COLORS['bg_selected']};
    color: {COLORS['text_white']};
    border-left: 3px solid {COLORS['accent_light']};
}}

QLabel#section_label {{
    color: #546E7A;
    font-size: 10px;
    letter-spacing: 2px;
    font-weight: 600;
    padding: 16px 20px 4px 20px;
}}

QLabel#tournament_info {{
    color: {COLORS['text_sidebar']};
    font-size: 11px;
    padding: 4px 20px;
}}

/* === Zone de contenu === */
QLabel#page_title {{
    color: {COLORS['text_primary']};
    font-size: 22px;
    font-weight: 700;
    padding-bottom: 4px;
}}

QLabel#page_subtitle {{
    color: {COLORS['text_secondary']};
    font-size: 13px;
    padding-bottom: 16px;
}}

/* === Cartes === */
QFrame#card {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 16px;
}}

/* === Formulaires === */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1.5px solid {COLORS['accent']};
    outline: none;
}}

QLabel#field_label {{
    color: {COLORS['text_primary']};
    font-size: 12px;
    font-weight: 600;
    padding-bottom: 4px;
}}

/* === Boutons === */
QPushButton#btn_primary {{
    background-color: {COLORS['accent']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#btn_primary:hover {{
    background-color: {COLORS['accent_light']};
}}

QPushButton#btn_primary:pressed {{
    background-color: {COLORS['accent_dark']};
}}

QPushButton#btn_secondary {{
    background-color: transparent;
    color: {COLORS['accent']};
    border: 1.5px solid {COLORS['accent']};
    border-radius: 6px;
    padding: 9px 24px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#btn_secondary:hover {{
    background-color: #EBF5FB;
}}

QPushButton#btn_danger {{
    background-color: {COLORS['danger']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 24px;
    font-size: 13px;
    font-weight: 600;
}}

QPushButton#btn_danger:hover {{
    background-color: #EC7063;
}}

/* === Tableaux === */
QTableWidget {{
    background-color: {COLORS['bg_card']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border']};
    font-size: 13px;
    color: {COLORS['text_primary']};
}}

QTableWidget::item {{
    padding: 10px 12px;
    border-bottom: 1px solid {COLORS['border']};
}}

QTableWidget::item:selected {{
    background-color: #EBF5FB;
    color: {COLORS['text_primary']};
}}

QHeaderView::section {{
    background-color: #F8F9FB;
    color: {COLORS['text_secondary']};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    padding: 10px 12px;
    border: none;
    border-bottom: 2px solid {COLORS['border']};
}}

/* === Divers === */
QScrollBar:vertical {{
    background: {COLORS['bg_main']};
    width: 6px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 3px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QMessageBox {{
    background-color: {COLORS['bg_card']};
    font-size: 13px;
}}

QRadioButton {{
    font-size: 13px;
    color: {COLORS['text_primary']};
    spacing: 8px;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
}}
"""
