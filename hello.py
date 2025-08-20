from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm, SearchForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os
import json
import time  # For SSE polling

# Create a Flask Instance
app = Flask(__name__)
ckeditor = CKEditor(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mynewtoy@localhost/our_users'
app.config['SECRET_KEY'] = "My Secret Key"
app.config['UPLOAD_FOLDER_BASE'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static/uploads/images')

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'webm', 'ogg', 'mov'}
VIDEO_FOLDER = os.path.join('static', 'uploads', 'videos')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

PAGE_PERMISSIONS = {
    'adele': [25, 17, 18],
    'videos': [25, 17, 18],
    'crafts': [25, 17, 18],
    'samantha': [25, 17, 18, 19],
    'philly': [25, 17, 18],
    'redhook': [25, 17, 18]
}
admin_id = PAGE_PERMISSIONS

if not os.path.exists(VIDEO_FOLDER):
    os.makedirs(VIDEO_FOLDER)

def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize The Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask_Login Configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Pass Stuff To Navbar
@app.context_processor
def base():
    search_form = SearchForm()
    return dict(search_form=search_form)

# Create Admin Page
@app.route('/admin')
@login_required
def admin():
    id = current_user.id
    if id == 25:
        return render_template("admin.html")
    else:
        flash("Sorry you must be the Admin to access the Admin Page...")
        return redirect(url_for('dashboard'))

# Create Search Function
@app.route('/search', methods=["POST"])
def search():
    form = SearchForm()
    posts = Posts.query
    if form.validate_on_submit():
        post.searched = form.search.data
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html", form=form, search=post.searched, posts=posts)

# Create Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    search_form = SearchForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                flash("Login successful!", "success")
                return redirect(url_for('dashboard'))
            else:
                flash("Wrong Password - Try Again!", "danger")
        else:
            flash("That User Doesn't Exist! Try Again...", "danger")
    else:
        if request.method == 'POST':
            print("Form Errors:", form.errors)
    return render_template('login.html', form=form, search_form=search_form)

# Create Logout Page
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash("You Have Been Logged Out! Thanks For Stopping By...")
    return redirect(url_for('login'))

# Create Dashboard Page
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UserForm()
    id = current_user.id
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        if 'profile_pic' in request.files:
            profile_pic_file = request.files['profile_pic']
            if profile_pic_file and profile_pic_file.filename != '':
                pic_filename = secure_filename(profile_pic_file.filename)
                pic_name = str(uuid.uuid4()) + "_" + pic_filename
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], pic_name)
                profile_pic_file.save(upload_path)
                name_to_update.profile_pic = pic_name
        try:
            db.session.commit()
            flash("User Updated Successfully!", "success")
            return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)
        except Exception as e:
            flash("Error! There was a problem... try again.", "danger")
            print(e)
            return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)
    return render_template("dashboard.html", form=form, name_to_update=name_to_update, id=id)

@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            flash("Blog Post Was Deleted!")
            posts = Posts.query.order_by(desc(Posts.date))
            return render_template("posts.html", posts=posts)
        except:
            flash("Whoops! There was a problem deleting post, try again...")
            posts = Posts.query.order_by(desc(Posts.date))
            return render_template("posts.html", posts=posts)
    else:
        flash("You Aren't Authorized To Delete That Post!")
        posts = Posts.query.order_by(desc(Posts.date))
        return render_template("posts.html", posts=posts)

@app.route('/posts')
def posts():
    posts = Posts.query.order_by(desc(Posts.date))
    return render_template("posts.html", posts=posts)

@app.route('/adele')
def adele():
    image_folder = os.path.join(app.static_folder, 'uploads', 'adele')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('adele.html', images=images, admin_id=admin_id["adele"])

@app.route('/crafts')
def crafts():
    image_folder = os.path.join(app.static_folder, 'uploads', 'crafts')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('crafts.html', images=images, admin_id=admin_id["crafts"])

@app.route('/samantha')
def samantha():
    image_folder = os.path.join(app.static_folder, 'uploads', 'samantha')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('samantha.html', images=images, admin_id=admin_id["samantha"])

