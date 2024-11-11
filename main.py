from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField
from wtforms.validators import DataRequired, NumberRange
import requests



API_TMDB = "e2784ba8eeec3dc08559f5b819f17ab4"
URL_TMDB = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class RateMovieForm(FlaskForm):
    rating = FloatField(label="Your Rating Out of 10 e.g 8.5", validators=[DataRequired(), NumberRange(min=1.0, max=10.0)])
    review = StringField(label="Your review", validators=[DataRequired()])
    submit = SubmitField(label="Done")

class AddMovie(FlaskForm):
    title = StringField(label="Movie Title", validators=[DataRequired()])
    submit = SubmitField(label="Add Movie")

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie))
    all_movies = result.scalars().all()
    return render_template("index.html", movies=all_movies)

@app.route("/update", methods=["GET", "POST"])
def update():
    form_update = RateMovieForm()
    movie_id = request.args.get("id")
    movie_selected = db.get_or_404(Movie, movie_id)
    if form_update.validate_on_submit():
        movie_selected.rating = form_update.rating.data
        movie_selected.review = form_update.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', form=form_update, movie=movie_selected)

@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get("id")
    movie_selected = db.get_or_404(Movie, movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_movie = AddMovie()
    if add_movie.validate_on_submit():
        movie_title = add_movie.title.data
        reponse = requests.get(URL_TMDB, params={"api_key":API_TMDB, "query":movie_title})
        data = reponse.json()['results']
        return render_template('select.html', selections=data)
    return render_template('add.html', form=add_movie)


@app.route("/find", methods=["GET", "POST"])
def find_movie():
    movie_id_api = request.args.get("id")
    if movie_id_api:
        url_for_movie = f"https://api.themoviedb.org/3/movie/{movie_id_api}"
        reponse = requests.get(url_for_movie, params={"api_key": API_TMDB, "language": "en-US"})
        data = reponse.json()
        print("API Response Data:", data)  # Print full response for debugging
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("home"))



if __name__ == '__main__':
    app.run(debug=True)