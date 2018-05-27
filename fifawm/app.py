#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#


from __future__ import print_function
from flask import Flask, render_template, request, Response, send_file
# from flask.ext.sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
import pandas as pd
import re
import os
from tournament.simulate_tournament import Tournament
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
#db = SQLAlchemy(app)
tourney = Tournament()

# Automatically tear down SQLAlchemy.
'''
@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()
'''

# Login required decorator.
'''
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return test(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap
'''
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def home():
    # filepath = os.path.join(os.getcwd(), 'static', 'data', 'schedule_fifa.csv')
    # df = pd.read_csv('~/hburg/hackaburg18datacollection/fifawm/static/data/schedule_fifa.csv')
    # df = pd.read_csv(filepath)
    group_winners, new_df, group_table_total = tourney.get_tournament_prediction()
    print(tourney.get_tournament_prediction())

    groupa = new_df.loc[new_df['group'] == 'A'].to_html(index=False)
    groupb = new_df.loc[new_df['group'] == 'B'].to_html(index=False)
    groupc = new_df.loc[new_df['group'] == 'C'].to_html(index=False)
    groupd = new_df.loc[new_df['group'] == 'D'].to_html(index=False)
    groupe = new_df.loc[new_df['group'] == 'E'].to_html(index=False)
    groupf = new_df.loc[new_df['group'] == 'F'].to_html(index=False)
    groupg = new_df.loc[new_df['group'] == 'G'].to_html(index=False)
    grouph = new_df.loc[new_df['group'] == 'H'].to_html(index=False)

    twod = group_winners.get("2D")
    print(twod)

    return render_template('pages/placeholder.home.html', groupa=groupa, groupb=groupb, groupc=groupc, groupd=groupd,
                           groupe=groupe, groupf=groupf, groupg=groupg, grouph=grouph, twod=twod)

@app.route('/get_tournament', methods=["GET"])
def get_tournament():
    tourney.get_tournament_prediction()


from flask import jsonify

@app.route('/get_tournament_statistics', methods=["GET"])
def get_tournament_statistics():
    #return jsonify(['2013-01,53', '2013-02,165'])
    """return send_file(os.path.join(os.getcwd(), 'templates', 'pages', 'bar-data.csv'),
                     mimetype='text/csv',
                     attachment_filename='bar-data.csv',
                     as_attachment=True)
    """
    with open(os.path.join(os.getcwd(), 'templates', 'pages', 'bar-data.csv')) as fp:
        csv = fp.read()
    #csv = '1,2,3\n4,5,6\n'
        return Response(
            csv,
            mimetype="text/csv",
            headers={"Content-disposition":
                    "attachment; filename=myplot.csv"})


@app.route('/about')
def about():
    return render_template('pages/placeholder.about.html')


@app.route('/login')
def login():
    form = LoginForm(request.form)
    return render_template('forms/login.html', form=form)


@app.route('/register')
def register():
    form = RegisterForm(request.form)
    return render_template('forms/register.html', form=form)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

# Error handlers.


@app.errorhandler(500)
def internal_error(error):
    #db_session.rollback()
    return render_template('errors/500.html'), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
