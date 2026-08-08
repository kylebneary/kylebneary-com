"""Smoke tests: every registered route should render without error."""
import pytest

from main import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize("path", ["/", "/blog/", "/about-me/", "/projects/"])
def test_route_returns_ok(client, path):
    response = client.get(path)
    assert response.status_code == 200


def test_home_page_lists_featured_posts(client):
    response = client.get("/")
    assert b"Featured Posts" in response.data


def test_blog_index_lists_posts(client):
    response = client.get("/blog/")
    assert response.status_code == 200


def test_unknown_route_is_404(client):
    response = client.get("/this-page-does-not-exist")
    assert response.status_code == 404


def test_individual_blog_post_renders(client):
    response = client.get("/blog/buildging-a-site")
    assert response.status_code == 200
