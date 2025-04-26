from flask import Blueprint, render_template

blog_bp = Blueprint('blog_bp', __name__,
    template_folder='templates')


@blog_bp.route('/')
def index():
    print('Request for blog page received')
    return render_template('index.html')
