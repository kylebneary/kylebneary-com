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
    [
        "/", "/blog/", "/about-me/", "/projects/", "/sitemap.xml", "/robots.txt",
        "/blog/feed.xml", "/blog/artificial", "/blog/artificial/feed.xml",
        "/projects/caliper",
    ],
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


def test_artificial_index_includes_only_artificial_posts(client):
    response = client.get("/blog/artificial")
    assert response.status_code == 200
    assert b"About the Premise" in response.data
    assert b"Redesigning This Site with Claude Code" not in response.data


def test_artificial_feed_scoped_to_series(client):
    response = client.get("/blog/artificial/feed.xml")
    assert response.content_type.startswith("application/rss+xml")
    assert b"About the Premise" in response.data
    assert b"Redesigning This Site with Claude Code" not in response.data


def test_artificial_post_shows_series_badge(client):
    response = client.get("/blog/about-the-premise")
    assert b"Artificial series" in response.data


def test_non_artificial_post_has_no_series_badge(client):
    response = client.get("/blog/redesigning-with-claude-code")
    assert b"Artificial series" not in response.data


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


def test_project_detail_renders(client):
    response = client.get("/projects/caliper")
    assert response.status_code == 200
    assert b"Caliper" in response.data


def test_project_index_links_to_detail(client):
    response = client.get("/projects/")
    assert b'href="/projects/caliper"' in response.data


def test_unknown_project_is_404(client):
    response = client.get("/projects/no-such-project")
    assert response.status_code == 404


def test_coming_soon_placeholders_have_no_detail_page(client):
    """Placeholder entries must not get a detail page or an index link."""
    from projects.projects import get_projects

    placeholders = [p for p in get_projects() if p["status"] == "coming-soon"]
    assert placeholders, "expected at least one coming-soon placeholder"
    index = client.get("/projects/").get_data()
    for project in placeholders:
        assert project["has_detail"] is False
        assert client.get(f"/projects/{project['slug']}").status_code == 404
        assert f'href="/projects/{project["slug"]}"'.encode() not in index


def test_sitemap_includes_project_detail(client):
    response = client.get("/sitemap.xml")
    assert b"/projects/caliper" in response.data


def test_post_renders_highlighted_code_and_tables(client):
    response = client.get("/blog/getting-paid-by-robots-x402")
    assert response.status_code == 200
    assert b'<div class="codehilite">' in response.data
    assert b'class="k' in response.data, "code should be syntax highlighted"
    assert b"<table>" in response.data


def test_project_detail_has_toc_wired_to_real_anchors(client):
    """Every TOC link must point at a heading id that exists on the page."""
    import re

    body = client.get("/projects/caliper").get_data(as_text=True)
    assert 'class="page-toc"' in body
    assert '<div class="toc">' in body

    targets = set(re.findall(r'<h[23] id="([^"]+)"', body))
    links = set(re.findall(r'<a href="#([^"]+)">', body))
    assert links, "expected a generated table of contents"
    assert links <= targets, f"dangling TOC links: {sorted(links - targets)}"


def test_project_detail_highlights_code(client):
    body = client.get("/projects/caliper").get_data(as_text=True)
    assert '<div class="codehilite">' in body
    assert 'class="k' in body


def test_project_detail_inlines_diagram(client):
    body = client.get("/projects/caliper").get_data(as_text=True)
    assert 'class="diagram"' in body
    assert 'viewBox="0 0 700 396"' in body


# ---------------------------------------------------------------------------
# Code explorer
# ---------------------------------------------------------------------------

def test_code_index_lists_source_files(client):
    response = client.get("/projects/caliper/code")
    assert response.status_code == 200
    assert b"src/index.ts" in response.data
    assert b"scripts/smoke-test.ts" in response.data


def test_code_index_excludes_lockfile(client):
    """package-lock.json is machine-written and would drown the file list."""
    response = client.get("/projects/caliper/code")
    assert b"package-lock.json" not in response.data


def test_code_file_renders_highlighted_source(client):
    response = client.get("/projects/caliper/code/src/index.ts")
    assert response.status_code == 200
    assert b"codehilite" in response.data
    assert b"paymentMiddleware" in response.data


def test_code_file_has_line_anchors_for_deep_links(client):
    """The write-up links to #L-<n>, so every line needs a matching span id."""
    response = client.get("/projects/caliper/code/src/index.ts")
    assert b'id="L-1"' in response.data
    assert b'id="L-48"' in response.data


def test_write_up_deep_links_resolve(client):
    """Every code-source caption on the write-up must point at a live URL."""
    import re

    page = client.get("/projects/caliper").data.decode("utf-8")
    hrefs = re.findall(r'<p class="code-source"><a href="([^"]+)"', page)
    assert hrefs, "write-up emitted no code-source captions"
    for href in hrefs:
        path, _, fragment = href.partition("#")
        assert client.get(path).status_code == 200, f"dead link: {href}"
        if fragment:
            body = client.get(path).data
            assert f'id="{fragment}"'.encode() in body, f"dead anchor: {href}"


def test_code_rejects_path_traversal(client):
    for attempt in [
        "/projects/caliper/code/../../../main.py",
        "/projects/caliper/code/..%2f..%2fmain.py",
        "/projects/caliper/code/src/../../../requirements.txt",
    ]:
        assert client.get(attempt).status_code in (301, 308, 404)


def test_code_rejects_unknown_file(client):
    assert client.get("/projects/caliper/code/src/nope.ts").status_code == 404


def test_code_404s_for_project_without_mirror(client):
    assert client.get("/projects/coming-soon-1/code").status_code == 404


def test_detail_page_links_to_code_explorer(client):
    response = client.get("/projects/caliper")
    assert b"/projects/caliper/code" in response.data


def test_code_redirects_to_github_when_mirror_missing(client, tmp_path, monkeypatch):
    """
    Cloud Run's build may not initialise submodules, leaving the mirror empty.
    The write-up links into these URLs, so they must reach the real file rather
    than 404. Verified by pointing CODE_DIR at an empty directory.
    """
    from projects import projects

    monkeypatch.setattr(projects, "CODE_DIR", tmp_path)

    index = client.get("/projects/caliper/code")
    assert index.status_code == 302
    assert index.headers["Location"] == (
        "https://github.com/kylebneary/x402-worker-template"
    )

    one_file = client.get("/projects/caliper/code/src/index.ts")
    assert one_file.status_code == 302
    assert one_file.headers["Location"] == (
        "https://github.com/kylebneary/x402-worker-template/blob/main/src/index.ts"
    )
