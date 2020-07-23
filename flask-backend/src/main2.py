from flask import Blueprint
from flask import Flask, request, jsonify, Response
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson import json_util 
from bson.objectid import ObjectId

from .extensions import client

main2 = Blueprint('main2', __name__)


dacot = client.dacot

@main2.route('/dsadsa')
def index():
    return '<h1>DACoT 2 22222<h1>'

@main2.route('/users2',methods=['POST'])
def create_user():
    #id = db.insert({
    #    'id': request.json['name']
    #    'etc': request.json['etc']
    # })
    # Receiving data
    username = request.json['username']
    password = request.json['password']
    email = request.json['email']

    if username and email and password:
        hashed_password = generate_password_hash(password)
        id = dacot.users.insert(
            {'username':username, 'email':email, 'password': hashed_password}
        )
        response = {
            'id': str(id),
            'username': username,
            'password': hashed_password,
            'email': email
        }
        return response      
    else:
        return not_found()

    return {'message': 'received'}

@main2.route('/users2', methods=['GET'])
def get_users():
    users = dacot.users.find()
    response = json_util.dumps(users)
    return Response(response, mimetype='application/json')

@main2.route('/users2/<id>', methods=['GET'])
def get_user(id):
    user = dacot.users.find_one({'_id': ObjectId(id)})
    response = json_util.dumps(user)
    return Response(response, mimetype="application/json")

@main2.route('/users2/<id>', methods=['DELETE'])
def delete_user(id):
    dacot.users.delete_one({'_id': ObjectId(id)})
    response = jsonify({'message': 'User ' + id + ' was Deleted successfully'})
    return response

@main2.route('/users2/<id>', methods=['PUT'])
def update_user(id):
    username = request.json['username']
    email = request.json['email']
    password = request.json['password']

    if username and email and password:
        hashed_password = generate_password_hash(password)
        dacot.users.update_one({'_id': ObjectId(id)}, {'$set': {
            'username': username,
            'password': hashed_password,
            'email': email
        }})
        response = jsonify({'message': 'User ' + id + 'was updated successfully'})
        return response

@main2.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource not found: ' + request.url,
        'status': 404
    })
    response.status_code = 404
    return response
