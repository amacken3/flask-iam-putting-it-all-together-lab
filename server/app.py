#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

class Signup(Resource):
    def post(self):
        data = request.get_json()

        try:
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data.get('password')

            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id

            return UserSchema().dump(user), 201

        except (IntegrityError, ValueError):
            db.session.rollback()
            return {'error': '422 Unprocessable Entity'}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': '401 Unauthorized'}, 401

        user = User.query.filter(User.id == user_id).first()

        if not user:
            return {'error': '401 Unauthorized'}, 401

        return UserSchema().dump(user), 200
    
class Login(Resource):
    def post(self):
        data = request.get_json()

        user = User.query.filter(User.username == data.get('username')).first()

        if user and user.authenticate(data.get('password')):
            session['user_id'] = user.id
            return UserSchema().dump(user), 200

        return {'error': '401 Unauthorized'}, 401

class Logout(Resource):
    def delete(self):
        if not session.get('user_id'):
            return {'error': '401 Unauthorized'}, 401

        session['user_id'] = None
        return {}, 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': '401 Unauthorized'}, 401

        recipes = Recipe.query.filter(Recipe.user_id == user_id).all()

        return RecipeSchema(many=True).dump(recipes), 200

    def post(self):
        user_id = session.get('user_id')

        if not user_id:
            return {'error': '401 Unauthorized'}, 401

        data = request.get_json()

        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )

            db.session.add(recipe)
            db.session.commit()

            return RecipeSchema().dump(recipe), 201

        except (IntegrityError, ValueError):
            db.session.rollback()
            return {'error': '422 Unprocessable Entity'}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)