import os
from datetime import UTC, datetime

from flask import Blueprint, Flask, Response, render_template

from about_me.about_me import about_bp
from blog.blog import blog_bp, get_blog_posts
from projects.projects import projects_bp

app = Flask(__name__)
app.config["SITE_URL"] = os.environ.get("SITE_URL", "https://www.kylebneary.com").rstrip('/')

app.register_blueprint(about_bp, url_prefix='/about-me')
app.register_blueprint(blog_bp, url_prefix='/blog')
app.register_blueprint(projects_bp, url_prefix='/projects')

# Set up Home page
home_bp = Blueprint('home_bp', __name__,
    template_folder='templates')

@home_bp.route('/')
def index():
    _, featured_posts = get_blog_posts()
    return render_template('index.html', featured_posts=featured_posts,
                           blog_prefix=blog_bp.url_prefix)

app.register_blueprint(home_bp)


@app.context_processor
def inject_site_url():
    return {"site_url": app.config["SITE_URL"], "now": datetime.now(UTC)}


@app.route('/robots.txt')
def robots():
    body = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {app.config['SITE_URL']}/sitemap.xml\n"
    )
    return Response(body, mimetype="text/plain")


@app.route('/sitemap.xml')
def sitemap():
    all_posts, _ = get_blog_posts()
    body = render_template('sitemap.xml', posts=all_posts)
    return Response(body, mimetype="application/xml")


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
