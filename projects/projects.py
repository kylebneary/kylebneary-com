import os
from datetime import UTC, datetime
from pathlib import Path

import markdown
from flask import Blueprint, abort, redirect, render_template
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.util import ClassNotFound

from content import is_published, parse_publication

projects_bp = Blueprint('projects_bp', __name__,
    template_folder='templates', url_prefix='/projects')

DATA_DIR = Path('./projects/data')
CODE_DIR = Path('./projects/code')

# A project's browsable source is a git submodule under CODE_DIR. These never
# appear in the tree: VCS and build noise, plus lockfiles that are
# machine-written rather than authored and would drown the file list.
CODE_SKIP = {'.git', '.gitignore', 'node_modules', '.wrangler', 'dist',
             'package-lock.json'}
MAX_CODE_BYTES = 256 * 1024

MARKDOWN_EXTENSIONS = ['meta', 'fenced_code', 'tables', 'toc', 'codehilite']
MARKDOWN_EXTENSION_CONFIGS = {
    'codehilite': {'guess_lang': False, 'css_class': 'codehilite'},
    'toc': {'toc_depth': '2-3'},
}


def _parse_list(metadata, key):
    items = []
    for line in metadata.get(key, []):
        items.extend(item.strip() for item in line.split(',') if item.strip())
    return items


def _has_detail(html, status):
    """
    True when this project earns its own /projects/<slug> page: it needs a
    real Markdown body, and placeholder ("coming-soon") entries never get one.
    """
    return bool(html and html.strip()) and status != 'coming-soon'


def _new_markdown():
    return markdown.Markdown(extensions=MARKDOWN_EXTENSIONS,
                             extension_configs=MARKDOWN_EXTENSION_CONFIGS)


def _build_project(path, md):
    with open(path, 'r', encoding='utf-8') as handle:
        text = handle.read()
    description = md.convert(text)
    metadata = md.Meta
    toc = getattr(md, 'toc', '')
    md.reset()

    stamp = parse_publication(metadata.get('date', [''])[0])

    status = metadata.get('status', ['in-progress'])[0]

    return {
        'slug': path.stem.replace('_', '-'),
        'title': metadata.get('title', [path.stem])[0],
        'summary': metadata.get('summary', [''])[0],
        'description': description,
        'toc': toc,
        'has_detail': _has_detail(description, status),
        'tech': _parse_list(metadata, 'tech'),
        'repo_url': metadata.get('repo_url', [None])[0],
        'code_dir': metadata.get('code_dir', [None])[0],
        'live_url': metadata.get('live_url', [None])[0],
        'post_url': metadata.get('post_url', [None])[0],
        'status': status,
        'display_date': stamp.strftime('%B %Y') if stamp else None,
        'iso_date': stamp.strftime('%Y-%m-%d') if stamp else None,
        '_stamp': stamp,
    }


def get_projects():
    """ Get all project entries, most recently dated first. """
    if not DATA_DIR.is_dir():
        return []

    md = _new_markdown()
    files = [i for i in DATA_DIR.iterdir() if i.is_file() and i.suffix == '.md']
    projects = [_build_project(i, md) for i in sorted(files, key=os.path.getmtime)]

    # A dated project is withheld until its date passes, which is what makes
    # a project page schedulable. An undated one has nothing to wait for and
    # stays visible, preserving how entries behaved before dates gated
    # anything.
    projects = [p for p in projects
                if p['_stamp'] is None or is_published(p['_stamp'])]

    projects = sorted(
        projects,
        key=lambda p: p['_stamp'] or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    for project in projects:
        del project['_stamp']
    return projects


def code_root(project):
    """ Root of a project's browsable code mirror, or None if it has none. """
    name = project.get('code_dir')
    if not name:
        return None
    root = CODE_DIR / name
    return root if root.is_dir() else None


def get_code_files(root):
    """ Every browsable file under root, as sorted posix-relative paths. """
    files = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if CODE_SKIP.intersection(rel.parts):
            continue
        files.append(rel.as_posix())
    return sorted(files)


def group_by_directory(files):
    """ Group flat paths into (directory, [(name, path)]) pairs for display. """
    groups = {}
    for rel in files:
        directory, _, name = rel.rpartition('/')
        groups.setdefault(directory, []).append((name, rel))
    return sorted(groups.items())


def read_code_file(root, relpath):
    """
    Read one file from the mirror, or None if it isn't readable as source.

    `relpath` arrives from the URL, so it is untrusted: the resolved path is
    confirmed to sit inside the root before anything is read, which stops
    "../.." from walking out of the submodule.
    """
    try:
        resolved = (root / relpath).resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None
    if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
        return None
    if resolved.stat().st_size > MAX_CODE_BYTES:
        return None
    return resolved.read_text(encoding='utf-8', errors='replace')


def highlight_source(source, filename):
    """ Server-side highlighting, with a line number anchor per line. """
    try:
        lexer = get_lexer_for_filename(filename, stripnl=False)
    except ClassNotFound:
        lexer = TextLexer(stripnl=False)
    # linespans (not lineanchors) wraps each line in a span carrying the id,
    # so a deep link like #L-48 can highlight the whole line via :target.
    formatter = HtmlFormatter(cssclass='codehilite', linenos='table',
                              linespans='L', anchorlinenos=True)
    return highlight(source, lexer, formatter)


def get_project(slug):
    """ Get a single project by slug, or None if it doesn't exist. """
    for project in get_projects():
        if project['slug'] == slug:
            return project
    return None


@projects_bp.route('/')
def index():
    return render_template('projects/index.html', projects=get_projects())


@projects_bp.route('/<slug>')
def detail(slug):
    """ Page for a single project write-up. """
    project = get_project(slug)
    if project is None or not project['has_detail']:
        abort(404)
    return render_template('projects/detail.html', project=project,
                           has_code=code_root(project) is not None)


@projects_bp.route('/<slug>/code')
@projects_bp.route('/<slug>/code/<path:filepath>')
def code(slug, filepath=None):
    """ Browsable source for a project, from its vendored code mirror. """
    project = get_project(slug)
    if project is None or not project['has_detail']:
        abort(404)
    root = code_root(project)
    if root is None:
        # The mirror is a git submodule, so it is empty in any checkout that
        # didn't initialise submodules. The write-up links into these URLs, so
        # send visitors to the canonical repo rather than 404ing at them.
        if project['repo_url']:
            target = project['repo_url']
            if filepath:
                target = f"{target}/blob/main/{filepath}"
            return redirect(target, code=302)
        abort(404)

    files = get_code_files(root)
    source = None
    if filepath is not None:
        # Whitelist first: only paths the tree itself offers are readable.
        if filepath not in files:
            abort(404)
        raw = read_code_file(root, filepath)
        if raw is None:
            abort(404)
        source = highlight_source(raw, filepath)

    return render_template('projects/code.html', project=project,
                           groups=group_by_directory(files), files=files,
                           current=filepath, source=source)
