from flask import Flask, render_template, request, redirect, url_for, jsonify, Response, flash
from bson import json_util
from bson.objectid import ObjectId
import requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from db import connect_db, initialize
import os 
import datetime
import re

app = Flask(__name__)

"""Declarar directorio de subida de imagenes"""
app.config['IMG_FOLDER'] = './static/img'

"""Api key """
app.config['API_KEY'] = '9221ace732f4c207a45d82a0d80f698e'

"""Clave necesaria para poder utilizar flash"""
app.secret_key = 'clave_secreta'

#Conexion a la bd
db = connect_db()

#Borrar coleccion
#db.heroes.drop()
#db.movies.drop()

#Checkear que haya datos en la bd
collist = db.list_collection_names()
if "heroes" not in collist:
    #cargar datos
    initialize(db) 


@app.route('/', methods=['GET'])
def get_heroes():
    #Obtener heroes de ambas casas
    data = db.heroes.find().sort('name')
    #Convertir BSON a JSON
    data = json_util.dumps(data)
    #json list
    data = json_util.loads(data)
    return render_template('home.html', data=data)  

@app.route('/movies', methods=['GET'])
def get_movies():
    #Obtener peliculas
    data = db.movies.find().sort('title')
    #Convertir BSON a JSON
    data = json_util.dumps(data)
    #json list
    data = json_util.loads(data)
    return render_template('home.html', data=data)  

@app.route('/marvel', methods=['GET'])
def get_heroes_marvel():
    #Obtener heroes de marvel
    data = db.heroes.find({"house": "MARVEL"}).sort('name')
    data = json_util.dumps(data)
    data = json_util.loads(data)
    return render_template('home.html', data=data)  

@app.route('/dc', methods=['GET'])
def get_heroes_dc():
    #Obtener heroes de dc
    data = db.heroes.find({"house": "DC"}).sort('name')
    data = json_util.dumps(data)
    data = json_util.loads(data)
    return render_template('home.html', data=data)  

@app.route('/add-hero', methods=['POST', 'GET'])
def add_hero():
    if request.method == 'GET':
        return render_template('add.html')
    else:
        #Recibiendo datos
        name = request.form.get('name')
        character = request.form.get('character')
        year = request.form.get('year')
        house = request.form.get('house')
        biography = request.form.get('biography')
        equipment = request.form.get('equipment')
        images = []
        
        # Guardar cada imagen en el servidor
        for file in request.files.getlist('images'):
            #Almacenar el nombre del archivo
            images.append(file.filename)
            file.save(os.path.join(app.config['IMG_FOLDER'], file.filename))   
                       
        if name and year and biography and house and images:
            
            if (character == None or character == '') and (equipment == None or equipment == ''):
                hero = {
                        "name": name,
                        "year": year,
                        "house": house,
                        "biography": biography,
                        "images": images,
                        "limit_images": len(images)
                    }
            elif (character == None or character == ''):
                hero = {
                        "name": name,
                        "year": year,
                        "house": house,
                        "biography": biography,
                        "equipment": equipment,
                        "images": images,
                        "limit_images": len(images)
                    }
            elif (equipment == None or equipment == ''):
                hero = {
                        "name": name,
                        "character": character,
                        "year": year,
                        "house": house,
                        "biography": biography,
                        "images": images,
                        "limit_images": len(images)
                    }
            else:
                hero = {
                        "name": name,
                        "character": character,
                        "year": year,
                        "house": house,
                        "biography": biography,
                        "equipment": equipment,
                        "images": images,
                        "limit_images": len(images)
                    }
            #Insertar objeto
            try:
                db.heroes.insert_one(hero)
                flash('Hero added successfully!')
                return redirect(url_for('get_heroes'))
            except Exception as err:
                print("An exception occurred :", err)
                flash('An error has occurred...')
                redirect('/add-hero')

@app.route('/add-movie', methods=['POST', 'GET'])
def add_movie():
    if request.method == 'GET':
        return render_template('add-movie.html')
    else:
        #Recibiendo datos
        movie = request.form.get('movie')
        url = 'https://api.themoviedb.org/3/search/movie/?api_key={}&query={}'.format(app.config['API_KEY'], movie)
        try:
            response = requests.get(url)
            results = response.json()['results']
            if results == []:
                flash('No se encontraron coincidencias...')
                return redirect(url_for('add_movie'))
            else:
                movie = results[0]
                poster_path = movie['poster_path']
                id = movie['id']
                #Comprobar que la pelicula no esté ya cargada en la bd
                exists = db.movies.find({'id': id})
                exists = json_util.dumps(exists)
                exists = json_util.loads(exists)
                if exists != []:
                    flash('Ups, movie already saved...')
                    return redirect('/add-movie')
                else:
                    url_cast = 'https://api.themoviedb.org/3/movie/{}/credits?api_key={}'.format(id, app.config['API_KEY'])
                    url_image = 'https://image.tmdb.org/t/p/w500/{}'.format(poster_path)
                    cast = requests.get(url_cast).json()['cast']
                    title = movie['title']
                    release_date = movie['release_date']
                    overview = movie['overview']
                    movie = {
                        'id': id,
                        'title': title,
                        'release_date': release_date,
                        'overview': overview,
                        'url_image': url_image,
                        'cast': cast
                    }
                    db.movies.insert_one(movie)
                    flash('Movie was added successfully!')
                    return redirect('/movies')
        except (ConnectionError, Timeout, TooManyRedirects) as error:
            print(error) 

