from flask import Flask, render_template, flash, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_migrate import Migrate
#from sqlalchemy.orm import DeclarativeBase
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from webforms import LoginForm, PostForm, UserForm, PasswordForm, NamerForm, SearchForm
from flask_ckeditor import CKEditor
from werkzeug.utils import secure_filename
import uuid as uuid
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired

# Create a Flask Instance
app = Flask(__name__)
ckeditor = CKEditor(app)
# Add Database

# Old SQLite DB
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///our_users.db'

# New MySQL DB
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/db_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:3221Redhook#@localhost/our_users'

# Secret Key!
app.config['SECRET_KEY'] = "My Secret Key"
dir


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
#UPLOAD_FOLDER = 'static/uploads/images/'




ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER_BASE'] = os.path.join(BASE_DIR, 'static/uploads')
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads/images')


# Ensure the upload folder exists
#if not os.path.exists(UPLOAD_FOLDER):
    #os.makedirs(UPLOAD_FOLDER)
    
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize The Database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask_Login Stuff
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
        # Get data from submitted form
        ##post.searched = form.searched.data
        post.searched = form.search.data
        # Query the Database
        posts = posts.filter(Posts.content.like('%' + post.searched + '%'))
        posts = posts.order_by(Posts.title).all()
        return render_template("search.html", 
        form=form, 
        ##searched = post.searched,
        search = post.searched,
        posts = posts)

# Create Login Page
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    search_form = SearchForm()  # only include if used in layout
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
        #name_to_update.about_author = request.form['about_author']

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            profile_pic_file = request.files['profile_pic']

            if profile_pic_file and profile_pic_file.filename != '':
                # Secure the filename
                pic_filename = secure_filename(profile_pic_file.filename)

                # Generate a unique name
                pic_name = str(uuid.uuid4()) + "_" + pic_filename

                # Save the file to the uploads folder
                upload_path = os.path.join(app.config['UPLOAD_FOLDER'], pic_name)
                profile_pic_file.save(upload_path)

                # Store just the filename in the database
                name_to_update.profile_pic = pic_name

        try:
            db.session.commit()
            flash("User Updated Successfully!", "success")
            return render_template("dashboard.html", 
                form=form,
                name_to_update=name_to_update,
                id=id)
        except Exception as e:
            flash("Error! There was a problem... try again.", "danger")
            print(e)
            return render_template("dashboard.html", 
                form=form,
                name_to_update=name_to_update,
                id=id)

    return render_template("dashboard.html", 
        form=form,
        name_to_update=name_to_update,
        id=id)

    
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
    post_to_delete = Posts.query.get_or_404(id)
    id = current_user.id
    if id == post_to_delete.poster.id:
        
        try:
            db.session.delete(post_to_delete)
            db.session.commit()
            
            #Return a message
            flash("Blog Post Was Deleted!")
            # Grab all the posts from the database
            posts = Posts.query.order_by(desc(Posts.date))
            return render_template("posts.html", posts=posts)

        except:
            # Return an error message
            flash("Whoops! There was a problem deleting post, try again...")
            
            # Grab all the posts from the database
            posts = Posts.query.order_by(desc(Posts.date))
            return render_template("posts.html", posts=posts)
    else:
        #Return a message
            flash("You Aren't Authorized To Delete That Post!")
            # Grab all the posts from the database
            posts = Posts.query.order_by(desc(Posts.date))
            return render_template("posts.html", posts=posts)

    
@app.route('/posts')
#@login_required
def posts():
    # Grab all the posts from the database
    posts = Posts.query.order_by(desc(Posts.date))
    return render_template("posts.html", posts=posts)

@app.route('/adele')
def adele():
    # Display Adele Gallery
    # Get list of image files in the upload folder
    
    image_folder = os.path.join(app.static_folder, 'uploads', 'adele')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('adele.html', images=images)
    

@app.route('/crafts')
def crafts():
    # Display Adele Crafts
    '''images = [f for f in os.listdir(os.path.join(app.config['UPLOAD_FOLDER_BASE'], 'crafts'))] 
    return render_template('crafts.html', images=images)'''
    
    image_folder = os.path.join(app.static_folder, 'uploads', 'crafts')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('crafts.html', images=images)

@app.route('/samantha')
def samantha():
    # Get list of image files in the upload folder
    '''images = [f for f in os.listdir(os.path.join(app.config['UPLOAD_FOLDER_BASE'], 'samantha'))]  
    return render_template('samantha.html', images=images)'''
    
    image_folder = os.path.join(app.static_folder, 'uploads', 'samantha')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('samantha.html', images=images)

@app.route('/philly')
def philly():
    # Display Philly Gallery
    # Get list of image files in the upload folder
    
    image_folder = os.path.join(app.static_folder, 'uploads', 'philly')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('philly.html', images=images)

@app.route('/redhook')
def redhook():
    # Display Redhook Gallery
    # Get list of image files in the upload folder
    
    image_folder = os.path.join(app.static_folder, 'uploads', 'redhook')
    images = os.listdir(image_folder)
    images = sorted(images, key=lambda x: os.path.getctime(os.path.join(image_folder, x)), reverse=True)
    return render_template('redhook.html', images=images)

    
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

        # Define upload path dynamically
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER_BASE'], page)
        os.makedirs(upload_folder, exist_ok=True)  # Ensure directory exists

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
        #post.author = form.author.data
        #post.slug = form.slug.data
        post.content = form.content.data
        # Update Database
        db.session.add(post)
        db.session.commit()
        flash("Post Has Been Updated!")
        return redirect(url_for('post', id=post.id))
    
    if current_user.id == post.poster_id:
        form.title.data = post.title
        #form.author.data = post.author
        #form.slug.data = post.slug
        form.content.data = post.content
        return render_template('edit_post.html', form=form)
    else:
        flash("You Aren't Authorized To Edit This Post...!")
        posts = Posts.query.order_by(desc(Posts.date))
        return render_template("posts.html", posts=posts)
    
