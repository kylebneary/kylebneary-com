from flask import Blueprint, render_template

home_bp = Blueprint('home_bp', __name__,
    template_folder='templates')


@home_bp.route('/')
def index():
    print('Request for home page received')
    return render_template('index.html')
