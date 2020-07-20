from flask import Blueprint
from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util 
from bson.objectid import ObjectId
from pymongo import MongoClient


from .extensions import mongo
from .extensions import db

def confirm_form():
    if True:
        return True
    else:
        return False

def check_junction():
    return True

dacot = db.dacot
junctions_c = db.junctions

junction = Blueprint('junction', __name__)

#cambiar users a junctions
@junction.route('/')
def index():
    print(db.node)
    print(db)
    #response = json_util.dumps(status)
    #return Response(response, mimetype='application/json')
    return '<h1>DACoT<h1>'

@junction.route('/junction',methods=['POST'])
def create_junction():
    #id = db.insert({
    #    'id': request.json['name']
    #    'etc': request.json['etc']
    # })
    # Receiving data
    #test = request.json['plans']
    #print(test)
    ##password = request.json['password']
    ##email = request.json['email']

    if True:
        db.junctions_c.insert({
            'fver': '0.1',
            '_id': 'J001332',
            'meta': {
                'ver': 4,
                'date': '09/2019',
                'ctrl': 'A4F',
                'addr': 'LUIS THAYER OJEDA - PROVIDENCIA -  NVA PROVIDENCIA',
                'lat': -33.4187140,
                'lon': -70.6027238,
                'img': 'https://dacot.uoct.cl/diagrams/J01331'
            },
            'stages': {
                'A': 'VEH',
                'B': 'PEAT',
                'C': 'VEH',
                'D': 'PEAT',
                'E': 'VEH',
                'F': 'PEAT'
            },
            'phases': {
                '1': [['A', 'C', 'D'], 8],
                '2': [['A', 'B', 'D'], 8],
                '3': [['E', 'F'], 8]
            },
            'sequence': [1, 2, 3],
            'intergreens': {
                'A': [['E', 'F'], 4],
                'B': [['C', 'E'], 9],
                'C': [['B', 'E', 'F'], 4],
                'D': [['E'], 9],
                'E': [['A', 'B', 'C', 'D'], 4],
                'F': [['A', 'C'], 14]
            },
            'plans': {
                '3': {
                    'cycle': 110,
                    'phase_start': {'1': 82, '2': 6, '3': 30},
                    'system_start': {'1': 72, '2': 6, '3': 25},
                    'green_start': {'1': 86, '2': 10, '3': 34},
                    'vehicle_green': {'1': 30, '2': 20, '3': 48},
                    'pedestrian_green': {'1': 30, '2': 15, '3': 38},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                },
                '4': {
                    'cycle': 120,
                    'phase_start': {'1': 59, '2': 94, '3': 118},
                    'system_start': {'1': 49, '2': 94, '3': 113},
                    'green_start': {'1': 63, '2': 98, '3': 2},
                    'vehicle_green': {'1': 31, '2': 20, '3': 57},
                    'pedestrian_green': {'1': 31, '2': 15, '3': 47},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                },
                '5': {
                    'cycle': 90,
                    'phase_start': {'1': 83, '2': 21, '3': 41},
                    'system_start': {'1': 73, '2': 21, '3': 36},
                    'green_start': {'1': 87, '2': 25, '3': 45},
                    'vehicle_green': {'1': 24, '2': 16, '3': 38},
                    'pedestrian_green': {'1': 24, '2': 11, '3': 28},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                },
                '6': {
                    'cycle': 72,
                    'phase_start': {'1': 11, '2': 21, '3': 59},
                    'system_start': {'1': 1, '2': 21, '3': 54},
                    'green_start': {'1': 15, '2': 25, '3': 63},
                    'vehicle_green': {'1': 6, '2': 34, '3': 20},
                    'pedestrian_green': {'1': 6, '2': 29, '3': 10},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                },
                '8': {
                    'cycle': 120,
                    'phase_start': {'1': 23, '2': 66, '3': 90},
                    'system_start': {'1': 13, '2': 66, '3': 85},
                    'green_start': {'1': 27, '2': 70, '3': 94},
                    'vehicle_green': {'1': 39, '2': 20, '3': 49},
                    'pedestrian_green': {'1': 39, '2': 15, '3': 39},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                },
                '28': {
                    'cycle': 120,
                    'phase_start': {'1': 23, '2': 66, '3': 90},
                    'system_start': {'1': 13, '2': 66, '3': 85},
                    'green_start': {'1': 27, '2': 70, '3': 94},
                    'vehicle_green': {'1': 39, '2': 20, '3': 49},
                    'pedestrian_green': {'1': 39, '2': 15, '3': 39},
                    'vehicle_intergreen': {'3': [1, 4], '1': [2, 4], '2': [3, 4]},
                    'pedestrian_intergreen': {'3': [1, 14], '1': [2, 4], '2': [3, 9]}
                }
            },
            'program': {
                'L': [
                    ['00:01', 'S'],
                    ['00:01', '6'],
                    ['07:00', 'XS'],
                    ['00:00', '28'],
                    ['07:30', '28'],
                    ['10:00', 'S'],
                    ['10:00', '3'],
                    ['12:00', '8'],
                    ['14:30', '3'],
                    ['17:00', 'XS'],
                    ['17:00', '4'],
                    ['20:30', 'S'],
                    ['21:00', '5'],
                    ['22:00', '6']
                ],
                'V': [
                    ['00:01', 'S'],
                    ['00:01', '6'],
                    ['07:00', 'XS'],
                    ['00:00', '28'],
                    ['07:30', '28'],
                    ['10:00', 'S'],
                    ['10:00', '3'],
                    ['12:00', '8'],
                    ['14:30', '3'],
                    ['17:00', 'XS'],
                    ['17:00', '4'],
                    ['20:30', 'S'],
                    ['21:00', '5'],
                    ['22:00', '6']
                ],
                'S': [
                    ['00:01', 'S'],
                    ['00:01', '6'],
                    ['10:00', '5'],
                    ['14:00', '6']
                ],
                'D': [
                    ['00:01', 'S'],
                    ['00:01', '6'],
                    ['10:00', '5'],
                    ['14:00', '6']
                ]
            }
        }
        )

      #  id = mongo.db.junctions.insert(
       #     {'username':username, 'email':email, 'password': "das"}
       # )
        #response = {
         #   'id': str(id),
          #  'username': username,
           # 'password': "ads",
            #'email': email
        #}
        return {'message': 'received'}   
    else:
        return not_found()

    return {'message': 'received'}

@junction.route('/junction', methods=['GET'])
def get_junctions():
    junctions = db.junctions_c.find()
    response = json_util.dumps(junctions)
    return Response(response, mimetype='application/json')

@junction.route('/junction/<id>', methods=['GET'])
def get_junction(id):
    junction = db.junctions_c.find_one({'_id': id})
    response = json_util.dumps(junction)
    return Response(response, mimetype="application/json")

@junction.route('/junction/<id>', methods=['DELETE'])
def delete_junction(id):
    db.junctions_c.delete_one({'_id': id})
    response = jsonify({'message': 'Junction ' + id + ' was Deleted successfully'})
    return response

@junction.route('/junction/<id>', methods=['PUT'])
def update_junction(id):
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if check_junction():
        hashed_password = generate_password_hash(password)
        mongo.db.junctions.update_one({'_id': id}, {'$set': {
            'username': username,
            'password': hashed_password,
            'email': email
        }})
        response = jsonify({'message': 'Junction ' + id + 'was updated successfully'})
        return response

@junction.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response
