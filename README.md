# Goal Tracker

Une application web pour suivre la progression d'un programme avec objectifs et tâches.

## Fonctionnalités

### Objectifs
- **Binaires** : Réalisé ou non (Oui/Non)
- **Numériques** : Avec une cible à atteindre
- **Fréquences** : 
  - Journalier (1 point par jour)
  - Hebdomadaire (5 points par semaine)
  - Programme entier (15 points total)

### Tâches
- Éléments binaires à réaliser sur l'ensemble du programme
- 5 points par tâche

### Calculs de progression
- **Progression actuelle** : Points obtenus / Points totaux
- **Progression attendue** : Prorata des jours écoulés
- **Statut** : Dans les temps ou en retard

## Installation

### Prérequis
- Python 3.7 ou plus récent
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Cloner ou télécharger le projet**
```bash
git clone <url-du-repo>
cd goal-tracker
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Lancer l'application**
```bash
python app.py
```

4. **Ouvrir dans le navigateur**
   - Accéder à http://localhost:5000
   - L'application s'ouvre automatiquement sur la page de configuration si aucun programme n'est défini

## Utilisation

### Première utilisation

1. **Configuration initiale** : Créer votre premier programme avec des objectifs et tâches
2. **Définir les objectifs** : Choisir le type, la fréquence et les paramètres
3. **Ajouter des tâches** : Définir les tâches à réaliser pendant le programme

### Suivi quotidien

1. **Page Daily** : Enregistrer les progrès jour par jour
2. **Dashboard** : Visualiser l'avancement global et individuel
3. **Todo** : Consulter les tâches à réaliser

### Interface de Suivi

Le **Dashboard** affiche tous vos objectifs organisés par type :

#### 📅 **Objectifs Journaliers** 
- À réaliser chaque jour
- Exemples : marcher 10 000 pas, boire 2L d'eau

#### 📊 **Objectifs Hebdomadaires**
- À réaliser sur la semaine
- Exemples : sport 3 fois par semaine, lire 1h par jour
- **Saisie** : Cochez/saisissez chaque jour, le système calcule par semaine

#### 🎯 **Objectifs du Programme**
- À réaliser sur toute la durée
- Exemples : courir 100km, perdre 3kg, lire 5 livres
- **Saisie** : Entrez vos données quotidiennes, le système accumule

### Types de Calcul

- **Cumulatif** : Additionne vos saisies (km de course, livres lus...)
- **Décroissant** : Pour perdre du poids, réduire un temps...
- **Dernière valeur** : Prend votre dernière saisie (poids actuel, score...)

### Conseils

- Utilisez le **sélecteur de date** pour saisir des données passées
- Les **unités** s'affichent automatiquement (km, kg, livres...)
- La **progression totale** est visible en temps réel pour les objectifs cumulatifs

## Structure du projet

```
goal-tracker/
├── app.py                    # Application Flask principale
├── tracker.py                # Logique métier et calculs
├── requirements.txt          # Dépendances Python
├── example_config.md         # Guide de configuration avec exemples
├── README.md                 # Ce fichier
├── data/                     # Données des programmes
│   ├── current_program.txt   # Programme actuel sélectionné
│   └── {program_name}/       # Dossier par programme
│       ├── program.json      # Configuration du programme
│       └── user_data.csv     # Données de progression
├── templates/                # Templates HTML
│   ├── base.html
│   ├── dashboard.html
│   ├── daily.html
│   ├── setup.html
│   ├── todo.html
│   └── progress_explanation.html
└── old_files/               # Ancienne version (archive)
```

## Structure des données

### Programme (`data/{program_name}/program.json`)
Contient la configuration du programme :
- Informations générales (nom, dates)
- Liste des objectifs avec leurs paramètres
- Liste des tâches

### Données utilisateur (`data/{program_name}/user_data.csv`)
Contient les données de progression :
- Date, ID de l'objectif/tâche, type, valeur

## API

L'application expose plusieurs endpoints API :

- `GET /api/dashboard` : Données du tableau de bord
- `POST /api/save_program` : Sauvegarder un programme
- `POST /api/save_data` : Sauvegarder une entrée de données
- `GET /api/progress` : Données de progression
- `GET /api/current_program` : Programme actuel

## Développement

### Structure du code

- **`app.py`** : Routes Flask et logique web
- **`tracker.py`** : Classe ProgressTracker avec la logique métier
- **`templates/`** : Templates Jinja2 pour l'interface utilisateur

### Lancement en mode développement

```bash
export FLASK_ENV=development
python app.py
```

L'application se recharge automatiquement lors des modifications du code.

## Fonctionnalités avancées

- **Gestion multi-programmes** : Possibilité de créer et basculer entre plusieurs programmes
- **Sélecteur de date** : Saisie de données passées
- **Calculs automatiques** : Progression en temps réel
- **Interface responsive** : Optimisée pour mobile et desktop

## Contribution

Pour contribuer au projet :
1. Fork le repository
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

L'interface est optimisée pour une utilisation simple et efficace avec un design minimaliste. 