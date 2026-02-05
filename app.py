from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
import pandas as pd


# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:sami_db_pw@localhost/micro_analyst"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "my_supersecretkey"


# Initialize database and login manager
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model


class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)


# Create database
with app.app_context():
    db.create_all()

# Load user for Flask-Login


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Home route


@app.route("/")
def home():
    return render_template("home.html")

# Register route


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            return render_template("sign_up.html", error="Username already taken!")
        if Users.query.filter_by(email=email).first():
            return render_template("sign_up.html", error="Email already registered!")

        hashed_password = generate_password_hash(
            password, method="pbkdf2:sha256")

        new_user = Users(username=username, email=email,
                         password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("sign_up.html")

# Login route


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Protected dashboard route


@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        file = request.files["file"]
        if file.content_type == "text/plain":
            return file.read().decode()
        elif file.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" or file.content_type == "application/vnd.ms-excel":
            df = pd.read_excel(file)
            return df.to_html()

    else:
        return render_template("dashboard.html", username=current_user.username)


@app.route("/handle_post", methods=["POST"])
def handle_post():
    greetings = request.json['greetings']
    name = request.json['name']

    with open('text_file.txt', 'w') as f:
        f.write(f"{greetings} {name}")
    return jsonify({'message': 'successfully written!'})
# Logout route


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
