from flask import Blueprint, render_template

legal_bp = Blueprint('legal_bp', __name__,
    template_folder='templates', url_prefix='/legal')


@legal_bp.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')


@legal_bp.route('/terms')
def terms():
    return render_template('legal/terms.html')
