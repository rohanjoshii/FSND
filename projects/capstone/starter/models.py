import os
from sqlalchemy import func, Column, String, Integer, Date, create_engine
from flask_sqlalchemy import SQLAlchemy
import json

db = SQLAlchemy()

def setup_db(app):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.app = app
    db.init_app(app)

actorsmovies = db.Table(
    'ActorsMovies',
    db.Column('movie_id', db.Integer, db.ForeignKey('movie.id')),
    db.Column('actor_id', db.Integer, db.ForeignKey('actor.id'))
)

class Movie(db.Model):
    __tablename__ = 'movie'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    release_date = Column(Date, nullable=False)

    def __init__(self, title, release_date):
      self.title = title
      self.release_date = release_date

    def insert(self):
      db.session.add(self)
      db.session.commit()

    def update(self):
      db.session.commit()

    def delete(self):
      db.session.delete(self)
      db.session.commit()

    def format_wo_actors(self):
      return {
        'id': self.id,
        'title': self.title,
        'release_date': self.release_date
      }

    def format(self):
      return {
        'id': self.id,
        'title': self.title,
        'release_date': self.release_date,
        'actors': [actor.format() for actor in self.actors]
      }

class Actor(db.Model):
    __tablename__ = 'actor'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)
    movies = db.relationship('Movie', secondary=actorsmovies, backref=db.backref('actors', lazy='True'))


    def __init__(self, name, age, gender):
      self.name = name
      self.age = age
      self.gender = gender

    def insert(self):
      db.session.add(self)
      db.session.commit()

    def update(self):
      db.session.commit()

    def delete(self):
      db.session.delete(self)
      db.session.commit()

    def format(self):
      return {
        'id': self.id,
        'name': self.name,
        'age': self.age,
        'gender': self.gender,
        'movies': [movie.format_wo_actors() for movies in self.movies]
      }
