from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextField
from wtforms.validators import DataRequired, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.widgets import TextArea
import re

class LoginForm(FlaskForm):
	username = StringField('Имя', validators=[DataRequired()])
	password = PasswordField('Пароль', validators=[DataRequired()])
	submit = SubmitField('Войти')

class RegForm(FlaskForm):
	username = StringField('Имя', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired()])
	password = PasswordField('Пароль', validators=[DataRequired()])
	repeat_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
	submit = SubmitField('Зарегистрироваться')

class CommentForm(FlaskForm):
	comment = StringField('Ваш комментарий...', validators=[DataRequired()])
	submit = SubmitField('Отправить')

class FileForm(FlaskForm):
	title = StringField('Название', validators=[DataRequired()])
	author = StringField('Автор', validators=[DataRequired()])
	file  = FileField(validators=[DataRequired()])
	description = StringField('Название', validators=[DataRequired()], widget=TextArea())
	submit = SubmitField('Добавить')
