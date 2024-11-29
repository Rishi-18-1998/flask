# 1. API Development with Flask

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import numpy as np
from sklearn.tree import DecisionTreeClassifier
import joblib

# Initialize Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/your_database'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User created successfully!'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login failed!'}), 401
    return jsonify({'message': 'Logged in successfully!'}), 200


@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    new_task = Task(
        user_id=data['user_id'],
        title=data['title'],
        description=data.get('description', ''),
        status=data['status'],
        priority=data['priority'],
        deadline=datetime.datetime.strptime(data['deadline'], '%Y-%m-%d'),
        estimated_time=data['estimated_time'],
    )
    db.session.add(new_task)
    db.session.commit()
    return jsonify({'message': 'Task created successfully!'}), 201


@app.route('/tasks/<user_id>', methods=['GET'])
def get_tasks(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'deadline': task.deadline,
        'estimated_time': task.estimated_time,
    } for task in tasks])

# 2. Database Operations
# Fetch overdue tasks
@app.route('/tasks/overdue/<user_id>', methods=['GET'])
def get_overdue_tasks(user_id):
    current_date = datetime.datetime.utcnow()
    tasks = Task.query.filter(Task.user_id == user_id, Task.deadline < current_date).all()
    return jsonify([{
        'id': task.id,
        'title': task.title,
        'description': task.description,
    } for task in tasks])

# Fetch tasks by priority and status
@app.route('/tasks/<user_id>/<priority>/<status>', methods=['GET'])
def get_tasks_by_priority_status(user_id, priority, status):
    tasks = Task.query.filter_by(user_id=user_id, priority=priority, status=status).all()
    return jsonify([{
        'id': task.id,
        'title': task.title,
        'description': task.description,
    } for task in tasks])

# 3. AI Integration
# A simple rule-based model for prioritizing tasks
@app.route('/tasks/prioritize/<user_id>', methods=['GET'])
def prioritize_tasks(user_id):
    tasks = Task.query.filter_by(user_id=user_id).all()
    task_data = [
        [
            (task.deadline - datetime.datetime.utcnow()).days,
            task.estimated_time,
            1 if task.priority == 'high' else (2 if task.priority == 'medium' else 3),
        ]
        for task in tasks
    ]
    labels = [1 for _ in tasks]  # Dummy labels for model
    # Fit a decision tree classifier
    model = DecisionTreeClassifier()
    model.fit(task_data, labels)
    # Predict priority
    predictions = model.predict(task_data)
    prioritized_tasks = sorted(zip(tasks, predictions), key=lambda x: x[1])
    return jsonify([{
        'id': task.id,
        'title': task.title,
        'priority': prediction
    } for task, prediction in prioritized_tasks])

# 4. Research Task
# Integrate Hugging Face sentiment analysis
@app.route('/tasks/analyze/sentiment', methods=['POST'])
def analyze_sentiment():
    from transformers import pipeline
    sentiment_pipeline = pipeline("sentiment-analysis")
    data = request.json
    task_description = data['description']
    result = sentiment_pipeline(task_description)
    return jsonify({'description': task_description, 'sentiment': result})

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
