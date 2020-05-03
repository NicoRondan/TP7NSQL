from pymongo import MongoClient
import json

def connect_db():
    try:
        client = MongoClient(host='localhost', port=27017)
        db = client["superheroes"]
        return db
    except Exception as err:
        print("An exception occurred :", err)
    
def initialize(db):
    #Insertar archivos json contenidos en superheroes.json
    with open('superheroes.json', "r", encoding='utf-8') as file:
        data = json.load(file)
    try:
        db.heroes.drop()
        db.heroes.insert_many(data)
    except Exception as err:
        print("An exception occurred :", err)
    