# PFE_APP

Ce dépôt contient une application Django (PFE). Ce README explique comment préparer, tester et publier le projet sur GitHub de façon professionnelle.

Prérequis
- Python 3.8+
- Git
- (optionnel) `gh` CLI pour automatiser la création du repo

Installation locale
1. Créer un environnement virtuel et l'activer:
```
python -m venv venv
venv\Scripts\activate
```
2. Installer les dépendances:
```
pip install -r requirements.txt
```
3. Appliquer les migrations et lancer le serveur:
```
python manage.py migrate
python manage.py runserver
```

Tests
```
python manage.py test
```

Publier sur GitHub (exemples)
1. Initialiser le dépôt local et valider:
```
git init
git add .
git commit -m "Initial commit"
```
2a. Créer le repo distant via `gh` et pousser:
```
gh repo create mon-organisation/nom-repo --public --source=. --remote=origin --push
```
2b. Ou créer le repo sur github.com puis lier et pousser:
```
git remote add origin https://github.com/<votre-compte>/<nom-repo>.git
git branch -M main
git push -u origin main
```

Notes pro
- Ne commitez jamais les secrets: utilisez un fichier `.env` (ignoré via `.gitignore`).
- Supprimez la DB locale avant le push si nécessaire (`git rm --cached db.sqlite3`).
- Ajoutez un `LICENSE` (MIT par défaut) et un fichier `CONTRIBUTING` si vous attendez des contributeurs.
- Activez GitHub Actions (workflow inclus) pour tests automatisés.