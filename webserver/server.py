#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)

# XXX: The Database URI should be in the format of:
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ashish.maheshwari"
DB_PASSWORD = ""

# DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"
DB_SERVER = "127.0.0.1"

DATABASEURI = "postgresql://" + DB_USER + ":" + DB_PASSWORD + "@" + DB_SERVER + "/w4111"

#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)

# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


@app.before_request
def before_request():
    """
    This function is run at the beginning of every web request
    (every time you enter an address in the web browser).
    We use it to setup a database connection that can be used throughout the request

    The variable g is globally accessible
    """
    try:
        g.conn = engine.connect()
    except:
        print "uh oh, problem connecting to database"
        import traceback;
        traceback.print_exc()
        g.conn = None


@app.teardown_request
def teardown_request(exception):
    """
    At the end of the web request, this makes sure to close the database connection.
    If you don't the database could run out of memory!
    """
    try:
        g.conn.close()
    except Exception as e:
        pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
    """
    request is a special object that Flask provides to access web request information:

    request.method:   "GET" or "POST"
    request.form:     if the browser submitted a form, this contains the data in the form
    request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

    See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
    """

    # DEBUG: this is debugging code to see what request looks like
    print request.args

    #
    # example of a database query
    #
    cursor = g.conn.execute("SELECT name FROM test")
    names = []
    for result in cursor:
        names.append(result['name'])  # can also be accessed using result[0]
    cursor.close()

    #
    # Flask uses Jinja templates, which is an extension to HTML where you can
    # pass data to a template and dynamically generate HTML based on the data
    # (you can think of it as simple PHP)
    # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
    #
    # You can see an example template in templates/index.html
    #
    # context are the variables that are passed to the template.
    # for example, "data" key in the context variable defined below will be
    # accessible as a variable in index.html:
    #
    #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
    #     <div>{{data}}</div>
    #
    #     # creates a <div> tag for each element in data
    #     # will print:
    #     #
    #     #   <div>grace hopper</div>
    #     #   <div>alan turing</div>
    #     #   <div>ada lovelace</div>
    #     #
    #     {% for n in data %}
    #     <div>{{n}}</div>
    #     {% endfor %}
    #
    context = dict(data=names)

    #
    # render_template looks in the templates/ folder for files.
    # for example, the below file reads template/index.html
    #
    return render_template("index.html", **context)


#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
# @app.route('/another')
# def another():
#     return render_template("anotherfile.html")


# Example of adding new data to the database
# @app.route('/add', methods=['POST'])
# def add():
#     name = request.form['name']
#     # print name
#     cmd = 'INSERT INTO test(name) VALUES (:name1), (:name2)'
#     g.conn.execute(text(cmd), name1=name, name2=name)
#     return redirect('/')


@app.route('/users')
def users():
    cmd = ''' SELECT * FROM users '''
    cur = g.conn.execute(text(cmd))
    users = []
    for row in cur:
        users.append(row)
    context = dict(data=users, cols=cur.keys())
    return render_template("users.html", **context)


@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    status = request.form['status']
    cmd = ''' INSERT INTO users (name, email, status) VALUES (:name, :email, :status) RETURNING u_id '''
    try:
        cur = g.conn.execute(text(cmd), name=name, email=email, status=status)
    except Exception as e:
        print e
    # u_id = cur.fetchone()[0]
    # print "user added with id: ", u_id
    return redirect('/')


@app.route('/new_presentation')
def new_presentation():
    return render_template("new_presentation.html")


@app.route('/add_presentation', methods=['POST'])
def add_presentation():
    # print "new presentation function reached..."
    pr_name = request.form['pr_name']
    pr_desc = request.form['pr_desc']

    cmd = ''' INSERT INTO presentation (pr_name, pr_description) VALUES (:pr_name, :pr_description) RETURNING pr_id '''
    try:
        cur = g.conn.execute(text(cmd), pr_name=pr_name, pr_description=pr_desc)
    except Exception as e:
        print e
    # pr_id = cur.fetchone()[0]
    # print "presentation inserted with id: ", pr_id
    return redirect('/')


@app.route('/add_owner', methods=['POST'])
def add_owner():
    pr_id = request.form['pr_id']
    u_id = request.form['u_id']

    cmd = ''' INSERT INTO presentation_owner (u_id, pr_id) VALUES (:u_id, :pr_id) '''
    try:
        cur = g.conn.execute(text(cmd), u_id=u_id, pr_id=pr_id)
    except Exception as e:
        print e
    return redirect('/')


@app.route('/add_participant', methods=['POST'])
def add_participant():
    pr_id = request.form['pr_id']
    u_id = request.form['u_id']

    cmd = ''' INSERT INTO presentation_participant (u_id, pr_id) VALUES (:u_id, :pr_id) '''
    try:
        cur = g.conn.execute(text(cmd), u_id=u_id, pr_id=pr_id)
    except Exception as e:
        print e
    return redirect('/')


