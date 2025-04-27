from datetime import datetime
from flask import Blueprint, render_template
import markdown

blog_bp = Blueprint('blog_bp', __name__,
    template_folder='templates')


# Dummy data for demonstration purposes
posts = [
    {
        "title": "Understanding AI and Ethics",
        "link": "/blog/article1",
        "summary": "Exploring the ethical implications of AI technologies and their impact on society.",
        "date": datetime(2025, 4, 25)
    },
    {
        "title": "Machine Learning in Action",
        "link": "/blog/article2",
        "summary": "A hands-on guide to implementing machine learning models in real-world scenarios.",
        "date": datetime(2025, 4, 24)
    },
    {
        "title": "The Future of AI",
        "link": "/blog/article3",
        "summary": "Discussing where AI technology is headed and the future implications for industries.",
        "date": datetime(2025, 4, 23)
    },
    # Additional posts for the directory section
    {
        "title": "The Rise of Quantum Computing",
        "link": "/blog/article4",
        "summary": "How quantum computing is changing the landscape of data processing.",
        "date": datetime(2025, 4, 22)
    },
    {
        "title": "AI and Job Automation",
        "link": "/blog/article5",
        "summary": "Examining the impact of AI on various job sectors and future job opportunities.",
        "date": datetime(2025, 4, 21)
    }
]

def get_featured_posts():
    # Return the first 3 posts for the featured section
    return posts[:3]

def get_all_posts():
    # Return all posts sorted by date in reverse chronological order
    return sorted(posts, key=lambda x: x['date'], reverse=True)

@blog_bp.route('/')
def index():
    print('Request for blog page received')
    featured_posts = get_featured_posts()
    all_posts = get_all_posts()
    return render_template('blog/index.html', featured_posts=featured_posts, all_posts=all_posts)

@blog_bp.route('/<post_name>')
def post(post_name):
    # Find the related file
    filename = post_name.replace('-', '_') + '.md'
    with open(f'blog/posts/{filename}', 'r') as i:
        text = i.read()
        post_content = markdown.markdown(text)
    return render_template('blog/post.html', post_content=post_content)