@app.route('/philly')
def philly():
    image_folder = os.path.join(app.static_folder, 'uploads', 'philly')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('philly.html', images=images, admin_id=admin_id["philly"])

@app.route('/redhook')
def redhook():
    image_folder = os.path.join(app.static_folder, 'uploads', 'redhook')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('redhook.html', images=images, admin_id=admin_id["redhook"])

@app.route('/videos', methods=['GET', 'POST'])
def video_gallery():
    if request.method == 'POST':
        if 'video' not in request.files:
            flash('No video file part')
            return redirect(request.url)
        file = request.files['video']
        if file.filename == '':
            flash('No video selected')
            return redirect(request.url)
        if file and allowed_video(file.filename):
            filepath = os.path.join(VIDEO_FOLDER, file.filename)
            file.save(filepath)
            flash(f'Video "{file.filename}" uploaded successfully!')
            return redirect(url_for('video_gallery'))
        else:
            flash('Invalid file type. Allowed: mp4, webm, ogg, mov')
            return redirect(request.url)
    video_files = sorted([f for f in os.listdir(VIDEO_FOLDER) if allowed_video(f)], reverse=True)
    return render_template('video_gallery.html', videos=video_files, admin_id=admin_id["videos"])

@app.route('/delete_video/<filename>', methods=['POST'])
@login_required
def delete_video(filename):
    filepath = os.path.join(VIDEO_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash(f'Video "{filename}" deleted successfully!')
    else:
        flash(f'Video "{filename}" not found.')
    return redirect(url_for('video_gallery'))

@app.route('/delete/<page>/<filename>', methods=['POST'])
@login_required
def delete_file(page, filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER_BASE'], page, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('File deleted successfully', 'success')
    else:
        flash('File not found', 'error')
    return redirect(url_for(page))

@app.route('/upload/<page>', methods=['POST'])
@login_required
def upload_file(page):
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for(page))
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for(page))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER_BASE'], page)
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        flash('File uploaded successfully', 'success')
        return redirect(url_for(page))
    flash('Invalid file type', 'error')
    return redirect(url_for(page))

@app.route('/photo/<page>/<filename>')
def view_photo(page, filename):
    directory = os.path.join(app.config['UPLOAD_FOLDER_BASE'], page)
    return send_from_directory(directory, filename)

@app.route('/posts/<int:id>')
def post(id):
    post = Posts.query.get_or_404(id)
    return render_template('post.html', post=post)

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Posts.query.get_or_404(id)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated!")
        return redirect(url_for('post', id=post.id))
    if current_user.id == post.poster_id:
        form.title.data = post.title
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You Aren't Authorized To Edit This Post...!")
        posts = Posts.query.order_by(desc(Posts.date))
        return render_template("posts.html", posts=posts)

@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        poster = current_user.id
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster)
        form.title.data = ''
        form.content.data = ''
        db.session.add(post)
        db.session.commit()
        flash("Blog Post Submitted Successfully!")
    return render_template("add_post.html", form=form)

@app.route('/date')
def get_current_date():
    favorite_pizza = {"John": "Pepperoni", "Mary": "Cheese", "Tim": "Mushroom"}
    return favorite_pizza

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    if id == current_user.id:
        user_to_delete = Users.query.get_or_404(id)
        name = None
        form = UserForm()
        try:
            db.session.delete(user_to_delete)
            db.session.commit()
            flash("User Deleted Successfully!!")
            our_users = Users.query.order_by(Users.date_added)
            return render_template("add_user.html", form=form, name=name, our_users=our_users)
        except:
            flash("Whoops! There was a problem deleting user, try again")
            return render_template("add_user.html", form=form, name=name, our_users=our_users)
    else:
        flash("Sorry, you can't delete that user!")
        return redirect(url_for('dashboard'), form=form)

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    form = UserForm()
    name_to_update = Users.query.get_or_404(id)
    if request.method == "POST":
        name_to_update.name = request.form['name']
        name_to_update.email = request.form['email']
        name_to_update.favorite_color = request.form['favorite_color']
        name_to_update.username = request.form['username']
        try:
            db.session.commit()
            flash("User Updated Successfully!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
        except:
            flash("Error! Looks like there was a problem...try again!")
            return render_template("update.html", form=form, name_to_update=name_to_update, id=id)
    else:
        return render_template("update.html", form=form, name_to_update=name_to_update, id=id)

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    if form.validate_on_submit():
        user_by_email = Users.query.filter_by(email=form.email.data).first()
        user_by_username = Users.query.filter_by(username=form.username.data).first()
        if user_by_email:
            flash("Email is already registered. Please use a different email or login.", "danger")
            return redirect(url_for('add_user'))
        if user_by_username:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for('add_user'))
        hashed_pw = generate_password_hash(form.password_hash.data, method='pbkdf2:sha256')
        user = Users(
            username=form.username.data,
            name=form.name.data,
            email=form.email.data,
            favorite_color=form.favorite_color.data,
            password_hash=hashed_pw
        )
        db.session.add(user)
        db.session.commit()
        name = form.name.data
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''
        flash("User Added Successfully!", "success")
    our_users = Users.query.order_by(Users.date_added)
    return render_template("add_user.html", form=form, name=name, our_users=our_users)

