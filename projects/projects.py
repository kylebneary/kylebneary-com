import os
from datetime import datetime
from pathlib import Path

import markdown
from flask import Blueprint, render_template

projects_bp = Blueprint('projects_bp', __name__,
    template_folder='templates', url_prefix='/projects')

DATA_DIR = Path('./projects/data')


def _parse_list(metadata, key):
    items = []
    for line in metadata.get(key, []):
        items.extend(item.strip() for item in line.split(',') if item.strip())
    return items


def get_projects():
    """ Get all project entries, most recently dated first. """
    if not DATA_DIR.is_dir():
        return []

    md = markdown.Markdown(extensions=['meta'])
    files = [i for i in DATA_DIR.iterdir() if i.is_file() and i.suffix == '.md']
    projects = []
    for i in sorted(files, key=os.path.getmtime):
        with open(i, 'r', encoding='utf-8') as o:
            text = o.read()
        description = md.convert(text)
        metadata = md.Meta
        md.reset()

        date_str = metadata.get('date', [''])[0]
        try:
            sort_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            sort_date = datetime.min

        projects.append({
            'title': metadata.get('title', [i.stem])[0],
            'summary': metadata.get('summary', [''])[0],
            'description': description,
            'tech': _parse_list(metadata, 'tech'),
            'repo_url': metadata.get('repo_url', [None])[0],
            'live_url': metadata.get('live_url', [None])[0],
            'status': metadata.get('status', ['in-progress'])[0],
            '_sort_date': sort_date,
        })

    projects = sorted(projects, key=lambda p: p['_sort_date'], reverse=True)
    for project in projects:
        del project['_sort_date']
    return projects


@projects_bp.route('/')
def index():
    return render_template('projects/index.html', projects=get_projects())