# @app.route('/show_presentations')
# def show_presentations():
#     return render_template("show_presentations.html")


@app.route('/show_presentations')
def show_presentations():
    cmd = ''' SELECT * FROM presentation '''
    cur = g.conn.execute(text(cmd))
    pr_data = []
    for row in cur:
        pr_data.append(row)
    context = dict(data=pr_data, cols=cur.keys())
    return render_template("show_presentations.html", **context)


@app.route('/fetch_pr_polls', methods=['POST'])
def fetch_pr_polls():
    pr_id = request.form['pr_id']
    cmd = ''' SELECT * FROM poll WHERE pr_id = :pr_id '''
    try:
        cur = g.conn.execute(text(cmd), pr_id=pr_id)
    except Exception as e:
        print e
        return redirect('/')
    polls = []
    for row in cur:
        polls.append(row)
    context = dict(pr_data=polls, pr_cols=cur.keys())
    return render_template("show_presentations.html", **context)


@app.route('/new_poll')
def new_poll():
    return render_template("new_poll.html")


@app.route('/add_poll', methods=['POST'])
def add_poll():
    # print "new poll function reached..."
    question = request.form['question']
    presentation = request.form['presentation']
    type = request.form['type']
    option1 = request.form['option1']
    option2 = request.form['option2']
    option3 = request.form['option3']
    option4 = request.form['option4']
    options = [option1, option2, option3, option4]

    if len(question) == 0:
        print "Error: Question field was left blank. Poll not added."
        return redirect('/')

    cmd = ''' SELECT pr_id FROM presentation WHERE pr_name = :name '''
    cur = g.conn.execute(text(cmd), name=presentation)
    presentation_id = -1
    for row in cur:
        presentation_id = row[0]
    # print presentation_id
    if presentation_id == -1:
        print "Error: no presentation found with name:", presentation
        return redirect('/')

    cmd = ''' INSERT INTO poll (pr_id, poll_question, poll_type) VALUES (:pr_id, :poll_question, :poll_type) RETURNING poll_id '''
    try:
        cur = g.conn.execute(text(cmd), pr_id=presentation_id, poll_question=question, poll_type=type)
    except Exception as e:
        print e
        return redirect('/')
    poll_id = cur.fetchone()[0]
    print "poll inserted with id: ", poll_id
    for i, option in zip(range(len(options)), options):
        add_poll_option(poll_id, i+1, option)
    return redirect('/')


def add_poll_option(poll_id, option_id, option_desc):
    # print "add_poll_option"
    # print "poll_id type: ", type(poll_id)
    # print "option_id type: ", type(option_id)
    # print "option_desc type: ", type(option_desc)
    cmd = ''' INSERT INTO poll_options (poll_id, option_id, option_desc) VALUES (:poll_id, :option_id, :option_desc) '''
    cur = g.conn.execute(text(cmd), poll_id=int(poll_id), option_id=int(option_id), option_desc=option_desc)


@app.route('/vote')
def vote():
    cmd = ''' SELECT * FROM poll '''
    cur = g.conn.execute(text(cmd))
    polls = []
    for row in cur:
        polls.append(row)
    # print "\nall fetched polls: \n"
    # print polls
    context = dict(data=polls, cols=cur.keys()[:-3])
    return render_template("vote.html", **context)


@app.route('/fetch_poll_options', methods=['POST'])
def fetch_poll_options():
    poll_id = request.form['poll_id']
    cmd = ''' SELECT * FROM poll_options WHERE poll_id = :poll_id '''
    try:
        cur = g.conn.execute(text(cmd), poll_id=poll_id)
    except Exception as e:
        print e
        return redirect('/')
    poll_options = []
    for row in cur:
        poll_options.append(row)
    context = dict(options_data=poll_options, option_cols=cur.keys())
    return render_template("vote.html", **context)


@app.route('/vote_on_poll', methods=['POST'])
def vote_on_poll():
    poll_id = request.form['poll_id']
    u_id = request.form['u_id']
    option_id = request.form['option_id']

    cmd = ''' SELECT poll_type FROM poll WHERE poll_id = :poll_id '''
    cur = g.conn.execute(text(cmd), poll_id=poll_id)
    poll_type = cur.fetchone()[0]
    # print "\npoll type returned: ", poll_type

    if poll_type == 'scq':
        cmd = ''' INSERT INTO votes_scq (poll_id, u_id, option_id) VALUES (:poll_id, :u_id, :option_id) RETURNING poll_id '''
    else:
        cmd = ''' INSERT INTO votes_mcq (poll_id, u_id, option_id) VALUES (:poll_id, :u_id, :option_id) RETURNING poll_id '''
    try:
        cur = g.conn.execute(text(cmd), poll_id=poll_id, u_id=u_id, option_id=option_id)
    except Exception as e:
        print e
        return redirect('/')
    # print "poll_id returned after voting: ", cur.fetchone()[0]
    return redirect('/')


