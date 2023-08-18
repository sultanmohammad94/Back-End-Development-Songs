from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))
app.config["MONGO_USERNAME"] = os.environ.get('MONGODB_USERNAME')
app.config["MONGO_PASSWORD"] = os.environ.get('MONGO_PASSWORD')
client = MongoClient(
    f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route('/health', methods = ['GET'])
def health():
    response = {"status": "OK"}
    return response

@app.route('/count', methods = ['GET'])
def count():
    response = jsonify({
        "count": db.songs.count_documents({})
    })
    response.status_code = 200
    return response

@app.route('/song', methods = ["GET"])
def song():
    songs = list(db.songs.find({}))
    for song in songs:
        song['_id'] = str(song['_id'])
    response = jsonify(json.loads(json_util.dumps(songs)))
    return response

@app.route('/song/<int:id>', methods = ["GET"])
def get_song_by_id(id):
    song = (db.songs.find_one({"id":id}))
    if song:
        song['_id'] = str(song['_id'])
        response = jsonify(song)
    else:
        response = {
            "message": "song with id not found"
        }
    return response

@app.route('/song', methods = ["POST"])
def create_song():
    data = request.get_json()
    if data.get("id"):
        song = db.songs.find_one({"id": data.get("id")})
        if song:
            return jsonify({"Message":f"song with id {song['id']} already present"}), 302
        else:
            song = db.songs.insert_one(data)
            inserted_id = str(song.inserted_id)
            return jsonify({"inserted id": {"$oid": inserted_id}}), 201
    return jsonify({"message": "song with id not found"}), 404