#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask_cors import CORS
from flask import Flask, request, jsonify, abort
import random
from models import setup_db, Question, Category
from utils import paginate_questions

#----------------------------------------------------------------------------#
# Setting Variables
#----------------------------------------------------------------------------#

QUESTIONS_PER_PAGE = 10

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

def create_app(test_config=None):

    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # set up CORS, allowing all origins
    CORS(app, resources={'/': {'origins': '*'}})


    # Setting access control

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers','Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods','GET,PUT,POST,DELETE,OPTIONS')
        return response

    # ----------------------------------------------------------------------------#
    # Handeling different Requests, Responses and Errors
    # ----------------------------------------------------------------------------#


    # Handeling categories GET requests

    @app.route('/categories')
    def get_categories():

        # getting (GET) requests for getting different categories.
        # Getting all different categories and save them in a dictionary

        # querying all categoris (Sci, Sports ..etc)
        categories = Category.query.all()
        get_eachCategories = {}
        for category in categories:

            # retrieving category ID as Type
            # print(get_eachCategories[category.id])

            get_eachCategories[category.id] = category.type

        # if there is no categories found, throw a 404 abort error
        if (get_eachCategories[category.id] is None):
            abort(404)

        # jsonify returned data
        return jsonify({
            'success': True,
            'categories': get_eachCategories
        })

    # Handeling questions GET requests

    @app.route('/questions')
    def get_questions():

        # getting (GET) requests for getting different questions.
        # Getting all different categories and save them in a questions

        # querying all questions (Sci, Sports ..etc)
        questionSelected = Question.query.all()
        NumQuestions = len(questionSelected)

        currentQuestions = paginate_questions(request, questionSelected,QUESTIONS_PER_PAGE)
        #print(currentQuestions)

        # get all categories and add to dict
        categories = Category.query.all()

        get_eachCategories = {}
        for category in categories:
            get_eachCategories[category.id] = category.type

        # abort 404 if no questions
        if (len(currentQuestions) is None):
            abort(404)

        # jsonify returned data
        return jsonify({
            'success': True,
            'questions': currentQuestions,
            'categories': get_eachCategories,
            'total_questions': NumQuestions
        })


    # Handeling deleted (DELET) questions by question id

    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_question(id):

        try:
            question = Question.query.filter_by(id=id).one_or_none()  # get the question by id
            # abort 404 if no question found
            if question is None:
                abort(404)
            else:
                question.delete()  # Delet the selected question
            # return success deletion response
            return jsonify({
                'success': True,
                'deleted': id
            })
        except:
            # throw a 422 response if these is a problem with deleting a question
            abort(422)


    # Handeling adding (POST) new questions
    @app.route('/questions', methods=['POST'])
    def post_question():

        body = request.get_json() # loading the request body

        # if search term is present
        if (body.get('searchTerm')):
            searchQuestion = body.get('searchTerm')
            # query the database using search term
            selectedQuesion = Question.query.filter(Question.question.ilike(f'%{searchQuestion}%')).all()
            # throw a 404 if these is no question found
            if (len(selectedQuesion) == 0):
                abort(404)

            # paginating the results
            paginated = paginate_questions(request, selectedQuesion,QUESTIONS_PER_PAGE)

            # return results
            return jsonify({
                'success': True,
                'questions': paginated,
                'total_questions': len(Question.query.all())
            })

        # if there is no search item found, create new question
        else:

            # load data from body
            newQuestion = body.get('question')
            newAnswer = body.get('answer')
            difficultyLevel = body.get('difficulty')
            newCategory = body.get('category')

            # ensure all fields have data
            if ((newQuestion is None) or (newAnswer is None)
                    or (difficultyLevel is None) or (newCategory is None)):
                abort(422)

            try:
                # create and insert new question
                newQuestion = Question(question=newQuestion, answer=newAnswer,
                                    difficulty=difficultyLevel, category=newCategory)
                newQuestion.insert()
                #print(newQuestion)

                # geting all questions and paginate
                selection = Question.query.order_by(Question.id).all()
                current_questions = paginate_questions(request, selection,QUESTIONS_PER_PAGE)

                # return new data to view
                return jsonify({
                    'success': True,
                    'created': newQuestion.id,
                    'question_created': newQuestion.question,
                    'questions': current_questions,
                    'total_questions': len(Question.query.all())
                })

            except:

                # throw a 422 abort error if a problem has occuried
                abort(422)

    # Handeling requests looking for a specific question

    @app.route('/categories/<int:id>/questions')
    def get_questions_by_category(id):

        #Querying categoty by ID
        category = Category.query.filter_by(id=id).one_or_none() # get the category by id

        # throw a 400 abort error if no category is found
        if (category is None):
            abort(400)

        # getting the matching results
        selectedQuestion = Question.query.filter_by(category=category.id).all()

        # paginate the selection
        paginated = paginate_questions(request, selectedQuestion,QUESTIONS_PER_PAGE)

        # jsonify returned data
        return jsonify({
            'success': True,
            'questions': paginated,
            'total_questions': len(Question.query.all()),
            'current_category': category.type
        })

    # Handeling quizzes answers (POST)

    @app.route('/quizzes', methods=['POST'])
    def get_random_quiz_question():

        # loading the request body
        body = request.get_json()

        # getting the previous questions
        previousQuestions = body.get('previous_questions')

        # getting the category
        quizCategory = body.get('quiz_category')

        # abort 400 if category or previous questions isn't found
        if ((quizCategory is None) or (previousQuestions is None)):
            abort(400)

        # if "ALL" is selected, load questions all questions
        if (quizCategory['id'] == 0):
            selectedQuestions = Question.query.all()
        # else load questions for given category
        else:
            selectedQuestions = Question.query.filter_by(category=quizCategory['id']).all()

        # get total number of questions
        totalQuestions = len(selectedQuestions)

        # picks a random question
        def get_random_question():
            return selectedQuestions[random.randrange(0, len(selectedQuestions), 1)]

        # checks to see if question has already been used
        def check_if_attmpted(attmptedQuestion):
            attmpted = False
            for i in previousQuestions:
                if (i == attmptedQuestion.id):
                    attmpted = True

            return attmpted

        # get random question
        attmptedQuestion = get_random_question()

        # check if used, execute until unused question found
        while (check_if_attmpted(attmptedQuestion)):
            attmptedQuestion = get_random_question()

            # return no results, if all questions were attmpted
            # necessary if category has <5 questions
            if (len(previousQuestions) == totalQuestions):

                # jsonify returned data
                return jsonify({
                    'success': True
                })

        # jsonify returned data
        return jsonify({
            'success': True,
            'question': attmptedQuestion.format()
        })

#----------------------------------------------------------------------------#
# ERROR HANDLERS
# Create error handlers for all expected errors
#----------------------------------------------------------------------------#

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