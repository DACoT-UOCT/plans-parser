from flask_pymongo import PyMongo
from pymongo import MongoClient

mongo = PyMongo()



db = MongoClient('mongodb://54.224.251.49:30001,54.224.251.49:30002,54.224.251.49:30003/?replicaSet=rsuoct')