@app.route('/delete/<id>', methods=['GET'])
def delete_hero(id):
    #Transformar el id (string) a un objectId
    try:
        db.heroes.delete_one({'_id': ObjectId(id)})
        flash('Hero deleted successfully!')
        return redirect(url_for('get_heroes'))
    except Exception as err:
        print("An exception occurred :", err)
        flash('An error has occurred...')
        return redirect('/hero/' + id)

@app.route('/update/<id>', methods=['GET', 'POST'])
def update_hero(id):
    #Obtener house e imagenes
    data = db.heroes.find_one({'_id': ObjectId(id)}, {'house': 1, 'images': 2, '_id': 0})
    #Recibiendo datos
    name = request.form.get('name')
    character = request.form.get('character')
    year = request.form.get('year')
    house = data['house']
    biography = request.form.get('biography')
    equipment = request.form.get('equipment')
    limit_images = int(request.form.get('limit_images'))
    images = data['images']
    
    if name and year and biography:
        if (character == None or character == '') and (equipment == None or equipment == ''):
            hero = {
                "name": name,
                "year": year,
                "house": house,
                "biography": biography,
                "images": images,
                "limit_images": limit_images
                }
        elif character == None or character == '':
             hero = {
                    "name": name,
                    "year": year,
                    "house": house,
                    "biography": biography,
                    "equipment": equipment,
                    "images": images,
                    "limit_images": limit_images
                }
        elif equipment == None or equipment == '':
            hero = {
                    "name": name,
                    "character": character,
                    "year": year,
                    "house": house,
                    "biography": biography,
                    "images": images,
                    "limit_images": limit_images
                }
        else:
            hero = {
                    "name": name,
                    "character": character,
                    "year": year,
                    "house": house,
                    "biography": biography,
                    "equipment": equipment,
                    "images": images,
                    "limit_images": limit_images
                }
        #Modificar heroe
        try:
            db.heroes.update_one({'_id': ObjectId(id)}, {'$set': hero }) 
            flash('Hero updated successfully!')
            return redirect('/hero/' + id)
        except Exception as err:
            print("An exception occurred :", err)
            flash('An error has occurred...')
            return redirect('/hero/' + id)
            
    
@app.route('/hero/<id>', methods=['GET'])
def get_hero(id):
    #Buscar en la bbdd
    hero = db.heroes.find_one({'_id': ObjectId(id)})
    #Convertir BSON a JSON
    data = json_util.dumps(hero)
    data = json_util.loads(data)
    #Arreglar un poco el texto de la biografia
    bio = data['biography'].lower()
    bio = bio.capitalize()
    #Truncar imagenes en base al limite que se le haya dado
    images = data['images']
    start = 0
    stop = data['limit_images']
    images = images[start:int(stop)]
    
    #Verificar si el heroe tiene un character name
    if data['character'] != '':
        #De ser así buscarlo en movies, teniendo en cuenta que esta el nombre del personaje y heroe juntos por un slash "/"
        result = db.movies.find({'cast.character': { '$in': [ re.compile(data['name'].strip(), re.IGNORECASE), re.compile(data['character'], re.IGNORECASE) ] } }, {'title': 1, '_id': 2})
    else:
        result = db.movies.find({'cast.character':{ '$in': [ re.compile(data['name'].strip(), re.IGNORECASE), re.compile(data['name'] + ' (voice)', re.IGNORECASE) ] }}, {'title': 1, '_id': 2})  
    #pasamos a lista para el front
    result = json_util.dumps(result)
    movies = json_util.loads(result)
    #print(movies)
    return render_template('detail.html', data=data, bio=bio, images=images, movies=movies) 

@app.route('/movie/<id>', methods=['GET'])
def get_movie(id):
    #Buscar en la bbdd
    movie = db.movies.find_one({'_id': ObjectId(id)})
    #Convertir BSON a JSON
    data = json_util.dumps(movie)
    data = json_util.loads(data)
    date = datetime.datetime.strptime(data['release_date'], "%Y-%m-%d").strftime("%Y")
    #Buscar heroes en el casting
    heroes = []
    for hero in data['cast']:
        if hero['character'].find('/') == -1:
            #Comprobar que el actor sólo hizo la voz del heroe (voice)
            if hero['character'].find('(') != -1:
                name = hero['character'].split('(')[0].strip()
            else:
                name = hero['character']
            result = db.heroes.find_one({'$or': [{'name':  re.compile(name, re.IGNORECASE)}]}, {'_id': 1})
            if result != None and result != []:    
                result = json_util.dumps(result)
                result = json_util.loads(result)
                temp = {'name': name, '_id': result['_id']}
                heroes.append(temp)
        else:
            #obtener nombre del personaje sin espacios en blanco
            character = hero['character'].split('/')[0].strip()
            #obtener nombre del heroe sin espacios en blanco
            name = hero['character'].split('/')[1].strip()
            
            print(name, character)
            #Buscar el heroe segun nombre del personaje o heroe
            result = db.heroes.find_one({'$or': [{'name': { '$in': [ re.compile(name, re.IGNORECASE), re.compile(character, re.IGNORECASE) ]}}, {'character':  { '$in': [ re.compile(name, re.IGNORECASE), re.compile(character, re.IGNORECASE) ]}} ]}, {'_id': 1})
            if result != None and result != []:
                result = json_util.dumps(result)
                result = json_util.loads(result)
                temp = {'name': name, '_id': result['_id']}
                #Añadirlo a la lista
                heroes.append(temp)
            
    return render_template('movie.html', data=data, date=date, heroes=heroes) 
    
    
#En caso de error de ruta
@app.errorhandler(404)
def not_found(error=None):
    response = jsonify({
        'message': 'Resource Not Found: ' + request.url,
        'status': 404 
    })
    response.status_code = 404
    return response


if __name__ == "__main__":
    app.run(host='localhost', port='5000', debug=True)