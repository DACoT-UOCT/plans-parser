from flask import Blueprint
from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util 
from bson.objectid import ObjectId

from .extensions import client

intersection = Blueprint('intersection', __name__)


dacot = client.dacot

@intersection.route('/intersection',methods=['POST'])
def create_intersection():
    return {'message': 'received'}

#@intersection.route('/intersections2', methods=['GET'])
def get_intersections():
    intersections = dacot.intersections.find()
    response = json_util.dumps(intersections)
    return Response(response, mimetype='application/json')

@intersection.route('/intersection/<id>', methods=['GET'])
def get_intersection(id):
    intersection = dacot.intersections.find_one({'_id': id})
    junctions = []
    if intersection == 'null':
        return bad_request()
    k = 0
    for junction in intersection['junctions']:
        junctions.append(dacot.junction.find_one({'_id': junction['id']}) )
        junction['programacion'] = junctions[k]['plans']
        k+= 1

    preview= {
        "_id": id,
        "metadata": intersection['metadata'],
        "tabla_periodizaciones": junctions[0]['program'],
        "junctions": intersection['junctions'],
        "stages": intersection['stages'],
        "fases":intersection['fases'],
        "secuencias": intersection['secuencias'],
        "entreverdes": intersection['entreverdes'],
        "observaciones": intersection['observaciones'],
        "imagen_instalacion": intersection['imagen_instalacion']
        }

    response = json_util.dumps(preview)
    return Response(response, mimetype="application/json")

@intersection.route('/intersection/<id>', methods=['DELETE'])
def delete_intersection(id):
    dacot.intersections.delete_one({'_id': ObjectId(id)})
    response = jsonify({'message': 'intersection ' + id + ' was Deleted successfully'})
    return response

@intersection.route('/intersections2/<id>', methods=['PUT'])
def update_intersection(id):
        response = jsonify({'message': 'intersection ' + id + 'was updated successfully'})
        return response

@intersection.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response

@intersection.errorhandler(400)
def bad_request(error=None):
    response = jsonify({
        'message': 'Bad request: ' + request.url,
        'status': 400
    })
    response.status_code = 400
    return response