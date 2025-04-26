from flask import Blueprint, render_template

projects_bp = Blueprint('projects_bp', __name__,
    template_folder='templates')


@projects_bp.route('/')
def index():
    print('Request for projects page received')
    return render_template('index.html')
