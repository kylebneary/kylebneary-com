import os
from pathlib import Path

import markdown
from bs4 import BeautifulSoup
from flask import Blueprint, Response, abort, render_template, url_for

from content import is_published, parse_publication

blog_bp = Blueprint('blog_bp', __name__,
                    url_prefix='/blog', template_folder='templates',
                    static_folder='static', static_url_path='/blog-static')

WORDS_PER_MINUTE = 200
MARKDOWN_EXTENSIONS = ['meta', 'fenced_code', 'tables', 'toc', 'codehilite']
MARKDOWN_EXTENSION_CONFIGS = {
    'codehilite': {'guess_lang': False, 'css_class': 'codehilite'},
}
ARTIFICIAL_TAG = 'artificial'


def recommended_posts(blog_posts):
    """
    Get top three recommended posts
    This will eventually consume more data to make actual recommendations.
    For now, it will just return the three most recent posts.
    """
    return blog_posts[:3]


def _parse_tags(metadata):
    tags = []
    for line in metadata.get('tags', []):
        tags.extend(tag.strip() for tag in line.split(',') if tag.strip())
    return tags


def _is_artificial(tags):
    return ARTIFICIAL_TAG in (tag.lower() for tag in tags)


def _reading_time(html):
    word_count = len(BeautifulSoup(html, "html.parser").get_text().split())
    return max(1, round(word_count / WORDS_PER_MINUTE))


def _first_image(html):
    soup = BeautifulSoup(html, "html.parser")
    img = soup.find("img")
    if img and img.get("src", "").startswith("images/"):
        return url_for("blog_bp.static", filename=img["src"])
    return None


def get_blog_posts():
    """ Get all blog posts. """
    md = markdown.Markdown(extensions=MARKDOWN_EXTENSIONS,
                          extension_configs=MARKDOWN_EXTENSION_CONFIGS)
    files = [i for i in Path('./blog/posts').iterdir() if i.is_file()]
    files = sorted(files, key=os.path.getmtime)
    blog_posts = []
    for i in files:
        url = os.path.basename(i).split('.')[0].replace('_','-')
        with open(i, 'r', encoding='utf-8') as o:
            text = o.read()
        html = md.convert(text)
        metadata = md.Meta
        md.reset()

        pub_date = parse_publication(metadata.get('publication_date', [''])[0])
        if not is_published(pub_date):
            continue

        tags = _parse_tags(metadata)
        blog_posts.append({
            'url': url,
            'name': metadata['title'][0],
            'summary': metadata['summary'][0],
            'publication_date': pub_date.strftime('%B %d, %Y'),
            'iso_date': pub_date.strftime('%Y-%m-%d'),
            'rfc822_date': pub_date.strftime('%a, %d %b %Y %H:%M:%S %z'),
            'tags': tags,
            'is_artificial': _is_artificial(tags),
            'reading_time': _reading_time(html),
            'image': _first_image(html),
            '_sort_date': pub_date,
        })

    blog_posts = sorted(blog_posts, key=lambda x: x['_sort_date'], reverse=True)
    for entry in blog_posts:
        del entry['_sort_date']
    featured_blog_posts = recommended_posts(blog_posts)
    return blog_posts, featured_blog_posts


@blog_bp.route('/')
def index():
    """ Blog home page. """
    all_posts, featured_posts = get_blog_posts()
    return render_template('blog/index.html', featured_posts=featured_posts, all_posts=all_posts)


@blog_bp.route('/feed.xml')
def feed():
    """ RSS feed of all blog posts. """
    all_posts, _ = get_blog_posts()
    body = render_template('blog/feed.xml', posts=all_posts)
    return Response(body, mimetype="application/rss+xml")


@blog_bp.route('/artificial')
def artificial_index():
    """ Landing page for the Artificial series (AI ethics posts). """
    all_posts, _ = get_blog_posts()
    posts = [entry for entry in all_posts if entry['is_artificial']]
    return render_template('blog/artificial.html', posts=posts)


@blog_bp.route('/artificial/feed.xml')
def artificial_feed():
    """ RSS feed scoped to the Artificial series. """
    all_posts, _ = get_blog_posts()
    posts = [entry for entry in all_posts if entry['is_artificial']]
    body = render_template(
        'blog/feed.xml', posts=posts,
        feed_title='Artificial',
        feed_description='AI ethics in both directions, from Kyle Neary.',
        feed_link=url_for('blog_bp.artificial_index'),
        feed_self=url_for('blog_bp.artificial_feed'),
    )
    return Response(body, mimetype="application/rss+xml")


def rewrite_img_src(html):
    """ Rewrite image src paths to be relative to static folder. """
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if src.startswith("images/"):
            img["src"] = url_for("blog_bp.static", filename=src)
    return str(soup)


@blog_bp.route('/<post_name>')
def post(post_name):
    """ Page for single blog post. """
    # Find the related file
    md = markdown.Markdown(extensions=MARKDOWN_EXTENSIONS,
                          extension_configs=MARKDOWN_EXTENSION_CONFIGS)
    filename = post_name.replace('-', '_') + '.md'
    with open(f'blog/posts/{filename}', 'r', encoding='utf-8') as i:
        text = i.read()
        post_content = md.convert(text)

    reading_time = _reading_time(post_content)
    image = _first_image(post_content)

    # Need to replace image paths to be relative to static folder
    post_content = rewrite_img_src(post_content)

    meta = getattr(md, "Meta", {})

    # A scheduled post isn't published just because nobody linked to it: the
    # URL is guessable from the filename, so gate the post route too.
    pub_date = parse_publication(meta.get('publication_date', [''])[0])
    if not is_published(pub_date):
        abort(404)

    title = meta.get('title', [post_name])[0]
    summary = meta.get('summary', [''])[0]
    publication_date = pub_date.strftime('%Y-%m-%d')
    display_date = pub_date.strftime('%B %d, %Y')

    tags = _parse_tags(meta)
    return render_template('blog/post.html', title=title, summary=summary,
                           post_content=post_content, meta=meta,
                           publication_date=publication_date, display_date=display_date,
                           tags=tags, reading_time=reading_time,
                           image=image, post_name=post_name,
                           is_artificial=_is_artificial(tags))
