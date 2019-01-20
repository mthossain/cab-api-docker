import flask
from flask import request, jsonify, Flask, render_template, url_for, redirect
from flask_caching import Cache
import mysql.connector


def ignore_cache(parameters):
    cache_param = parameters.get('cache')

    if cache_param and cache_param.lower() == 'false':
        return True
    else:
        return False

app = flask.Flask(__name__, template_folder='templates')
app.config["DEBUG"] = True

#Cache setup
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

config = {
    'user': 'root',
    'password': 'root',
    'host': 'db',
    'port': '3306',
    'database': 'ny_cab_data'
}


#Home page
@app.route('/')
def home():
    return render_template('home.html')

#Handle form request
@app.route('/', methods=['POST'])
def form_handler():
    medallion = request.form['medallion']
    date = request.form['date']
    output = request.form['output']
    source = request.form['source']

    medallion = medallion.replace(' ', '')
    processed_link = '/api/v1/trips?medallion='

    if ',' in medallion:
        for meds in medallion.split(','):
            processed_link += meds + '&medallion='
        processed_link = processed_link[:-11]
    else:
        processed_link += medallion

    if date:
        processed_link += '&date='+date

    if output == 'json':
        processed_link += '&output=json'

    if source == 'no_cache':
        processed_link += '&cache=false'

    return redirect(processed_link, code=302)


#Error page handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html')

#Clear cache function for the button
@app.route("/clear_cache/", methods=['POST'])
def clear_cache():
    cache.clear()
    return redirect(url_for('home'))

#the main api
@app.route('/api/v1/trips', methods=['GET'])
@cache.cached(timeout=0, query_string=True, unless=lambda: ignore_cache(request.args))
def api():
    # Open database connection
    mydb = mysql.connector.connect(**config)
    #Parsing parameters
    parameters = request.args
    medallion = parameters.getlist('medallion')
    date = parameters.get('date')
    output = parameters.get('output')

    #Basic query
    query = "SELECT medallion, COUNT(medallion) FROM cab_trip_data WHERE medallion IN"
    #List for prepared statements
    args = []

    #If medallion parameter is provided
    if medallion:
        query += ' ('
        for med in medallion:
            query += '%s, '
            args.append(med)
        query = query[:-2]
        query += ')'
    #If date parameter is provided
    if date:
        #using range instead of date() function because date() function is very slow comapred to this approach
        query += ' AND (pickup_datetime >= %s and pickup_datetime <= %s)'
        date_new_start = date + ' 00:00:00'
        date_new_end = date + ' 23:59:59'
        args.append(date_new_start)
        args.append(date_new_end)
    query += ' GROUP BY medallion'

    mycursor = mydb.cursor(prepared=True)
    mycursor.execute(query, args)
    result = mycursor.fetchall()

    #If user asks for JSON output
    if output and output == 'json':
        final_return = []

        if date:
            for row in result:
                final_return.append({'medallion': row[0].decode('utf-8'), 'date': date, 'trips': row[1]})
        else:
            for row in result:
                final_return.append({'medallion': row[0].decode('utf-8'), 'trips': row[1]})

        return jsonify(final_return)
    #For default TEXT output
    else:
        final_return = ''
        if date:
            for row in result:
                final_return += 'Medallion: ' + str(row[0].decode('utf-8')) + ' => Date: ' + str(date) + ' => No of Trips: ' + str(row[1]) + '<br/> '
        else:
            for row in result:
                final_return += 'Medallion: ' + str(row[0].decode('utf-8')) + ' => No of Trips: ' + str(row[1]) + '<br/> '

        return final_return

app.run(host='0.0.0.0')
