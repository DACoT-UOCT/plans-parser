from flask import Blueprint
from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util 
from bson.objectid import ObjectId

from .extensions import mongo
from .extensions import client

petitions = Blueprint('petitions', __name__)

dacot = client.dacot

@petitions.route('/petition',methods=['POST'])
def create_pettition():
    
    petition = 'Esta es una peticion'
    id = dacot.petitions.insert(
            {'petition': petition}
        )
    response = {
            'id': str(id),
            'petition': petition
        }
    return response  

@petitions.route('/petition', methods=['GET'])
def get_petitions():
    petitions = dacot.petitions.find()
    response = json_util.dumps(petitions)
    return Response(response, mimetype='application/json')

@petitions.route('/petition/<id>', methods=['GET'])
def get_petition(id):
    s_petition = dacot.petitions.find_one({'_id': ObjectId(id)})
    response = json_util.dumps(s_petition)
    return Response(response, mimetype="application/json")

@petitions.route('/petition/<id>', methods=['DELETE'])
def delete_petition(id):
    dacot.petitions.delete_one({'_id': ObjectId(id)})
    response = jsonify({'message': 'User ' + id + ' was Deleted successfully'})
    return response

@petitions.route('/petition/<id>', methods=['PUT'])
def update_petition(id):
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if username and email and password:
        hashed_password = generate_password_hash(password)
        mongo.db.users.update_one({'_id': ObjectId(id)}, {'$set': {
            'username': username,
            'password': hashed_password,
            'email': email
        }})
        response = jsonify({'message': 'User ' + id + 'was updated successfully'})
        return response

@petitions.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response
