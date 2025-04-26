from flask import Blueprint, render_template

about_bp = Blueprint('about_bp', __name__,
    template_folder='templates')


@about_bp.route('/')
def index():
    print('Request for about me page received')
    return render_template('index.html')
