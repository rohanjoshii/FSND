import os
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random
from flask_sqlalchemy import SQLAlchemy

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

# CORS Headers

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def retrieve_categories():
            categories = Category.query.all()

            if len(categories) == 0:
                abort(404)

            return jsonify({
                'success': True,
                'categories': {category.id: category.type for category in categories}
            })

    @app.route('/questions')
    def retrieve_questions():
                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection)

                categories = Category.query.order_by(Category.type).all()

                if len(current_questions) == 0:
                    abort(404)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection),
                    'categories': {category.id: category.type
                                   for category in categories},
                    'current_category': None
                })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
            try:
                question = Question.query.filter(
                    Question.id == question_id).one_or_none()

                if question is None:
                    abort(404)

                    question.delete()

                    return jsonify({
                        'success': True,
                        'deleted': question_id
                    })

            except:
                abort(422)

    @app.route('/questions', methods=['POST'])
    def create_question():
                body = request.get_json()

                if not (
                        'question' in body and
                        'answer' in body and
                        'difficulty' in body and 'category' in body):
                    abort(422)

                new_question = body.get('question')
                new_answer = body.get('answer')
                new_difficulty = body.get('difficulty')
                new_category = body.get('category')

                try:
                    question = Question(
                                        question=new_question, answer=new_answer,
                                        difficulty=new_difficulty,
                                        category=new_category)
                    question.insert()

                    return jsonify({
                        'success': True,
                        'created': question.id
                    })

                except:
                    abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
            body = request.get_json()
            search_term = body.get('searchTerm', None)

            if search_term:
                questions = Question.query.filter(
                    Question.question.ilike(f'%{search_term}%')).all()
                if questions:

                        return jsonify({
                            'success': True,
                            'questions': [question.format() for question in questions],
                            'total_questions': len(questions),
                            'current_category': None
                        })
                else:
                        abort(422)
            else:
                abort(404)

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def retrieve_questions_by_category(category_id):
                try:
                    category = Category.query.filter_by(id=category_id).one_or_none()

                    if (category is None):
                        abort(400)

                    questions = Question.query.filter_by(category=category.id).all()

                    return jsonify({
                            'success': True,
                            'questions': [question.format() for question in questions],
                            'total_questions': len(questions),
                            'current_category': category_id
                    })
                except:
                    abort(404)

    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
                    body = request.get_json()

                    if not ('quiz_category' in body and 'previous_questions' in body):
                        abort(422)

                    category = body.get('quiz_category')
                    previous_questions = body.get('previous_questions')

                    print(category['id'])
                    category_id = int(category['id'])
                    if (category['id'] == 0):
                        questions = Question.query.all()
                    else:
                        questions = Question.query.filter_by(category=category['id']).all()

                    all = len(questions)

                    def get_random_question():
                        return questions[random.randrange(0, len(questions), 1)]

                    def check_if_used(question):
                        used = False
                        for q in previous_questions:
                            if (q == question.id):
                                used = True

                        return used

                    rand = get_random_question()

                    while (check_if_used(rand)):
                        rand = get_random_question()

                        if (len(previous_questions) == all):
                            return jsonify({
                                'success': True
                            })

                    return jsonify({
                        'success': True,
                        'question': rand.format()
                    })

    @app.errorhandler(404)
    def not_found(error):
                return jsonify({
                  "success": False,
                  "error": 404,
                  "message": "resource not found"
                  }), 404

    @app.errorhandler(422)
    def unprocessable(error):
                return jsonify({
                  "success": False,
                  "error": 422,
                  "message": "unprocessable"
                  }), 422

    @app.errorhandler(400)
    def bad_request(error):
                return jsonify({
                  "success": False,
                  "error": 400,
                  "message": "bad request"
                  }), 400

    return app
