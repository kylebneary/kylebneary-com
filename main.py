import os

from flask import Blueprint, Flask, render_template

from about_me.about_me import about_bp
from blog.blog import blog_bp, get_blog_posts
from projects.projects import projects_bp

app = Flask(__name__)

app.register_blueprint(about_bp, url_prefix='/about-me')
app.register_blueprint(blog_bp, url_prefix='/blog')
app.register_blueprint(projects_bp, url_prefix='/projects')

# Set up Home page
home_bp = Blueprint('home_bp', __name__,
    template_folder='templates')

@home_bp.route('/')
def index():
    print('Request for home page received')
    _, featured_posts = get_blog_posts()
    print(featured_posts)
    return render_template('index.html', featured_posts=featured_posts,
                           blog_prefix=blog_bp.url_prefix)

app.register_blueprint(home_bp)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
