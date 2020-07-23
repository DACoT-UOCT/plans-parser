import os
from flask_pymongo import PyMongo
from pymongo import MongoClient

client = MongoClient(os.environ['MONGO_URI'])
