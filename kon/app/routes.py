from flask import render_template, flash, redirect, url_for, request, jsonify
from app import app, db
from app.forms import LoginForm, RegistrationForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Vote
from werkzeug.urls import url_parse
from sqlalchemy import update
import csv, random

users =[
]
sameplace =[
]
years =[
]
year1=2000
year2=2001
yearDictionary = dict()
cities = [
]
with open('years.txt', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            yearAndScore ={
                "year": row["Year"],
                "value": row["Value"]
            }
            if row["Region"] not in cities:
                cities.append(row["Region"])
            if (yearDictionary.get(row["Region"])==None):
                yearDictionary.setdefault(row["Region"], [])
            yearDictionary.get(row["Region"]).append(yearAndScore)
            line_count += 1

def Sortandincrease(sub_li, index): 
    l = len(sub_li) 
    for i in range(0, l): 
        if (sub_li[i]["id"]==index):
            sub_li[i]["score"]+=50
        for j in range(0, l-i-1): 
            if (sub_li[j]["score"] < sub_li[j + 1]["score"]): 
                tempo = sub_li[j] 
                sub_li[j]= sub_li[j + 1] 
                sub_li[j + 1]= tempo 
    return sub_li 

def Sort(sub_li): 
    l = len(sub_li) 
    for i in range(0, l): 
        for j in range(0, l-i-1): 
            if (sub_li[j]["score"] < sub_li[j + 1]["score"]): 
                tempo = sub_li[j] 
                sub_li[j]= sub_li[j + 1] 
                sub_li[j + 1]= tempo 
    return sub_li 

@app.before_request
def before_request():
    global users
    users=[]
    current = User.query.all()
    for person in current:
        user = {
            "id": person.id,
            "name": person.username,
            "score": person.score,
            "location": person.location
        }
        users.append(user)
    Sort(users)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global sameplace
    sameplace = []
    if current_user.is_authenticated:
        for user in users:
            if (user["location"]==current_user.location):
                sameplace.append(user)
        return redirect(url_for('game'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        for user in users:
            if (user["location"]==current_user.location):
                sameplace.append(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('game')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('game'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    global cities
    if current_user.is_authenticated:
        return redirect(url_for('game'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, score =0, location = form.location.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form, cities=cities)

@app.route('/')
@app.route('/game')
@login_required
def game():
    global year1
    global year2
    if not sameplace:
        for user in users:
            if (user["location"]==current_user.location):
                sameplace.append(user)
    votes = current_user.votes.all()
    found = True
    while (found):
        found = False
        first = random.randint(2000, 2019)
        second = random.randint(2000, 2019)
        if(first == second):
            if (first==2019):
                second= random.randint(2000, 2018)
            else:
                second=second+1
        for vote in votes:
            if (vote.year1 == first and vote.year2 == second):
                found = True
                break
    return render_template('game.html', users=sameplace, year1=first, year2=second)

@app.route('/button', methods=['GET', 'POST'])
def button():
    global users
    global years
    global year1
    global year2

    json_data = request.get_json()
    buttonPressed = int(json_data["button"])
    first = int(json_data["year1"])
    second = int(json_data["year2"])

    if (buttonPressed==4):
        vote = Vote(year1=first, year2=second, answer="?", author=current_user)
        db.session.add(vote)
        db.session.commit()
        votes = current_user.votes.all()
        found = True
        while (found):
            found = False
            first = random.randint(2000, 2019)
            second = random.randint(2000, 2019)
            if(first == second):
                if (first==2019):
                    second= random.randint(2000, 2018)
                else:
                    second=second+1
            for vote in votes:
                if (vote.year1 == first and vote.year2 == second):
                    found = True
                    break
        score = current_user.score
        return jsonify(users=sameplace, year1=first, year2=second, score = score, name = current_user.username)
    
    rank1 = 0
    rank2 = 0
    for year in yearDictionary.get(current_user.location):
        if (int(year["year"])==first):
            rank1 = int(year["value"])
        if (int(year["year"])==second):
            rank2 = int(year["value"])
    if(buttonPressed==1):
        print (rank1, rank2)
        vote = Vote(year1=first, year2=second, answer=str(first), author=current_user)
        db.session.add(vote)
        db.session.commit()
        if(rank1>rank2):
            u = User.query.get(current_user.id)
            u.increase_score(50)
            db.session.commit()
            Sortandincrease(sameplace, current_user.id)
    if(buttonPressed==2):
        print (rank1, rank2)
        vote = Vote(year1=first, year2=second, answer=str(second), author=current_user)
        db.session.add(vote)
        db.session.commit()
        if(rank2>rank1):
            u = User.query.get(current_user.id)
            u.increase_score(50)
            db.session.commit()
            Sortandincrease(sameplace, current_user.id)
    if(buttonPressed==3):
        print (rank1, rank2)
        vote = Vote(year1=first, year2=second, answer="=", author=current_user)
        db.session.add(vote)
        db.session.commit()
        if(rank2==rank1):
            u = User.query.get(current_user.id)
            u.increase_score(50)
            db.session.commit()
            Sortandincrease(sameplace, current_user.id)
    votes = current_user.votes.all()
    found = True
    while (found):
        found = False
        first = random.randint(2000, 2019)
        second = random.randint(2000, 2019)
        if(first == second):
            if (first==2019):
                second= random.randint(2000, 2018)
            else:
                second=second+1
        for vote in votes:
            if (vote.year1 == first and vote.year2 == second):
                found = True
                break
    score = current_user.score

    return jsonify(users=sameplace, year1=first, year2=second, score = score, name = current_user.username)
