import os
from datetime import UTC, datetime

from flask import Blueprint, Flask, Response, redirect, render_template, request

from about_me.about_me import about_bp
from blog.blog import blog_bp, get_blog_posts
from legal.legal import legal_bp
from projects.projects import get_projects, projects_bp

app = Flask(__name__)
app.config["SITE_URL"] = os.environ.get("SITE_URL", "https://www.kylebneary.com").rstrip('/')

app.register_blueprint(about_bp, url_prefix='/about-me')
app.register_blueprint(blog_bp, url_prefix='/blog')
app.register_blueprint(projects_bp, url_prefix='/projects')
app.register_blueprint(legal_bp, url_prefix='/legal')


@app.before_request
def enforce_https():
    """Redirect plain-HTTP requests to HTTPS.

    Cloud Run terminates TLS in front of the app and sets X-Forwarded-Proto,
    so request.is_secure is never true directly; this is a defense-in-depth
    guard for any path that reaches the app over HTTP (e.g. a domain mapping
    that doesn't force it upstream). Skipped under TESTING/debug so the test
    client (which never sets the header) isn't redirected.
    """
    if app.config.get("TESTING") or app.debug:
        return
    if request.headers.get("X-Forwarded-Proto", "http") == "https":
        return
    return redirect(request.url.replace("http://", "https://", 1), code=301)

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
    projects = [p for p in get_projects() if p['has_detail']]
    body = render_template('sitemap.xml', posts=all_posts, projects=projects)
    return Response(body, mimetype="application/xml")


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
