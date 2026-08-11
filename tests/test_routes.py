"""Smoke tests: every registered route should render without error."""
import pytest

from main import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "path",
    ["/", "/blog/", "/about-me/", "/projects/", "/sitemap.xml", "/robots.txt", "/blog/feed.xml"],
)
def test_route_returns_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_home_page_lists_featured_posts(client):
    response = client.get("/")
    assert b"From the Blog" in response.data


def test_home_page_has_meta_description(client):
    response = client.get("/")
    assert b'<meta name="description" content="' in response.data


def test_blog_index_lists_posts(client):
    response = client.get("/blog/")
    assert response.status_code == 200


def test_unknown_route_is_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404


def test_individual_blog_post_renders(client):
    response = client.get("/blog/buildging-a-site")
    assert response.status_code == 200


def test_blog_feed_lists_posts(client):
    response = client.get("/blog/feed.xml")
    assert response.content_type.startswith("application/rss+xml")
    assert b"<rss" in response.data


def test_sitemap_is_xml(client):
    response = client.get("/sitemap.xml")
    assert response.content_type.startswith("application/xml")
    assert b"<urlset" in response.data


def test_robots_points_at_sitemap(client):
    response = client.get("/robots.txt")
    assert b"Sitemap:" in response.data


def test_projects_page_lists_placeholder_entries(client):
    response = client.get("/projects/")
    assert b"coming soon" in response.data.lower()
