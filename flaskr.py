#coding:utf8
# all the imports
import MySQLdb
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from contextlib import closing
import string
import math
import re

# configuration
MYSQL_DB = 'flaskr'
DEBUG = True
SECRET_KEY = ''
MYSQL_USER = 'root'
MYSQL_PASS = ''
MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = '3306'

# 针对SAE配置
try:
    isSae = True
    import sae.const
    MYSQL_DB = sae.const.MYSQL_DB
    # DEBUG = False
    SECRET_KEY = ''
    MYSQL_USER = sae.const.MYSQL_USER
    MYSQL_PASS = sae.const.MYSQL_PASS
    MYSQL_HOST = sae.const.MYSQL_HOST
    MYSQL_PORT = sae.const.MYSQL_PORT
except ImportError:
    pass


# 获取摘要视图
def get_summary(text, count=150, suffix=u'', wrapper=u'p'):
    """A simpler implementation (vs `SummaryHTMLParser`).
    >>> text = u'<p>Hi guys:</p><p>This is a example using SummaryHTMLParser.</p>'
    >>> get_summary(text, 10, u'...')
    u'<p>Higuys:Thi...</p>'
    """
    assert(isinstance(text, unicode))
    summary = re.sub(r'<.*?>', u'', text) # key difference: use regex
    summary = u''.join(summary.split())[0:count]
    return u'<{0}>{1}{2}</{0}>'.format(wrapper, summary, suffix)


# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)
# app.config.from_envvar('FLASKR_SETTINGS', silent=True)

def connect_db():
    # conn = MySQLdb.connect(host='localhost', user='root',passwd='', db='flaskr', charset='utf8')
    # conn.select_db('flaskr');
    # return conn
    return MySQLdb.connect(MYSQL_HOST, MYSQL_USER, MYSQL_PASS, \
        MYSQL_DB, port = int(MYSQL_PORT), charset = 'utf8')

# def init_db():
#     pass
#     with closing(connect_db()) as db:
#        with app.open_resource('schema.sql', mode='r') as f:
#            db.cursor().executescript(f.read())
#        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'): g.db.close()
    # db = getattr(g, 'db', None)
    # if db is not None:
    #     db.close()
    # g.db.close()


@app.route('/',methods=['GET','POST'])
def show_entries():
    error = None
    p = request.args.get('page','0')    #get url query parameter 'page'
    p = string.atoi(p)  # convert string to int
    POST_PER_PAGE = 5
    
    cur = g.db.cursor()
    cur.execute('select COUNT(*) from entries;')
    totals = cur.fetchall()[0][0]
    g.db.commit()

    cur = g.db.cursor()
    cur.execute('select title,substr(text,1,175),id from entries order by id desc limit ' + 
        str(p) + ',' + str(POST_PER_PAGE) + ';')
    g.db.commit()
    entries = [dict(title=row[0], text=get_summary(row[1], 175, u'...'), id=row[2]) for row in cur.fetchall()]


    if request.method == 'POST':
        pagenumber = int(request.form['pagenumber'])
        if pagenumber < 0 or pagenumber > totals:
            error = 'Pagenumber out of range'
        p = (pagenumber - 1) * POST_PER_PAGE

    if p - POST_PER_PAGE < 0:
        p = 0
    elif p + POST_PER_PAGE > totals:
        p = int(math.floor(totals / float(POST_PER_PAGE)) * POST_PER_PAGE )
    
    pagetotal = []
    pagetotal.append(p)
    pagetotal.append(int(math.floor(totals / float(POST_PER_PAGE)) * POST_PER_PAGE ))
    pagetotal.append(totals)

    pages = []
    pagesize = int( math.ceil(totals / float(POST_PER_PAGE)) )
    for i in range(pagesize):
        pages.append(i)
    return render_template('show_entries.html', entries=entries, pagetotal=pagetotal, pages=pages, error=error)


