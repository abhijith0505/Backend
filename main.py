from flask import Flask,flash,render_template,redirect,url_for,jsonify,make_response,request,abort,g,flash
from helpers import *
import sqlite3
from contextlib import closing


app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = 'aBcDeFg1@3$5'

# configuration
DATABASE = '/tmp/tt.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def connect_db():
    return sqlite3.connect(DATABASE)

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html')

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html'), 500

@app.route("/")
def mainInit():
	return render_template('home.html')

@app.route("/loadDb")
def loadDb():
	init_db()
	getTwitterFeed()
	return render_template('home.html')



#---------------------API Section-----------------------------------------------------------------------------------

#Sample API HIT: curl -i http://localhost:5000/api/blrttweets
@app.route("/api/blrttweets", methods=['GET'])
def blrttweets():
	tweets = retrieveAllblrTweets()
	return jsonify({'tweets': tweets}), 201
#----------------------------------------------------------------------------------------------------------------------------------


#Required Json: {
#				"src":"mvit",
#				"srclat":"40.81381340000001",
#				"srclong":"-74.06693179999999",
#				"dest":"hebbal",
#				"destlat":"40.8145647",
#				"destlong":"-74.06878929999999",
#				"day":"thursday",
#				"time":"13:32:12"
#				}


#Sample API HIT: curl -i -H "Content-Type: application/json" -X POST -d '{"src":"mvit","srclat":"40.81381340000001","srclong":"-74.06693179999999","dest":"hebbal","destlat":"40.8145647","destlong":"-74.06878929999999","day":"thursday","time":"13:32:12"}' http://localhost:5000/api/route/traffic/now
@app.route("/api/route/traffic/now", methods = ['POST'])
def TrafficNow():
    if not request.json:
        abort(400)
    if "src" not in request.json:
    	abort(400)
    if "dest" not in request.json:
    	abort(400)	
    if "srclat" not in request.json:
    	abort(400)
    if "srclong" not in request.json:
    	abort(400)	
    if "destlat" not in request.json:
    	abort(400)
    if "destlong" not in request.json:
    	abort(400)	
    if "day" not in request.json:
    	abort(400)
    if "time" not in request.json:
    	abort(400)	
    
    #index '0'->lat ; '1'->long
    source = [request.json['srclat'],request.json['srclong'],request.json['src']]
    destination = [request.json['destlat'],request.json['destlong'],request.json['dest']]
    day = request.json['day']
    time = request.json['time']

    try:

        g.db.execute('insert into routes values (?, ?, ?, ?)',[source[2], destination[2], day, time])
        g.db.commit()

        g.db.execute('insert into coordinates values (?, ?, ?)',[source[2], source[0], source[1]])
        g.db.commit()

        g.db.execute('insert into coordinates values (?, ?, ?)',[destination[2], destination[0], destination[1]])
        g.db.commit()

    except sqlite3.IntegrityError:
        print "Could not add"

    #insertRouteIntoDb(source,destination,day,time)
    locations = insertRouteIntoDb(source,destination)

    trafficTweets = getTrafficTweetsForRoute(locations,day,time)

    return jsonify({"Under":"development","source":source[2],"destination":destination[2],"tweets":trafficTweets}), 201
#----------------------------------------------------------------------------------------------------------------------------------


#Required Json: {
#				"src":"mvit",
#				"srclat":"40.81381340000001",
#				"srclong":"-74.06693179999999",
#				"dest":"hebbal",
#				"destlat":"40.8145647",
#				"destlong":"-74.06878929999999"
#				}


#Sample API HIT: curl -i -H "Content-Type: application/json" -X POST -d '{"src":"mvit","srclat":"40.81381340000001","srclong":"-74.06693179999999","dest":"hebbal","destlat":"40.8145647","destlong":"-74.06878929999999"}' http://localhost:5000/api/route/traffic/alltime
@app.route("/api/route/traffic/alltime", methods = ['POST'])
def TrafficAllTime():
    if not request.json:
        abort(400)
    if "src" not in request.json:
    	abort(400)
    if "dest" not in request.json:
    	abort(400)	
    if "srclat" not in request.json:
    	abort(400)
    if "srclong" not in request.json:
    	abort(400)	
    if "destlat" not in request.json:
    	abort(400)
    if "destlong" not in request.json:
    	abort(400)	
    
    #index '0'->lat ; '1'->long
    source = [request.json['srclat'],request.json['srclong'],request.json['src']]
    destination = [request.json['destlat'],request.json['destlong'],request.json['dest']]

    locations = returnLocations(source,destination)
    trafficTweets = getTrafficTweetsForRouteAllTime(locations)

    return jsonify({"Under":"development","source":source[2],"destination":destination[2],"tweets":trafficTweets}), 201
#----------------------------------------------------------------------------------------------------------------------------------


#Required Json: {
#				"srclat":"40.81381340000001",
#				"srclong":"-74.06693179999999",
#				"destlat":"40.8145647",
#				"destlong":"-74.06878929999999",
#				}


#Sample API HIT: curl -i -H "Content-Type: application/json" -X POST -d '{"srclat":"40.81381340000001","srclong":"-74.06693179999999","destlat":"40.8145647","destlong":"-74.06878929999999"}' http://localhost:5000/api/checkpoints/locations
@app.route("/api/checkpoints/locations", methods = ['POST'])
def checkpointsLocations():
    if not request.json:
        abort(400)
    if "srclat" not in request.json:
    	abort(400)
    if "srclong" not in request.json:
    	abort(400)
    if "destlat" not in request.json:
    	abort(400)
    if "destlong" not in request.json:
    	abort(400)
    
    #index '0'->lat ; '1'->long
    source = [request.json['srclat'],request.json['srclong']]
    destination = [request.json['destlat'],request.json['destlong']]
    

    json_checkpoints = getCheckpoints(source,destination)
    locations = getCheckpointLocations(source,destination)

    return jsonify({"source_lat":source[0],"source_long":source[1],"destination_lat":destination[0],"destination_long":destination[1],"checkpoints-locations":locations}), 201

#Sample API HIT: curl -i -H "Content-Type: application/json" -X POST -d '{"srclat":"40.81381340000001","srclong":"-74.06693179999999","destlat":"40.8145647","destlong":"-74.06878929999999"}' http://localhost:5000/api/checkpoints/coordinates
@app.route("/api/checkpoints/coordinates", methods = ['POST'])
def checkpointsCoordinates():
    if not request.json:
        abort(400)
    if "srclat" not in request.json:
        abort(400)
    if "srclong" not in request.json:
        abort(400)
    if "destlat" not in request.json:
        abort(400)
    if "destlong" not in request.json:
        abort(400)
    
    #index '0'->lat ; '1'->long
    source = [request.json['srclat'],request.json['srclong']]
    destination = [request.json['destlat'],request.json['destlong']]
    
    json_checkpoints = getCheckpoints(source,destination)

    return jsonify({"source_lat":source[0],"source_long":source[1],"destination_lat":destination[0],"destination_long":destination[1],"checkpoints-coordinates":json_checkpoints}), 201


if __name__ == "__main__":
    app.run(debug = True)
