# TournamentApp
A full-stack tournament management application — create brackets, manage players, track scores and results in real time.


TournamentApp/
├── main.py                    
├── models/
│   ├── __init__.py
│   ├── config.py              → config du tournoi 
│   ├── match.py               → definition d'un objet Match
│   ├── phase.py               → definition d'une phase d'un tournoi
│   ├── players.py             → definition d'un objet Player
│   ├── teams.py               → definition d'un objet Team
│   ├── tournament.py          → definition d'un objet Tournament
│   └── generators/
│       ├── __init__.py         
│       ├── double_elim.py     → fonctionnement des tableaux à double éliminitations
│       ├── single_elim.py     → fonctionnement des élimination directe
│       ├── swiss.py           → fonctionnement des swiss
│       └── pool.py            → fonctionnement des poules
└── cli/
    ├── __init__.py
    ├── app.py                 → boucle principale + menu
    ├── tournament_ui.py       → créer un tournoi, résumé
    ├── participant_ui.py      → inscrire joueurs / équipes
    ├── phase_ui.py            → ajouter une phase, tour suivant
    ├── match_ui.py            → résultats, classement, matchs
    └── utils.py               → input_int, input_str, input_yn, choose...