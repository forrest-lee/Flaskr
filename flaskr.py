# all the imports
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import string
import math

# configuration
DATABASE = './flaskr.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()
    g.db.close()


@app.route('/',methods=['GET','POST'])
def show_entries():
    #cur = g.db.execute('select title, text from entries order by id desc')
    p = request.args.get('page','0')    #get url query parameter 'page'
    p = string.atoi(p)  # convert string to int
    POST_PER_PAGE = 5

    if request.method == 'POST':
        pagenumber = int(request.form['pagenumber'])
        p = (pagenumber - 1) * POST_PER_PAGE
        
    cur = g.db.execute('select COUNT(*) from entries;')
    totals = cur.fetchall()[0][0]
    g.db.commit()

    cur = g.db.execute('select title,substr(text,1,120),id from entries order by id desc limit ' + str(p) + ',5;')
    g.db.commit()
    entries = [dict(title=row[0], text=row[1]+"...", id=row[2]) for row in cur.fetchall()]


    if p - POST_PER_PAGE < 0:
        p = 0
        #flash("It's the first page!")
    elif p + POST_PER_PAGE > totals:
        p = int(math.floor(totals / float(POST_PER_PAGE)) * POST_PER_PAGE )
        #flash("It's the last page!")
    
    pagetotal = []
    pagetotal.append(p)
    pagetotal.append(int(math.floor(totals / float(POST_PER_PAGE)) * POST_PER_PAGE ))
    pagetotal.append(totals)

    pages = []
    pagesize = int( math.ceil(totals / float(POST_PER_PAGE)) )
    for i in range(pagesize):
        pages.append(i)
    return render_template('show_entries.html', entries=entries, pagetotal=pagetotal, pages=pages)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    g.db.execute('insert into entries (title, text) values (?, ?)',
                 [request.form['title'], request.form['text']])
    g.db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     error = None
#     if request.method == 'POST':
#         if request.form['username'] != app.config['USERNAME']:
#             error = 'Invalid username'
#         elif request.form['password'] != app.config['PASSWORD']:
#             error = 'Invalid password'
#         else:
#             session['logged_in'] = True
#             flash('You were logged in')
#             return redirect(url_for('show_entries'))
#     return render_template('login.html', error=error)

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        cur = g.db.cursor()
        cur.execute('select * from users where username = (?) and password = (?);',
            [request.form['username'], request.form['password']])
        res = cur.fetchall()
        g.db.commit()
        if(res == []):
            error = 'login info incorrect'
            return render_template('login.html', error=error)
        else:
            flash('Welcome, ' + str(res[0][0]) + '!')
            session['logged_in'] = True
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/register',methods=['GET','POST'])
def register():
    error = None
    if request.method == 'GET':
        return render_template('register.html', error=error)
    elif request.method == 'POST':
        g.db.execute('insert into users (username, password) values (?, ?)',
                 [request.form['username'], request.form['password']])
        g.db.commit()
        flash('New User was successfully Sign Up')
        session['logged_in'] = True
        return redirect(url_for('show_entries'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))



@app.route('/article')
def show_article():
    articleId = int(request.args.get('id', '0'))
    cur = g.db.execute('select title,text from entries where id = (?);', [articleId])
    g.db.commit()
    resultRow = cur.fetchall()[0]
    article = dict(title=resultRow[0], text=resultRow[1])
    return render_template('show_article.html', article=article)


if __name__ == '__main__':
    app.run()
