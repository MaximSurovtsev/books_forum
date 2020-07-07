from flask import render_template, redirect, flash, url_for, request, session, jsonify
from app import app, db
from app.form import *
from app.models import *
from flask_login import login_user, logout_user, current_user, login_required ###
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
from app import basedir
from sqlalchemy.exc import IntegrityError
import hashlib
import json
from random import randint

@app.errorhandler(404)
def not_found_error(error):
	return render_template('404.html'), 404
@app.errorhandler(500)
def internal_error(error):
	db.session.rollback()
	return render_template('500.html'), 500



@app.route('/')
@login_required
def index():
	if User.query.filter_by(username='admin').first() is None:
		admin = User(username='admin', email='admin@mail.ru')
		admin.set_password('1')
		admin.set_admin()
		db.session.add(admin)
		try:
			db.session.commit()
		except IntegrityError:
			return redirect(url_for('internal_error'))
	session.setdefault('urls', [])
	books = Book.query.all()[:10]
	return render_template('index.html', books=books)

	
@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			return redirect(url_for('login', error=1))

		login_user(user)
		return redirect(url_for('index'))

	
	error = request.args.get('error')

	return render_template('login.html', form=form, error=error)



@app.route('/reg', methods=['GET', 'POST'])
def reg():
	form = RegForm()
	if form.validate_on_submit():

		user = User(email=form.email.data, username=form.username.data)
		user.set_password(form.password.data)
		user.set_user()

		db.session.add(user)

		try:
			db.session.commit()
		except IntegrityError:
			return redirect(url_for('internal_error'))
		return redirect(url_for('login', error=''))
		
	return render_template('reg.html', form=form)



@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
	if not current_user.is_admin():
		return redirect(url_for('index'))

	form = FileForm()
	books = Book.query.all()

	if form.validate_on_submit():	
		description = form.description.data
		title = form.title.data
		author = form.author.data

		filename = secure_filename(form.file.data.filename) + str(randint(0, 2**32))
		ext = form.file.data.content_type.replace('image/', '')
		hashname = hashlib.md5(filename.encode()).hexdigest()
		form.file.data.save(basedir + '/static/img/' + hashname + '.' + ext)
		src = hashname + '.' + ext
	 
		cat = 'Не задано'
		date = datetime.now().strftime('%G %e %B %H:%M')
		book = Book(title=title, author=author, category=cat, description=description, date=date, views=0, user_id=current_user.id, username=current_user.username, comments_counter=0, votes=0,src=src)
		db.session.add(book)

	
		try:
			db.session.commit()
		except IntegrityError:
			return redirect(url_for('internal_error'))
		return redirect(url_for('admin'))

	return render_template('admin.html', form=form, books=books)

@app.route('/delete_book/<book_id>', methods=['POST'])
def delete_book(book_id):
	book = Book.query.filter_by(id=book_id).first()
	comments = Comment.query.filter_by(book_id=book_id).all()
	votes = BookVote.query.filter_by(book_id=book_id).all()
	
	if current_user.is_admin:
		for v in votes: db.session.delete(v)
		for c in comments: db.session.delete(c)
		db.session.delete(book)
		
		try:
			db.session.commit()
		except IntegrityError:
			return redirect(url_for('internal_error'))

		return jsonify({'status': 'OK'})
	return jsonify({'status': 'FAILED'})



@app.route('/user/<user_id>')
def user(user_id):
	user = User.query.filter_by(id=user_id).first()
	votes = BookVote.query.filter_by(user_id=user.id).all()
	books = [Book.query.filter_by(id=vote.book_id).first() for vote in votes]
	comments = Comment.query.filter_by(user_id=user_id).all()
	rating = sum([comment.votes for comment in comments])
	return render_template('profile.html', books=books, comments=comments, user=user, rating=rating)




@app.route('/delete_comment/<comment_id>', methods=['POST'])
def delete_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first()
	if current_user.id == comment.user_id:
		votes = CommentVote.query.filter_by(comment_id=comment_id).all()
		for v in votes: db.session.delete(v)
		book_id = comment.book_id
		book = Book.query.get(book_id)
		book.comments_counter -= 1
		db.session.delete(comment)
		try:
			db.session.commit()
		except IntegrityError:
			return redirect(url_for('internal_error'))

		return jsonify({'status': 'OK'})
	return jsonify({'status': 'FAILED'})