@app.route('/add', methods=['GET','POST'])
def add_entry():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if not session.get('logged_in'):
            abort(401)
        cur = g.db.cursor()
        cur.execute('insert into entries (title, text) values (%s, %s)',
                     [request.form['title'], request.form['text']])
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))
    else:
        return render_template('show_addPage.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == '' or password == '':
            error = 'Username or password can not be empty!'
            return render_template('login.html', error=error)

        cur = g.db.cursor()
        # cur.execute('select * from users where username = (%s) and password = (%s);',
        #     [username, password] )
        cur.execute("select * from users where username = '%s' and password = '%s';" % (username, password) )
        g.db.commit()
        res = cur.fetchall()
        if(cur.rowcount == 0):
            error = 'login info incorrect'
            return render_template('login.html', error=error)
        else:
            flash('Welcome, ' + str(res[0][0]) + '!')
            session['logged_in'] = True
            return redirect(url_for('show_admin'))
    else:
        return render_template('login.html', error=error)


@app.route('/register',methods=['GET','POST'])
def register():
    error = None
    if request.method == 'GET':
        return render_template('register.html', error=error)
    elif request.method == 'POST':
        cur = g.db.cursor()
        cur.execute('insert into users (username, password) values (%s, %s)',
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
    cur = g.db.cursor()
    cur.execute('select title,text from entries where id = (%s);', [articleId])
    g.db.commit()
    resultRow = cur.fetchall()[0]
    article = dict(title=resultRow[0], text=resultRow[1])
    return render_template('show_article.html', article=article)


@app.route('/admin')
def show_admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    p = request.args.get('page','0')    #get url query parameter 'page'
    p = string.atoi(p)  # convert string to int
    POST_PER_PAGE = 20

    cur = g.db.cursor()
    cur.execute('select COUNT(*) from entries;')
    totals = cur.fetchall()[0][0]
    g.db.commit()


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

    cur = g.db.cursor()
    cur.execute('select id,title from entries order by id desc limit ' + 
        str(p) + ',' + str(POST_PER_PAGE) + ';')
    g.db.commit()
    articles = [dict(id=row[0], title=row[1]) for row in cur.fetchall()]

    return render_template("show_admin.html", articles=articles, pages=pages, pagetotal=pagetotal)
    

@app.route('/edit', methods=['GET','POST'])
def edit():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    articleId = int(request.args.get('id', '0'))
    if request.method == 'POST':
        articleTitle = request.form['title'].replace("'","\\'")
        articleText = request.form['text'].replace("'","\\'")   # 单引号转义处理        
        cur = g.db.cursor()
        cur.execute(u'''update entries set title = '%s', text = '%s' where id = '%s';''' % (articleTitle,articleText,articleId))
        g.db.commit()
        flash('\"' + articleTitle + '\" edit successfully!')
        return redirect(url_for('show_admin'))
        # return redirect(url_for('edit') + '?id=' + str(articleId) )
    else:
        cur = g.db.cursor()
        cur.execute('select title,text,id from entries where id = (%s);', [articleId])
        g.db.commit()
        resultRow = cur.fetchall()[0]
        article = dict(title=resultRow[0], text=resultRow[1], id=resultRow[2])
        return render_template('show_editPage.html', article=article)


@app.route('/delete', methods=['GET','POST'])
def delete():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    else:
        error = None
        articleId = int(request.args.get('id', '0'))
        cur = g.db.cursor()
        cur.execute('delete from entries where id = (%s)', [articleId])
        g.db.commit()
        if cur.rowcount != 0:
            flash('Delete article which id = %s successfully!' % (articleId) )
        else:
            error = 'Delete error'
        return redirect(url_for('show_admin'))

@app.route('/about')
def showABout():
    pass


@app.errorhandler(404) 
def page_not_found(error): 
    return render_template('page_not_found.html')


if __name__ == '__main__':
    app.run()



