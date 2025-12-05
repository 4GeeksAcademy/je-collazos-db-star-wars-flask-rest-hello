
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
# Importamos TODOS los modelos que definimos en models.py
from models import db, User, People, Planet, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)


# RUTAS DE USUARIOS (USERS)
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    # Usamos list comprehension para serializar todos los usuarios
    results = [user.serialize() for user in users]
    return jsonify(results), 200

@app.route('/users', methods=['POST'])
def create_user():
    body = request.get_json()
    
    if not body.get('email') or not body.get('password'):
        return jsonify({"msg": "Email y Password son requeridos"}), 400

    new_user = User(
        email=body['email'],
        password=body['password'],
        first_name=body.get('first_name', ''), 
        last_name=body.get('last_name', ''),   
        is_active=True
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"msg": "Usuario creado exitosamente", "user": new_user.serialize()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": "Error creando usuario (posible email duplicado)", "error": str(e)}), 500


# RUTAS DE PLANETAS (PLANETS)

@app.route('/planets', methods=['GET'])
def get_planets():
    planets = Planet.query.all()
    results = [planet.serialize() for planet in planets]
    return jsonify(results), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"msg": "Planeta no encontrado"}), 404
    return jsonify(planet.serialize()), 200

@app.route('/planets', methods=['POST'])
def create_planet():
    body = request.get_json()
    new_planet = Planet(
        name=body['name'],
        climate=body.get('climate'),
        terrain=body.get('terrain'),
        population=body.get('population')
    )
    db.session.add(new_planet)
    db.session.commit()
    return jsonify({"msg": "Planeta creado", "planet": new_planet.serialize()}), 201

# RUTAS DE CHARACTERS

@app.route('/people', methods=['GET'])
def get_people():
    people = People.query.all()
    results = [person.serialize() for person in people]
    return jsonify(results), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_person(people_id):
    person = People.query.get(people_id)
    if not person:
        return jsonify({"msg": "Personaje no encontrado"}), 404
    return jsonify(person.serialize()), 200

@app.route('/people', methods=['POST'])
def create_person():
    body = request.get_json()
    new_person = People(
        name=body['name'],
        gender=body.get('gender'),
        hair_color=body.get('hair_color'),
        eye_color=body.get('eye_color')
    )
    db.session.add(new_person)
    db.session.commit()
    return jsonify({"msg": "Personaje creado", "person": new_person.serialize()}), 201

# RUTAS DE FAVORITOS (FAVORITES)

@app.route('/users/<int:user_id>/favorites', methods=['GET'])
def get_user_favorites(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    
    favorites = [fav.serialize() for fav in user.favorites]
    return jsonify(favorites), 200

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    body = request.get_json()
    user_id = body.get("user_id") 

    exists = Favorite.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if exists:
        return jsonify({"msg": "Este planeta ya es favorito"}), 400

    new_fav = Favorite(user_id=user_id, planet_id=planet_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Planeta añadido a favoritos"}), 201

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    body = request.get_json()
    user_id = body.get("user_id")

    exists = Favorite.query.filter_by(user_id=user_id, people_id=people_id).first()
    if exists:
        return jsonify({"msg": "Este personaje ya es favorito"}), 400

    new_fav = Favorite(user_id=user_id, people_id=people_id)
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"msg": "Personaje añadido a favoritos"}), 201