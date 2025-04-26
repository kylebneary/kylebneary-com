from flask import Flask

from home.home import home_bp
from about_me.about_me import about_bp
from blog.blog import blog_bp
from projects.projects import projects_bp

app = Flask(__name__)

app.register_blueprint(home_bp)
#app.register_blueprint(about_bp, url_prefix='/about-me')
#app.register_blueprint(blog_bp, url_prefix='/blog')


if __name__ == '__main__':
    app.run(debug=True)
