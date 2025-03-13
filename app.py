from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import db, Post, Comment
from datetime import datetime
from functools import wraps
import markdown  # Added for Markdown support

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = '0f9c48316c32823508408963e51b7964'  # Replace with your generated key
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Admin credentials (change these!)
ADMIN_USERNAME = 'ImUrMom'
ADMIN_PASSWORD = 'Jono@5752'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    # Convert content to HTML for preview
    for post in posts:
        post.content_preview = markdown.markdown(post.content, extensions=['nl2br'])[:150]  # Added nl2br extension
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    
    if request.method == 'POST':
        content = request.form['content']
        author = request.form['author']
        
        new_comment = Comment(
            content=content,
            author=author,
            date_posted=datetime.now(),
            post_id=post_id
        )
        
        db.session.add(new_comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
        return redirect(url_for('post', post_id=post_id))
    
    # Convert post content to HTML with Markdown, preserving newlines
    post.content_html = markdown.markdown(post.content, extensions=['nl2br'])  # Added nl2br extension
    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.date_posted.asc()).all()
    return render_template('post.html', post=post, comments=comments)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        subtitle = request.form['subtitle']
        author = request.form['author']
        content = request.form['content']
        
        new_post = Post(
            title=title,
            subtitle=subtitle,
            author=author,
            content=content,
            date_posted=datetime.now()
        )
        
        db.session.add(new_post)
        db.session.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_post.html')

@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        post.title = request.form['title']
        post.subtitle = request.form['subtitle']
        post.author = request.form['author']
        post.content = request.form['content']
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('post', post_id=post.id))
    
    return render_template('edit_post.html', post=post)

@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    Comment.query.filter_by(post_id=post_id).delete()
    db.session.delete(post)
    db.session.commit()
    flash('Post and its comments deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/delete_comment/<int:comment_id>', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    post_id = comment.post_id  # Store post_id to redirect back to the post
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted successfully!', 'success')
    return redirect(url_for('post', post_id=post_id))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)