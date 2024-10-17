from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from config import Config
from rule_engine import create_rule, combine_rules, evaluate_rule
import logging
import os

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

# Set up caching
cache = Cache(app)

class Rule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rule_string = db.Column(db.String(500), nullable=False)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/create_rule', methods=['POST'])
@limiter.limit("10 per minute")
def api_create_rule():
    rule_string = request.json.get('rule')
    if not rule_string:
        return jsonify({"error": "No rule provided"}), 400

    try:
        rule_ast = create_rule(rule_string)
    except ValueError as e:
        logging.error(f"Error creating rule: {str(e)}")
        return jsonify({"error": str(e)}), 400

    new_rule = Rule(rule_string=rule_string)
    db.session.add(new_rule)
    db.session.commit()

    return jsonify({"message": "Rule created successfully", "rule_id": new_rule.id}), 201

@app.route('/evaluate_rule', methods=['POST'])
@limiter.limit("100 per minute")
def api_evaluate_rule():
    data = request.json.get('data')
    if not data:
        return jsonify({"error": "No data provided"}), 400

    rules = Rule.query.all()
    if not rules:
        return jsonify({"result": True, "message": "No rules to evaluate"}), 200

    rule_strings = [rule.rule_string for rule in rules]

    try:
        combined_rule = combine_rules(rule_strings)
        result = evaluate_rule(combined_rule, data)
        return jsonify({"result": result})
    except Exception as e:
        logging.error(f"Error evaluating rule: {str(e)}")
        return jsonify({"error": f"Error evaluating rule: {str(e)}"}), 500

@app.route('/get_rules', methods=['GET'])
def get_rules():
    rules = Rule.query.all()
    return jsonify([{"id": rule.id, "rule_string": rule.rule_string} for rule in rules])

@app.route('/delete_rule/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    rule = Rule.query.get(rule_id)
    if rule:
        db.session.delete(rule)
        db.session.commit()
        return jsonify({"message": f"Rule {rule_id} deleted successfully"}), 200
    return jsonify({"error": "Rule not found"}), 404

@app.route('/delete_all_rules', methods=['DELETE'])
def delete_all_rules():
    Rule.query.delete()
    db.session.commit()
    return jsonify({"message": "All rules deleted successfully"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)