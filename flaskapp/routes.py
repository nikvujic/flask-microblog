import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from flaskapp import app, db, bcrypt, mail
from flaskapp.forms import RegistrationForm, LoginForm, ChangeInfoForm, PostForm, RequestResetForm, ResetPasswordForm
from flaskapp.models import User, Post
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message


@app.route("/")
@app.route("/home")
def home():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(
        Post.date_posted.desc()).paginate(page=page, per_page=10)
    return render_template('home.html', title='Home', jumbo=False, sidemenu=False, posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(
            f'Account created for {form.username.data}! You can log in now.', "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login unsuccessful! Please check your username and password.')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    prof_image = url_for('static', filename='images/' +
                         current_user.image_file)
    return render_template('account.html', title=f'{current_user.username}', prof_image=prof_image)


def save_image(form_image):
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(form_image.filename)
    image_filename = random_hex + file_extension
    image_path = os.path.join(app.root_path, 'static/images', image_filename)
    form_image.save(image_path)

    output_size = (300, 300)
    resized = Image.open(form_image)
    resized.thumbnail(output_size)
    resized.save(image_path)

    return image_filename


@app.route("/account/update", methods=['GET', 'POST'])
@login_required
def account_update():
    form = ChangeInfoForm()
    if form.validate_on_submit():
        if form.image.data:
            image_file = save_image(form.image.data)
            current_user.image_file = image_file
        current_user.username = form.username.data
        current_user.full_name = form.full_name.data
        current_user.about = form.about.data
        db.session.commit()
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.full_name.data = current_user.full_name
        form.about.data = current_user.about
    return render_template('change-info.html', title=f'{current_user.username}', form=form)


@app.route("/post/create_new", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data,
                    content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been published!", 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title="Post", post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post_id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form)


@app.route("/post/<int:post_id>/delete")
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))


@app.route("/user/<username>")
def user_info(username):
    if current_user.is_authenticated and current_user.username == username:
        return redirect(url_for('account'))
    user = User.query.filter_by(username=username).first()
    return render_template('user.html', title=f'{username}', user=user)


def send_reset_email(user):
    token = user.get_reset_token()
    message = Message('Password Reset', sender='noreply@demo.com', recipients=[user.email])
    message.body = f'''To reset your password, please visit the following link:
{url_for('reset_token', token=token, _external=True)}
'''
    mail.send(message)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Password reset email sent!', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Password Reset', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if not user:
        flash('Invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(
            f'Your password has been updated! You can log in now.', "success")
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Password Reset', form=form)