@app.route('/like_book/<book_id>', methods=['POST'])
@login_required
def like_book(book_id):
	book = Book.query.filter_by(id=book_id).first()
	like = BookVote.query.filter_by(user_id=current_user.id).first()
	
	if like is None:
		like = BookVote(user_id=current_user.id, book_id=book_id)
		book.votes += 1
		db.session.add(like)
	else:
		book.votes -= 1
		db.session.delete(like)

	db.session.add(book)
	try:
		db.session.commit()
	except IntegrityError:
		db.session.rollback() 
		return render_template('500.html'), 500

	return jsonify({'votes': book.votes})

@app.route('/like_comment/<comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
	comment = Comment.query.filter_by(id=comment_id).first()

	like = CommentVote.query.filter_by(user_id=current_user.id).first()

	if like is None:
		like = CommentVote(user_id=current_user.id, comment_id=comment_id)
		comment.votes += 1
		db.session.add(like)
	else:
		comment.votes -= 1
		db.session.delete(like)

	db.session.add(comment)
	try:
		db.session.commit()
	except IntegrityError:
		db.session.rollback() 
		return render_template('500.html'), 500
		
	return jsonify({'votes': comment.votes})

@app.route('/test')
def test():
	description = 'Еще недавно у двенадцатилетнего Люка Эллиса была вполне привычная жизнь: школа, обеды с родителями в любимой пиццерии, вечера в компании лучшего друга… Пока одним июньским утром он не просыпается в собственной комнате, вот только в ней нет окон и находится она в тщательно укрытом от всего мира месте под названием "Институт". Здесь над похищенными из разных городов детьми, обладающими даром телепатии или телекинеза, проводят жестокие эксперименты с целью максимально развить их паранормальные способности.Бежать невозможно. Будущее предопределено, и это будущее - загадочная Дальняя половина Института, откуда не возвращался еще ник... Однако Люк не намерен сдаваться. Он уверен: в любой системе есть слабое место и он дождется часа, когда сможет вновь оказаться на свободе...'
	title = 'Интитут'
	author = 'Стивен Кинг'
	cat = 'Ужасы'
	date = datetime.now().strftime('%G %e %B %H:%M')
	book = Book(title=title, author=author, category=cat, description=description, date=date, views=0, user_id=current_user.id, username=current_user.username, comments_counter=0, votes=0,src='cover.jpg')

	db.session.add(book)
	try:
		db.session.commit()
	except IntegrityError:
		db.session.rollback() 
		return render_template('500.html'), 500
	return redirect(url_for('book', book_id=book.id))



@app.route('/book/<book_id>', methods=['GET', 'POST'])
def book(book_id):
	comments = Comment.query.filter_by(book_id=book_id).all()
	book = Book.query.get(book_id)
	
	if request.url not in session['urls']:
		session['urls'].append(request.url)
		book.views += 1
		db.session.add(book)
		try:
			db.session.commit()
		except IntegrityError:
			db.session.rollback() 
			return render_template('500.html'), 500
		session.modified = True

	if request.method == "POST":
		content = request.form['comment']
		date = datetime.now().strftime('%G %e %B %H:%M')

		comment = Comment(votes=0, username=current_user.username, user_id=current_user.id, content=content, book_id=book.id, date=date)
		db.session.add(comment)
		book.comments_counter += 1

		try:
			db.session.commit()
		except IntegrityError:
			db.session.rollback() 
			return render_template('500.html'), 500

		# return redirect(url_for('book', book_id=book_id))

		print('REQUEST')
		return jsonify({
			'id': comment.id,
			'content': comment.content,
			'votes': 0,
			'date': date,
			'userlink': url_for('user', user_id=current_user.id),
			'username': current_user.username,
			'comment_delete_link': url_for('delete_comment', comment_id=comment.id)
			})


	return render_template('book.html', book=book, comments=comments)
	# return render_template('book.html', form=form, book=book, comments=comments)