@app.route('/')
def index():
    first_name = "Eddie"
    stuff = "This is <strong>Bold</strong> Text"
    favorite_pizza = ["Pepperoni", "Cheese", "Mushrooms", 41]
    return render_template("index.html", first_name=first_name, stuff=stuff, favorite_pizza=favorite_pizza)

@app.route('/user/<name>')
def user(name):
    return render_template("user.html", user_name=name)

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password_hash.data
        form.email.data = ''
        form.password_hash.data = ''
        pw_to_check = Users.query.filter_by(email=email).first()
        passed = check_password_hash(pw_to_check.password_hash, password)
    return render_template("test_pw.html", email=email, password=password, pw_to_check=pw_to_check, passed=passed, form=form)

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        print("POST received", request.form)
        message_text = request.form.get('message')
        print("message_text:", message_text)
        if message_text:
            try:
                new_message = ChatMessages(
                    sender_id=current_user.id,
                    message=message_text
                )
                db.session.add(new_message)
                db.session.commit()
                return jsonify({'status': 'success', 'message': message_text, 'username': current_user.username, 'timestamp': new_message.timestamp.strftime('%Y-%m-%d %H:%M:%S')})
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'error': str(e)}), 500
    messages = ChatMessages.query.order_by(ChatMessages.timestamp.asc()).limit(50).all()
    print("Retrieved messages:", [(m.id, m.sender.username, m.message, m.timestamp) for m in messages])
    return render_template('chat.html', messages=messages)

@app.route('/stream')
@login_required
def stream():
    def generate():
        last_id = 0
        while True:
            with app.app_context():
                messages = ChatMessages.query.filter(ChatMessages.id > last_id).order_by(ChatMessages.timestamp.asc()).all()
                for message in messages:
                    last_id = message.id
                    data = {
                        'username': message.sender.username,
                        'message': message.message,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    yield f"data: {json.dumps(data)}\n\n"
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')
'''@app.route('/stream')
@login_required
def stream():
    def generate():
        last_id = 0
        while True:
            # get only new messages since last_id
            new_messages = (ChatMessages.query
                            .filter(ChatMessages.id > last_id)
                            .order_by(ChatMessages.timestamp.asc())
                            .all())
            
            for message in new_messages:
                last_id = message.id  # update pointer
                data = {
                    'username': message.sender.username,
                    'message': message.message,
                    'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # wait before checking again
            time.sleep(1)
    return Response(generate(), mimetype='text/event-stream')

@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form = NamerForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully!")
    return render_template("name.html", name=name, form=form)'''

# Create Models
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.now)
    slug = db.Column(db.String(255))
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500), nullable=True)
    user_type = db.Column(db.String(120))
    admin_type = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default=datetime.now)
    profile_pic = db.Column(db.String(128), nullable=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Posts', backref='poster')
    messages = db.relationship('ChatMessages', backref='sender', lazy=True)  

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Name %r>' % self.name

class ChatMessages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now, nullable=False)


    def __repr__(self):
        return f'<ChatMessage {self.id} from {self.sender.username}>'