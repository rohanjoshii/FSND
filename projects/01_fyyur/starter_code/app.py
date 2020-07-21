#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from sqlalchemy import func
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    genres = db.Column(db.ARRAY(db.String()))
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String()))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(1000))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.name}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues = Venue.query.order_by(Venue.state, Venue.city).all()
  data = []
  current_location = [None, None]
  for venue in venues:
      upcoming_shows = [show for show in venue.shows if show.start_time>datetime.now()]
      venue_data = {
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(upcoming_shows)
      }
      if current_location[0] == venue.city and current_location[1] == venue.state:
          current_area = len(data) - 1
          data[current_area]['venues'].append(venue_data)
      else:
          data.append({
          "city": venue.city,
          "state": venue.state,
          "venues": [venue_data]
          })
          current_location = [venue.city, venue.state]

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():

  search_term = request.form.get('search_term', '')
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []

  for venue in venues:
      upcoming_shows = [show for show in venue.shows if show.start_time>datetime.now()]
      data.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_shows': len(upcoming_shows)
      })
  response={
    "count": len(venues),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in past_shows_query:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  for show in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })

  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  print(venue.genres)
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    error = False
    body = {}
    try:
        json_request = request.form
        print (json_request)
        print (request)
        name = json_request['name']
        state = json_request['state']
        city = json_request['city']
        address = json_request['address']
        phone = json_request['phone']
        genres = request.form.getlist('genres')
        facebook_link = json_request['facebook_link']
        image_link = json_request['image_link']
        website = json_request['website']
        seeking_talent = True if 'seeking_talent' in request.form else False
        seeking_description = json_request['seeking_description']
        venue = Venue(name=name, state=state, city=city, address=address, phone=phone, genres=genres, facebook_link=facebook_link, image_link=image_link, website=website, seeking_talent=seeking_talent, seeking_description=seeking_description)
        db.session.add(venue)
        db.session.commit()
        body['id'] = venue.id
        body['name'] = venue.name
        body['state'] = venue.state
        body['city'] = venue.city
        body['address'] = venue.address
        body['phone'] = venue.phone
        body['genres'] = venue.genres
        body['facebook_link'] = venue.facebook_link
        body['image_link'] = venue.image_link
        body['website'] = venue.website
        body['seeking_talent'] = venue.seeking_talent
        body['seeking_description'] = venue.seeking_description
    except:
        db.session.rollback()
        error = True
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + 'could not be listed.')
    if not error:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):

        error = False
        try:
            venue = Venue.query.get(venue_id)
            db.session.delete(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
        finally:
            db.session.close()
        if error:
            flash(f'An error occurred. Venue {venue_id} could not be deleted.')
        if not error:
            flash(f'Venue {venue_id} was successfully deleted.')


        return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()

    return render_template('pages/artists.html', artists=artists)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []

  for artist in artists:
      upcoming_shows = [show for show in artist.shows if show.start_time>datetime.now()]
      data.append({
        'id': artist.id,
        'name': artist.name,
        'num_upcoming_shows': len(upcoming_shows)
      })
  response={
    "count": len(artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  selected_artist = Artist.query.get(artist_id)

  past_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []

  for show in past_query:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  upcoming_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []

  for show in upcoming_query:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })

  genres = ''.join(selected_artist.genres[1:-1]).split(',')
  if selected_artist.genres[0] != '{':
      genres = [''.join(selected_artist.genres)]

  artist = {
    "id": selected_artist.id,
    "name": selected_artist.name,
    "genres": genres,
    "city": selected_artist.city,
    "state": selected_artist.state,
    "phone": selected_artist.phone,
    "website": selected_artist.website,
    "facebook_link": selected_artist.facebook_link,
    "seeking_venue": selected_artist.seeking_venue,
    "seeking_description": selected_artist.seeking_description,
    "image_link": selected_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  print(selected_artist.genres)

  return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  if artist:
    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.facebook_link.data = artist.facebook_link
    form.image_link.data = artist.image_link
    form.website.data = artist.website
    form.seeking_venue.data = artist.seeking_venue
    form.seeking_description.data = artist.seeking_description

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    error = False
    artist = Artist.query.get(artist_id)

    try:
        json_request = request.form
        artist.name = json_request['name']
        artist.genres = request.form.getlist('genres')
        artist.city = json_request['city']
        artist.state = json_request['state']
        artist.phone = json_request['phone']
        artist.image_link = json_request['image_link']
        artist.facebook_link = json_request['facebook_link']
        artist.website = json_request['website']
        artist.seeking_venue = True if 'seeking_venue' in request.form else False
        artist.seeking_description = json_request['seeking_description']

        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('Due to an error, the artist could not be edited.')
    if not error:
        flash('Artist was successfully updated!')

    return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue:
    form.name.data = venue.name
    form.genres.data = venue.genres
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  error = False
  venue = Venue.query.get(venue_id)

  try:
      json_request = request.form
      venue.name = json_request['name']
      venue.city = json_request['city']
      venue.state = json_request['state']
      venue.phone = json_request['phone']
      venue.genres = request.form.getlist('genres')
      venue.address = json_request['address']
      venue.image_link = json_request['image_link']
      venue.facebook_link = json_request['facebook_link']
      venue.website = json_request['website']
      venue.seeking_talent = True if 'seeking_talent' in request.form else False
      venue.seeking_description = json_request['seeking_description']

      db.session.commit()
  except:
      error = True
      db.session.rollback()
  finally:
      db.session.close()
  if error:
      flash('Due to an error, the venue could not be edited.')
  if not error:
      flash('Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  body = {}
  try:
      json_request = request.form
      name = json_request['name']
      state = json_request['state']
      city = json_request['city']
      phone = json_request['phone']
      genres = request.form.getlist('genres')
      facebook_link = json_request['facebook_link']
      image_link = json_request['image_link']
      website = json_request['website']
      seeking_venue = True if 'seeking_venue' in request.form else False
      seeking_description = json_request['seeking_description']

      artist = Artist(name=name, state=state, city=city, phone=phone, genres=genres,
      facebook_link=facebook_link, image_link=image_link, website=website,
      seeking_venue=seeking_venue, seeking_description=seeking_description)

      db.session.add(artist)
      db.session.commit()

      body['id'] = artist.id
      body['name'] = artist.name
      body['state'] = artist.state
      body['city'] = artist.city
      body['phone'] = artist.phone
      body['genres'] = artist.genres
      body['facebook_link'] = artist.facebook_link
      body['image_link'] = artist.image_link
      body['website'] = artist.website
      body['seeking_venue'] = artist.seeking_venue
      body['seeking_description'] = artist.seeking_description
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      flash('An error occurred. Your artist could not be listed.')
  else:
      flash('Artist was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  all_shows = db.session.query(Show).join(Artist).join(Venue).order_by(Show.start_time).all()
  data = []
  for show in all_shows:
      data.append({
          "venue_id": show.venue_id,
          "venue_name": show.venue.name,
          "artist_id": show.artist_id,
          "artist_name": show.artist.name,
          "artist_image_link": show.artist.image_link,
          "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
      })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  body = {}
  try:
      json_request = request.form
      artist_id = json_request['artist_id']
      venue_id = json_request['venue_id']
      start_time = json_request['start_time']
      show = Show(artist_id=artist_id, venue_id=venue_id, start_time=start_time)
      db.session.add(show)
      db.session.commit()
      body['artist_id'] = show.artist_id
      body['venue_id'] = show.venue_id
      body['start_time'] = show.start_time
  except:
      db.session.rollback()
      error = True
  finally:
      db.session.close()
  if error:
      abort(500)
      flash('An error occurred. Your show could not be listed.')
  else:
      flash('Your show was successfully listed!')

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
