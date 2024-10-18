from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from rule_engine import create_rule, combine_rules, evaluate_rule
import logging
import json

app = Flask(__name__)
app.config.from_object(Config)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Set up CORS
CORS(app)

# Set up rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

# Set up database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Set up caching
cache = Cache(app)

# Set up login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    rules = db.relationship('Rule', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_string = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/api/create_rule', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
def api_create_rule():
    try:
        rule_string = request.json.get('rule')
        if not rule_string:
            return jsonify({"error": "No rule provided"}), 400

        rule_ast = create_rule(rule_string)

        new_rule = Rule(rule_string=rule_string, author=current_user)
        db.session.add(new_rule)
        db.session.commit()

        return jsonify({"message": "Rule created successfully", "rule_id": new_rule.id}), 201
    except ValueError as e:
        logging.error(f"Error creating rule: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Unexpected error creating rule: {str(e)}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/evaluate_rule', methods=['POST'])
@login_required
@limiter.limit("100 per minute")
def api_evaluate_rule():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        rules = Rule.query.filter_by(user_id=current_user.id).all()
        if not rules:
            return jsonify({"result": True, "message": "No rules to evaluate"}), 200

        rule_strings = [rule.rule_string for rule in rules]

        combined_rule = combine_rules(rule_strings)
        result = evaluate_rule(combined_rule, data)
        return jsonify({"result": result})
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON data provided"}), 400
    except Exception as e:
        app.logger.error(f"Error evaluating rule: {str(e)}")
        return jsonify({"error": f"Error evaluating rule: {str(e)}"}), 500

@app.route('/api/get_rules', methods=['GET'])
@login_required
def get_rules():
    try:
        rules = Rule.query.filter_by(user_id=current_user.id).all()
        return jsonify([{"id": rule.id, "rule_string": rule.rule_string} for rule in rules])
    except Exception as e:
        app.logger.error(f"Error fetching rules: {str(e)}")
        return jsonify({"error": f"Error fetching rules: {str(e)}"}), 500

@app.route('/api/delete_rule/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    try:
        rule = Rule.query.get(rule_id)
        if rule and rule.user_id == current_user.id:
            db.session.delete(rule)
            db.session.commit()
            return jsonify({"message": f"Rule {rule_id} deleted successfully"}), 200
        return jsonify({"error": "Rule not found or unauthorized"}), 404
    except Exception as e:
        app.logger.error(f"Error deleting rule: {str(e)}")
        return jsonify({"error": f"Error deleting rule: {str(e)}"}), 500

@app.route('/api/delete_all_rules', methods=['DELETE'])
@login_required
def delete_all_rules():
    try:
        Rule.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"message": "All rules deleted successfully"}), 200
    except Exception as e:
        app.logger.error(f"Error deleting all rules: {str(e)}")
        return jsonify({"error": f"Error deleting all rules: {str(e)}"}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)