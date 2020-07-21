import os
import dateutil.parser
import babel
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import setup_db, Movie, Actor
from auth import AuthError, requires_auth

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    app.debug = True
    CORS(app)
    setup_db(app)

    # db_drop_and_create_all()
    def format_datetime(value, format='medium'):
        date = dateutil.parser.parse(value)
        if format == 'full':
            format = "EEEE MMMM, d, y 'at' h:mma"
        elif format == 'medium':
            format = "EE MM, dd, y h:mma"
        return babel.dates.format_datetime(date, format)

        app.jinja_env.filters['datetime'] = format_datetime


    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/movies')
    @requires_auth('get:movies')
    def get_movies(jwt):

        try:
            movies = Movie.query.all()

            movies_format = [movie.format() for movie in movies]

            return jsonify({
                "success": True,
                "movies": movies_format
            })
        except:
            abort(404)


    @app.route('/actors')
    @requires_auth('get:actors')
    def get_actors(jwt):

        try:
            actors = Actor.query.all()

            actors_format = [actor.format() for actor in actors]

            return jsonify({
                "success": True,
                "actors": actors_format
            })
        except:
            abort(404)


    @app.route('/actors', methods=['POST'])
    @requires_auth('post:actors')
    def add_actor(jwt):

        body = request.get_json()
        print (body)
        if not ('name' in body and 'age' in body and 'gender' in body):
            abort(422)
        name = body.get('name')
        age = body.get('age')
        gender = body.get('gender')

        try:
            actor = Actor(name=name, age=age, gender=gender)
            actor.insert()

            return jsonify({
                "success": True,
                "actor": actor.format()
            })
        except Exception as e:
            print (e)
            abort(422)

    @app.route('/movies', methods=['POST'])
    @requires_auth('post:movies')
    def add_movie(jwt):

        body = request.get_json()
        print (body)
        if not ('title' in body and 'release_date' in body):
            abort(422)
        title = body.get('title')
        release_date = body.get('release_date')

        try:
            movie = Movie(title=title, release_date=release_date)
            movie.insert()

            return jsonify({
                "success": True,
                "movie": movie.format_wo_actors()
            })
        except Exception as e:
            print (e)
            abort(422)

    @app.route('/movies/<int:movie_id>', methods=['DELETE'])
    @requires_auth('delete:movies')
    def delete_movie(jwt, movie_id):

        movie = Movie.query.get(movie_id)

        if movie:
            try:
                movie.delete()
                return jsonify({
                    'success': True,
                    'delete': movie_id
                })
            except:
                abort(422)
        else:
            abort(404)

    @app.route('/actors/<int:actor_id>', methods=['DELETE'])
    @requires_auth('delete:actors')
    def delete_actor(jwt, actor_id):

        actor = Actor.query.get(actor_id)

        if actor:
            try:
                actor.delete()
                return jsonify({
                    'success': True,
                    'delete': actor_id
                })
            except:
                abort(422)
        else:
            abort(404)


    @app.route('/movies/<int:movie_id>', methods=['PATCH'])
    @requires_auth('patch:movies')
    def update_movie(movie_id, jwt):
        movie = Movie.query.get(movie_id)

        try:
            body = request.get_json()

            if ('title' not in body and 'release_date' not in body):
                abort(422)

            title = body.get('title')
            release_date = body.get('release_date')


            if title:
                movie.title = title

            if release_date:
                movie.release_date = release_date

            movie.update()

            return jsonify({
                'success': True,
                'updated': movie.format()
            })

        except:
            abort(422)


    @app.route('/actors/<int:actor_id>', methods=['PATCH'])
    @requires_auth('patch:actors')
    def update_actor(actor_id, jwt):
        actor = Actor.query.get(actor_id)

        try:
            body = request.get_json()

            if body is None:
                abort(422)

            name = body.get('name')
            age = body.get('age')
            gender = body.get('gender')


            if name:
                actor.title = name

            if age:
                actor.age = age

            if gender:
                actor.gender = gender

            actor.update()

            return jsonify({
                'success': True,
                'updated': actor.format()
            })

        except:
            abort(422)


    @app.errorhandler(AuthError)
    def unauthorized(error):
        return (
            jsonify({
                "success": False,
                "error": error.status_code,
                "message": error.error
            }),
            error.status_code,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(
            {
                'success': False,
                'error': 400,
                'message': 'Bad request'
            }
        ), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {
                'success': False,
                'error': 404,
                'message': 'Not found'
            }
        ), 404

    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify(
            {
                'success': False,
                'error': 422,
                'message': 'Unprocessable entity'
            }
        ), 422

    @app.errorhandler(500)
    def server_error(error):
        return (
            jsonify({
                "success": False,
                'error': 500,
                "message": "Server error"
            }),
            500,
        )

    return app

app = create_app()

if __name__ == '__main__':
    app.run()