@app.route('/results')
def results():
    return render_template("results.html")


@app.route('/poll_results', methods=['POST'])
def poll_results():
    poll_id = request.form['poll_id']
    cmd = ''' SELECT poll_type FROM poll WHERE poll_id = :poll_id '''
    try:
        cur = g.conn.execute(text(cmd), poll_id=poll_id)
    except Exception as e:
        print e
        return redirect('/')
    poll_type = cur.fetchone()
    if poll_type is not None:
        poll_type = poll_type[0]

    if poll_type == 'scq':
        cmd = ''' SELECT * FROM votes_scq WHERE poll_id = :poll_id '''
    else:
        cmd = ''' SELECT * FROM votes_mcq WHERE poll_id = :poll_id '''
    try:
        cur = g.conn.execute(text(cmd), poll_id=poll_id)
    except Exception as e:
        print e
        return redirect('/')
    votes = []
    for row in cur:
        votes.append(row)
    context = dict(votes_data=votes, votes_cols=cur.keys())
    return render_template("results.html", **context)


@app.route('/stats')
def stats():
    cmd = ''' SELECT p.poll_question, o.option_desc, COUNT(*)
              FROM Poll p, Votes_Mcq v, Poll_Options o
              WHERE p.poll_type = 'mcq' AND p.poll_id = v.poll_id AND o.option_id = v.option_id AND o.poll_id = p.poll_id
              GROUP BY o.option_desc, p.poll_question, p.poll_id
              ORDER BY p.poll_id; '''
    try:
        cur = g.conn.execute(text(cmd))
    except Exception as e:
        print e
        return redirect('/')
    q1_data = []
    for row in cur:
        q1_data.append(row)
    q1_cols = cur.keys()

    cmd = ''' WITH optionids (opt_id) AS ( 
              SELECT pop.option_id FROM Poll_Options pop WHERE poll_id IN (
                SELECT p.poll_id FROM Poll p WHERE p.pr_id IN (
                  SELECT po.pr_id FROM Presentation_Owner po WHERE po.u_id = 1
                  )
                )
              )
              SELECT u.name, COUNT(*) FROM (
                SELECT poll_id, u_id FROM Votes_Scq WHERE option_id IN (
                  SELECT opt_id FROM optionids)
                  UNION
                  SELECT poll_id, u_id FROM Votes_Mcq WHERE option_id IN 
                  (SELECT opt_id FROM optionids)
                ) AS tmp, Users as u
                WHERE u.u_id = tmp.u_id
                GROUP BY u.name; '''
    try:
        cur = g.conn.execute(text(cmd))
    except Exception as e:
        print e
        return redirect('/')
    q2_data = []
    for row in cur:
        q2_data.append(row)
    q2_cols = cur.keys()

    cmd = ''' SELECT min(p.option_desc), max(p.option_desc), avg(p.option_desc::int) FROM VOTES_SCQ v, poll_options p where v.option_id in (
              SELECT po.option_id FROM poll_options po where poll_id = 9) and p.poll_id = v.poll_id and p.option_id = v.option_id; '''
    try:
        cur = g.conn.execute(text(cmd))
    except Exception as e:
        print e
        return redirect('/')
    q3_data = []
    for row in cur:
        q3_data.append(row)
    q3_cols = cur.keys()

    cmd = ''' SELECT name FROM Users WHERE email LIKE '%columbia%'; '''
    try:
        cur = g.conn.execute(text(cmd))
    except Exception as e:
        print e
        return redirect('/')
    q4_data = []
    for row in cur:
        q4_data.append(row)
    q4_cols = cur.keys()

    context = dict(q1_data=q1_data, q1_cols=q1_cols, q2_data=q2_data, q2_cols=q2_cols, q3_data=q3_data, q3_cols=q3_cols,
                   q4_data=q4_data, q4_cols=q4_cols)
    return render_template("stats.html", **context)


# @app.route('/login')
# def login():
#     abort(401)
#     this_is_never_executed()


if __name__ == "__main__":
    import click


    @click.command()
    @click.option('--debug', is_flag=True)
    @click.option('--threaded', is_flag=True)
    @click.argument('HOST', default='0.0.0.0')
    @click.argument('PORT', default=8111, type=int)
    def run(debug, threaded, host, port):
        """
        This function handles command line parameters.
        Run the server using

            python server.py

        Show the help text using

            python server.py --help

        """

        HOST, PORT = host, port
        print "running on %s:%d" % (HOST, PORT)
        app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


    run()
