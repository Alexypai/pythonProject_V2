import os
import sqlite3

from flask import (
    Flask, g, redirect, render_template, request, session, url_for, flash)

import db

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='ALEXY',
    DATABASE=os.path.join(app.instance_path, 'BDD_python_project.db')
)

app.secret_key = os.urandom(12)

try:
    os.makedirs(app.instance_path)
except OSError:
    pass


@app.route('/', methods=['GET', 'POST'])
def log():
    db.init_db()
    """Login page."""
    if request.method == 'POST':
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT MAIL, password,USERS_NAME FROM USERS WHERE MAIL=? AND password=?",
            (request.form['Login'], request.form['Password']))
        users = cursor.fetchone()

        if users is not None:
            session['logged_in'] = True
            session['user'] = users[2]
            flash(f'Bienvenue {session["user"]}', "success")
            return render_template("Pages/Index.html")
        else:
            flash(f'Mot de passe ou email incorect', "danger")
            return render_template('Pages/login.html')

    return render_template('Pages/login.html')


@app.route('/NewUser', methods=['GET', 'POST'])
def create():
    """Create a new user."""
    if request.method == 'POST':
        if not request.form['newLogin'] or not request.form['newPassword'] \
                or not request.form['TT'] or not request.form['nom']:
            flash(f"Un ou des champ(s) ne sont pas renseigner ", "danger")
            return render_template('Pages/nouvelUtilisateur.html')
        else:
            cursor = db.get_cursor()
            cursor.execute(
                "SELECT MAIL FROM USERS WHERE MAIL=?",
                (request.form['newLogin'],))
            check = cursor.fetchone()
            if check is not None:
                flash(f"Adresse mail deja utiliser", "danger")
                return render_template('Pages/nouvelUtilisateur.html')
            cursor.execute(
                "INSERT INTO USERS (MAIL, password,USERS_NAME,TAUX_HORAIRE,Responsibilities_Name,BIRTHDAY,CONTACT_NUMBER,ENTITY) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (request.form['newLogin'], request.form['newPassword'], request.form['nom'], request.form['TT'],
                 request.form['ROLES'], request.form['birth'], request.form['number'], request.form['Entite']))
            cursor.connection.commit()
            flash(f"Utilisateur ajouté veuillez saisir le mail et le password utilisé précedement", "success")
            return render_template('Pages/login.html')

    return render_template('Pages/nouvelUtilisateur.html')


@app.route('/logout')
def logout():               #logout user
    session['logged_in'] = False
    session.pop('user', None)
    flash(f'Vous etes déconnecter', "success")
    return render_template('Pages/login.html')


@app.route('/Index')
def index():
    if 'user' not in session:               # if user is not connected
        return render_template('Pages/login.html')
    else:                       # if user is connected
        user = session['user']
        """Application index."""
        flash(f'Bienvenue {user}', "success")
        return render_template('Pages/Index.html')


@app.route('/Annuaire', methods=['GET', 'POST'])
def employe():
    if 'user' not in session:
        return render_template('Pages/login.html')
    else:
        if request.method == 'POST':    #if we use search mode
            cursor = db.get_cursor()
            cursor.execute("SELECT USERS_NAME,TAUX_HORAIRE,BIRTHDAY,MAIL,"
                           "CONTACT_NUMBER,ENTITY,Responsibilities_Name "
                           "FROM USERS WHERE USERS_NAME=?",
                           (request.form['nom'],))
            donneesEmploye = cursor.fetchall()
            return render_template(
                'Pages/annuaire.html', donneesEmploye=donneesEmploye)
        else:                               #if we don't use search mode show all people in the app
            cursor = db.get_cursor()
            cursor.execute("SELECT USERS_NAME,TAUX_HORAIRE,BIRTHDAY,MAIL,"
                           "CONTACT_NUMBER,ENTITY,Responsibilities_Name FROM USERS")
            donneesEmploye = cursor.fetchall()
            return render_template(
                'Pages/annuaire.html', donneesEmploye=donneesEmploye)


@app.route('/Crea', methods=['GET', 'POST'])
def Crea():
    if 'user' not in session:
        return render_template('Pages/login.html')
    else:
        """Team creation page where the user must enter the project name."""
        if request.method == 'POST':
            cursor = db.get_cursor()

            cursor.execute(
                'SELECT PROJECTS_name FROM PROJECTS WHERE PROJECTS_name = (?)',
                (request.form['team_name'],))
            select_project_name = cursor.fetchone()
            if not select_project_name:
                cursor.execute(
                    'INSERT INTO PROJECTS (PROJECTS_name) VALUES (?)',
                    (request.form['team_name'],))
                cursor.connection.commit()
                New_Project = cursor.lastrowid
                return redirect(url_for('choice', New_Project=New_Project))
            else:
                flash(f"Nom d'equipe {request.form['team_name']} deja utiliser ", "danger")
                return render_template('Pages/Création_equipe.html')

        return render_template('Pages/Création_equipe.html')


