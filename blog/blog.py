import os
from pathlib import Path
from datetime import datetime
from flask import Blueprint, render_template, url_for
from bs4 import BeautifulSoup
import markdown

blog_bp = Blueprint('blog_bp', __name__,
                    url_prefix='/blog', template_folder='templates',
                    static_folder='static', static_url_path='/blog-static')


def recommended_posts(blog_posts):
    """ 
    Get top three recommended posts
    This will eventually consume more data to make actual recommendations.
    For now, it will just return the three most recent posts.
    """
    return blog_posts[:3]


def get_blog_posts():
    """ Get all blog posts. """
    md = markdown.Markdown(extensions=['meta'])
    files = [i for i in Path('./blog/posts').iterdir() if i.is_file()]
    files = sorted(files, key=os.path.getmtime)
    blog_posts = []
    for i in files:
        url = os.path.basename(i).split('.')[0].replace('_','-')
        with open(i, 'r', encoding='utf-8') as o:
            text = o.read()
        _ = md.convert(text)
        metadata = md.Meta

        try:
            pub_date = datetime.strptime(metadata['publication_date'][0], "%Y-%m-%d")
        except (ValueError, KeyError):
            continue
        else:
            if pub_date < datetime.today():
                pub_date = pub_date.strftime('%B %d, %Y')
                blog_posts.append({'url': url, 'name': metadata['title'][0],
                                   'summary': metadata['summary'][0],
                                   'publication_date': pub_date})

    blog_posts = sorted(blog_posts,
                        key=lambda x: datetime.strptime(x['publication_date'], '%B %d, %Y'),
                        reverse=True)
    featured_blog_posts = recommended_posts(blog_posts)
    return blog_posts, featured_blog_posts


@blog_bp.route('/')
def index():
    """ Blog home page. """
    print('Request for blog page received')
    all_posts, featured_posts = get_blog_posts()
    return render_template('blog/index.html', featured_posts=featured_posts, all_posts=all_posts)


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
    md = markdown.Markdown(extensions=['meta'])
    filename = post_name.replace('-', '_') + '.md'
    with open(f'blog/posts/{filename}', 'r', encoding='utf-8') as i:
        text = i.read()
        post_content = md.convert(text)
    
    # Need to replace image paths to be relative to static folder
    post_content = rewrite_img_src(post_content)
    
    title = md.Meta.get('title', [post_name])[0] if hasattr(md, "Meta") else post_name
    return render_template('blog/post.html', title=title, post_content=post_content,
                           meta=getattr(md, "Meta", {}))