# Add Post page
@app.route('/add-post', methods=['GET', 'POST'])
@login_required
def add_post():
    form = PostForm()
    
    if form.validate_on_submit():
        poster = current_user.id
        #post = Posts(title=form.title.data, content=form.content.data, poster_id=poster, slug=form.slug.data)
        post = Posts(title=form.title.data, content=form.content.data, poster_id=poster)
        # Clear the Form
        form.title.data = ''
        form.content.data = ''
        form.author.data = ''
        #form.slug.data = ''
        
        # Add Post Data to Database
        db.session.add(post)
        db.session.commit()
        # Return a Message
        flash("Blog Post Submitted Successfully!")
    # Redirect to the Webpage
    return render_template("add_post.html", form=form)
#Json Thing
@app.route('/date')
def get_current_date():
    favorite_pizza = {
        "John": "Pepperoni",
        "Mary": "Cheese",
        "Tim": "Mushroom"    
        }
    return favorite_pizza
    #return {"Date": date.today()}    
    


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
            return render_template("add_user.html",
            form=form,
            name=name,
            our_users=our_users)
        except:
        
            flash ("Whoops! There was a problem deleting user, try again")
            return render_template("add_user.html",
            form=form,
            name=name,
            our_users=our_users)
    else:
        flash ("Sorry, you can't delete that user!")
        return redirect(url_for('dashboard'), form=form)
    
# Update Database Record
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
            return render_template("update.html", 
				form=form,
				name_to_update = name_to_update, id=id)
        except:
            flash("Error!  Looks like there was a problem...try again!")
            return render_template("update.html", 
				form=form,
				name_to_update = name_to_update,
                id=id)
    else:
        return render_template("update.html", 
				form=form,
				name_to_update = name_to_update,
				id = id)  
            




@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
    name = None
    form = UserForm()
    
    if form.validate_on_submit():
        # Check for duplicate email
        user_by_email = Users.query.filter_by(email=form.email.data).first()

        # Check for duplicate username
        user_by_username = Users.query.filter_by(username=form.username.data).first()

        if user_by_email:
            flash("Email is already registered. Please use a different email or login.", "danger")
            return redirect(url_for('add_user'))

        if user_by_username:
            flash("Username already exists. Please choose a different one.", "danger")
            return redirect(url_for('add_user'))

        # Hash the password
        hashed_pw = generate_password_hash(form.password_hash.data, method='pbkdf2:sha256')

        # Create new user
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

        # Clear form fields
        form.name.data = ''
        form.username.data = ''
        form.email.data = ''
        form.favorite_color.data = ''
        form.password_hash.data = ''  # Fix: use `.data`

        flash("User Added Successfully!", "success")

    our_users = Users.query.order_by(Users.date_added)

    return render_template("add_user.html",
                        form=form,
                        name=name,
                        our_users=our_users)


# Create a route decorator
@app.route('/')
def index():
    first_name = "Eddie"
    stuff = "This is <strong>Bold</strong> Text"
    favorite_pizza = ["Pepperoni","Cheese","Mushrooms",41]
    return render_template("index.html",
        first_name=first_name,
        stuff=stuff,
        favorite_pizza=favorite_pizza)

# localhost:5000/user/John
@app.route('/user/<name>')

def user(name):
    return render_template("user.html",user_name=name)

# Create Custom Error Pages

# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404

# Internal Server Error
@app.errorhandler(500)
def page_not_found(e):
    return render_template("500.html"), 500

# Create Password Test Page
@app.route('/test_pw', methods=['GET', 'POST'])
def test_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form =  PasswordForm()
    # Validate Form
    if form.validate_on_submit():
        email =  form.email.data
        password = form.password_hash.data
        
        form.email.data = ''
        form.password_hash.data = ''
        # Lookup User by Email Address
        pw_to_check = Users.query.filter_by(email=email).first()
        
        # Check Hashed Password
        passed = check_password_hash(pw_to_check.password_hash,password)

    return render_template("test_pw.html",
        email = email,
        password = password,
        pw_to_check = pw_to_check,
        passed = passed,
        form = form)
    
# Create Name Page
@app.route('/name', methods=['GET', 'POST'])
def name():
    name = None
    form =  NamerForm()
    # Validate Form
    if form.validate_on_submit():
        name =  form.name.data
        form.name.data = ''
        flash("Form Submitted Successfully!")

    return render_template("name.html",
        name = name,
        form = form)
# Create a Blog Post model
class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    content = db.Column(db.Text)
    #author = db.Column(db.String(255))
    #date_posted = db.Column(db.DateTime, default=datetime.now)
    date = db.Column(db.DateTime, default=datetime.now)
    slug = db.Column(db.String(255))
    # Foreign Key To Link Users (refer to primary key of the user)
    poster_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
# Create Model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    favorite_color = db.Column(db.String(120))
    about_author = db.Column(db.Text(500), nullable=True)
    user_type = db.Column(db.String(120))
    date_added = db.Column(db.DateTime, default = datetime.now)
    profile_pic = db.Column(db.String(128), nullable=True)
    # Do some password stuff!
    password_hash = db.Column(db.String(128))
    # User Can Have Many Posts
    posts = db.relationship('Posts', backref='poster')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

# Create A String
    def __repr__(self):
        return '<Name %r>' % self.name
    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    #app.run(host='0.0.0.0', port=5000)
    #app.run()