@app.route('/choice/<int:New_Project>', methods=['GET', 'POST'])
def choice(New_Project):
    """Choice page when the user has validated the name of the team.

    Thanks to this page the user can adds members to the team previously
    created. Whenever an employee has been added to a team the page will
    regenerate. To leave this page, click on the end creation of a team that
    returns to the application index.

    """
    if 'user' not in session:
        return render_template('Pages/login.html')
    else:

        if request.method == 'POST':
            print(request.form['TIME'])
            if not request.form['TIME']:
                flash(f'Vous avez rentrer un temps requis vide ', "danger")
                return render_template(
                    'Pages/choice.html', New_Project=New_Project)
            elif int(request.form['TIME']) <= 0 :
                flash(f'Vous avez rentrer un temps requis incorrect ', "danger")
                return render_template(
                    'Pages/choice.html', New_Project=New_Project)
            else:
                cursor = db.get_cursor()
                cursor.execute(
                    'SELECT USERS_ID,TAUX_HORAIRE FROM USERS WHERE Responsibilities_Name = (?)',
                    (request.form['ROLES'],))
                select_all_users_by_role = cursor.fetchall() #Select all user from function choice by user
                Total_user = []
                for i in range(len(select_all_users_by_role)):      #For each user, calculate the time available for each
                    user_id = select_all_users_by_role[i][0]
                    cursor.execute(
                        'SELECT TIME FROM USERS_BY_PROJECT WHERE USERS_ID = (?)',
                        (user_id,))
                    select_all_project_by_user_selected = cursor.fetchall()
                    total = 0
                    for i2 in range(len(select_all_project_by_user_selected)):  #Calculate time depending by project assignement
                        count_time = select_all_project_by_user_selected[i2][0]
                        total = total + count_time
                    time_available = select_all_users_by_role[i][1] - total
                    user_append = [user_id, time_available]
                    Total_user.append(user_append)
                selected_by_time = 0
                user_final_selected = 9999999999
                for i3 in range(len(Total_user)):       #Select User choice by the algorithm with the most time availible
                    if Total_user[i3][1] > selected_by_time:
                        user_final_selected = Total_user[i3][0]
                if user_final_selected == 9999999999:
                    flash(f'Tous les employés au role : {request.form["ROLES"]} sont actuellement occupé  ', "danger")
                    return render_template(
                        'Pages/choice.html', New_Project=New_Project)
                else:
                    cursor.execute(
                        "INSERT INTO USERS_BY_PROJECT (TIME,USERS_ID,PROJECTS_ID) "
                        "VALUES (?,?,?)", (request.form['TIME'], user_final_selected, New_Project))
                    cursor.connection.commit()

                    cursor.execute("SELECT USERS_NAME FROM USERS  WHERE USERS_ID = (?)", (user_final_selected,))
                    select_name = cursor.fetchone()
                    user_name = select_name[0]

                    flash(f'Employé {user_name} Ajouté !'
                          ' Vous pouvez continuer ou valide votre equipe en cliquant sur fin création d equipe', "success")

                    return render_template(
                        'Pages/choice.html', New_Project=New_Project)

        return render_template('Pages/choice.html', New_Project=New_Project)


@app.route('/Equipe')
def Equipe():
    """Current projects and users linked to the different projects."""
    if 'user' not in session:
        return render_template('Pages/login.html')
    else:
        cursor = db.get_cursor()
        cursor.execute(
            "SELECT USERS_BY_PROJECT.USERS_ID,USERS.USERS_NAME,"
            "USERS_BY_PROJECT.PROJECTS_ID,PROJECTS.PROJECTS_name,"
            "USERS_BY_PROJECT.TIME FROM PROJECTS "
            "INNER JOIN ("
            "USERS INNER "
            "JOIN USERS_BY_PROJECT ON USERS.USERS_ID = USERS_BY_PROJECT.USERS_ID) "
            "ON PROJECTS.PROJECTS_ID = USERS_BY_PROJECT.PROJECTS_ID ")
        users = cursor.fetchall()

        cursor.execute("SELECT * FROM PROJECTS")
        equipe = cursor.fetchall()

        return render_template(
            'Pages/Equipe_cree.html', Equipe=equipe, Users=users)


@app.route('/Delete', methods=['GET', 'POST'])
def Delete():
    """Delete a project according to the project id."""
    if 'user' not in session:
        return render_template('Pages/login.html')
    else:
        if request.method == 'POST':
            if request.form['name'] == 'Initialisation':
                flash('Impossible de supprimer cette equipe', "danger")
                return render_template('Pages/Delete.html')
            cursor = db.get_cursor()

            cursor.execute("SELECT PROJECTS_ID FROM PROJECTS WHERE PROJECTS_name = (?)", (request.form['name'],))
            select_project_id = cursor.fetchone()
            if not select_project_id:
                flash('Equipe invalide', "danger")
                return render_template('Pages/Delete.html')
            else:
                project_id = select_project_id[0]

                cursor.execute(
                    "DELETE FROM PROJECTS WHERE PROJECTS_ID = ?",
                    (project_id,))

                cursor.execute(
                    "DELETE FROM USERS_BY_PROJECT WHERE PROJECTS_ID = ?",
                    (project_id,))
                cursor.connection.commit()
                flash(f"Equipe {request.form['name']} supprimé ! Vous pouvez continuer ou utilisé le menu "
                      "ci dessus pour d'autres fonctionnalités", "success")
                return render_template('Pages/Delete.html')

        return render_template('Pages/Delete.html')
