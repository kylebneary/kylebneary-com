"""Smoke tests: every registered route should render without error."""
import pytest

from main import app


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.fixture()
def preview_client(monkeypatch):
    """
    A client that sees future-dated content.

    Tests of the Caliper showcase exercise its machinery, not its schedule --
    without this they would flip to failing the moment its publication date
    moves into the future.
    """
    monkeypatch.setenv("SHOW_UNPUBLISHED", "1")
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.mark.parametrize(
    "path",
    [
        "/", "/blog/", "/about-me/", "/projects/", "/sitemap.xml", "/robots.txt",
        "/blog/feed.xml", "/blog/artificial", "/blog/artificial/feed.xml",
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


def test_projects_page_lists_placeholder_entries(preview_client):
    response = preview_client.get("/projects/")
    assert b"coming soon" in response.data.lower()


def test_project_detail_renders(preview_client):
    response = preview_client.get("/projects/caliper")
    assert response.status_code == 200
    assert b"Caliper" in response.data


def test_project_index_links_to_detail(preview_client):
    response = preview_client.get("/projects/")
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


def test_sitemap_includes_project_detail(preview_client):
    response = preview_client.get("/sitemap.xml")
    assert b"/projects/caliper" in response.data


def test_post_renders_highlighted_code_and_tables(preview_client):
    response = preview_client.get("/blog/getting-paid-by-robots-x402")
    assert response.status_code == 200
    assert b'<div class="codehilite">' in response.data
    assert b'class="k' in response.data, "code should be syntax highlighted"
    assert b"<table>" in response.data


def test_project_detail_has_toc_wired_to_real_anchors(preview_client):
    """Every TOC link must point at a heading id that exists on the page."""
    import re

    body = preview_client.get("/projects/caliper").get_data(as_text=True)
    assert 'class="page-toc"' in body
    assert '<div class="toc">' in body

    targets = set(re.findall(r'<h[23] id="([^"]+)"', body))
    links = set(re.findall(r'<a href="#([^"]+)">', body))
    assert links, "expected a generated table of contents"
    assert links <= targets, f"dangling TOC links: {sorted(links - targets)}"


def test_project_detail_highlights_code(preview_client):
    body = preview_client.get("/projects/caliper").get_data(as_text=True)
    assert '<div class="codehilite">' in body
    assert 'class="k' in body


def test_project_detail_inlines_diagram(preview_client):
    body = preview_client.get("/projects/caliper").get_data(as_text=True)
    assert 'class="diagram"' in body
    assert 'viewBox="0 0 700 396"' in body


# ---------------------------------------------------------------------------
# Code explorer
# ---------------------------------------------------------------------------

def test_code_index_lists_source_files(preview_client):
    response = preview_client.get("/projects/caliper/code")
    assert response.status_code == 200
    assert b"src/index.ts" in response.data
    assert b"scripts/smoke-test.ts" in response.data


def test_code_index_excludes_lockfile(preview_client):
    """package-lock.json is machine-written and would drown the file list."""
    response = preview_client.get("/projects/caliper/code")
    assert b"package-lock.json" not in response.data


def test_code_file_renders_highlighted_source(preview_client):
    response = preview_client.get("/projects/caliper/code/src/index.ts")
    assert response.status_code == 200
    assert b"codehilite" in response.data
    assert b"paymentMiddleware" in response.data


def test_code_file_has_line_anchors_for_deep_links(preview_client):
    """The write-up links to #L-<n>, so every line needs a matching span id."""
    response = preview_client.get("/projects/caliper/code/src/index.ts")
    assert b'id="L-1"' in response.data
    assert b'id="L-48"' in response.data


def test_write_up_deep_links_resolve(preview_client):
    """Every code-source caption on the write-up must point at a live URL."""
    import re

    page = preview_client.get("/projects/caliper").data.decode("utf-8")
    hrefs = re.findall(r'<p class="code-source"><a href="([^"]+)"', page)
    assert hrefs, "write-up emitted no code-source captions"
    for href in hrefs:
        path, _, fragment = href.partition("#")
        assert preview_client.get(path).status_code == 200, f"dead link: {href}"
        if fragment:
            body = preview_client.get(path).data
            assert f'id="{fragment}"'.encode() in body, f"dead anchor: {href}"


def test_code_rejects_path_traversal(preview_client):
    for attempt in [
        "/projects/caliper/code/../../../main.py",
        "/projects/caliper/code/..%2f..%2fmain.py",
        "/projects/caliper/code/src/../../../requirements.txt",
    ]:
        assert preview_client.get(attempt).status_code in (301, 308, 404)


def test_code_rejects_unknown_file(preview_client):
    assert preview_client.get("/projects/caliper/code/src/nope.ts").status_code == 404


def test_code_404s_for_project_without_mirror(preview_client):
    assert preview_client.get("/projects/coming-soon-1/code").status_code == 404


def test_detail_page_links_to_code_explorer(preview_client):
    response = preview_client.get("/projects/caliper")
    assert b"/projects/caliper/code" in response.data


def test_code_redirects_to_github_when_mirror_missing(preview_client, tmp_path, monkeypatch):
    """
    Cloud Run's build may not initialise submodules, leaving the mirror empty.
    The write-up links into these URLs, so they must reach the real file rather
    than 404. Verified by pointing CODE_DIR at an empty directory.
    """
    from projects import projects

    monkeypatch.setattr(projects, "CODE_DIR", tmp_path)

    index = preview_client.get("/projects/caliper/code")
    assert index.status_code == 302
    assert index.headers["Location"] == (
        "https://github.com/kylebneary/x402-worker-template"
    )

    one_file = preview_client.get("/projects/caliper/code/src/index.ts")
    assert one_file.status_code == 302
    assert one_file.headers["Location"] == (
        "https://github.com/kylebneary/x402-worker-template/blob/main/src/index.ts"
    )


# ---------------------------------------------------------------------------
# Scheduled publishing
# ---------------------------------------------------------------------------

@pytest.fixture()
def scheduled_post(tmp_path_factory):
    """Write a post with a given stamp, yield its url, then remove it."""
    from pathlib import Path

    created = []

    def make(stamp, name="zz_scheduled_probe"):
        path = Path("blog/posts") / f"{name}.md"
        path.write_text(
            f"title: Scheduled Probe\n"
            f"summary: A post used to test scheduling.\n"
            f"publication_date: {stamp}\n"
            f"tags: test\n\nBody text.\n",
            encoding="utf-8",
        )
        created.append(path)
        return name.replace("_", "-")

    yield make
    for path in created:
        path.unlink(missing_ok=True)


@pytest.fixture()
def scheduled_project():
    """Write a project with a given stamp, yield its slug, then remove it."""
    from pathlib import Path

    created = []

    def make(stamp, name="zz_scheduled_project"):
        path = Path("projects/data") / f"{name}.md"
        path.write_text(
            f"title: Scheduled Project\n"
            f"summary: A project used to test scheduling.\n"
            f"status: shipped\n"
            f"date: {stamp}\n\nBody text.\n",
            encoding="utf-8",
        )
        created.append(path)
        return name.replace("_", "-")

    yield make
    for path in created:
        path.unlink(missing_ok=True)


def _stamp(**delta):
    from datetime import datetime as dt
    from datetime import timedelta

    from content import site_timezone

    return (dt.now(site_timezone()) + timedelta(**delta)).strftime("%Y-%m-%d %H:%M")


# -- the parser ------------------------------------------------------------

def test_parse_publication_accepts_bare_date():
    from content import parse_publication

    stamp = parse_publication("2026-09-15")
    assert (stamp.year, stamp.month, stamp.day) == (2026, 9, 15)
    assert (stamp.hour, stamp.minute) == (0, 0)
    assert stamp.tzinfo is not None


def test_parse_publication_accepts_date_and_time():
    from content import parse_publication

    for text in ["2026-09-15 09:30", "2026-09-15T09:30"]:
        stamp = parse_publication(text)
        assert (stamp.hour, stamp.minute) == (9, 30), text


def test_parse_publication_honours_explicit_offset():
    from content import parse_publication

    stamp = parse_publication("2026-09-15T09:30-05:00")
    assert stamp.utcoffset().total_seconds() == -5 * 3600


def test_parse_publication_rejects_garbage():
    from content import parse_publication

    for text in ["", "not a date", "2026-13-45", None]:
        assert parse_publication(text) is None


def test_bare_stamp_uses_site_timezone(monkeypatch):
    from content import parse_publication

    monkeypatch.setenv("SITE_TZ", "America/New_York")
    assert parse_publication("2026-07-01 12:00").utcoffset().total_seconds() == -4 * 3600
    monkeypatch.setenv("SITE_TZ", "UTC")
    assert parse_publication("2026-07-01 12:00").utcoffset().total_seconds() == 0


# -- blog posts ------------------------------------------------------------

def test_future_post_is_hidden_everywhere(client, scheduled_post):
    url = scheduled_post(_stamp(hours=6))

    assert b"Scheduled Probe" not in client.get("/blog/").data
    assert b"Scheduled Probe" not in client.get("/blog/feed.xml").data
    assert b"Scheduled Probe" not in client.get("/").data
    assert b"Scheduled Probe" not in client.get("/sitemap.xml").data
    # Guessable URL, so the post route has to refuse it too.
    assert client.get(f"/blog/{url}").status_code == 404


def test_past_post_is_visible(client, scheduled_post):
    url = scheduled_post(_stamp(hours=-1))

    assert b"Scheduled Probe" in client.get("/blog/").data
    assert client.get(f"/blog/{url}").status_code == 200


def test_scheduling_is_precise_to_the_minute(client, scheduled_post):
    """Same calendar day, either side of now — the time must decide."""
    url = scheduled_post(_stamp(minutes=5))
    assert client.get(f"/blog/{url}").status_code == 404

    url = scheduled_post(_stamp(minutes=-5))
    assert client.get(f"/blog/{url}").status_code == 200


def test_show_unpublished_reveals_scheduled_post(client, scheduled_post, monkeypatch):
    url = scheduled_post(_stamp(days=30))
    assert client.get(f"/blog/{url}").status_code == 404

    monkeypatch.setenv("SHOW_UNPUBLISHED", "1")
    assert client.get(f"/blog/{url}").status_code == 200
    assert b"Scheduled Probe" in client.get("/blog/").data


def test_existing_date_only_posts_still_publish(client):
    """Every post already in the repo is date-only; none may regress."""
    response = client.get("/blog/")
    for title in [b"About the Premise", b"Redesigning This Site with Claude Code"]:
        assert title in response.data


def test_feed_pubdate_carries_real_time(client):
    body = client.get("/blog/feed.xml").data
    assert b"00:00:00 GMT" not in body
    assert b"<pubDate>" in body


# -- projects --------------------------------------------------------------

def test_future_project_is_hidden_everywhere(client, scheduled_project):
    slug = scheduled_project(_stamp(hours=6))

    assert b"Scheduled Project" not in client.get("/projects/").data
    assert b"Scheduled Project" not in client.get("/sitemap.xml").data
    assert client.get(f"/projects/{slug}").status_code == 404
    assert client.get(f"/projects/{slug}/code").status_code == 404


def test_past_project_is_visible(client, scheduled_project):
    slug = scheduled_project(_stamp(hours=-1))

    assert b"Scheduled Project" in client.get("/projects/").data
    assert client.get(f"/projects/{slug}").status_code == 200


def test_undated_project_stays_visible(client, scheduled_project):
    """Undated entries have nothing to wait for and must not vanish."""
    slug = scheduled_project("")
    assert client.get(f"/projects/{slug}").status_code == 200


def test_caliper_and_placeholders_unaffected(preview_client):
    response = preview_client.get("/projects/")
    assert b"Caliper" in response.data
    assert b"coming soon" in response.data.lower()


def test_caliper_and_its_post_publish_together():
    """
    The write-up and its companion post are cross-linked, so one appearing
    without the other would ship a dead link in both directions. Asserted
    against their stamps rather than the clock, so this holds before and
    after publication.
    """
    from datetime import timedelta
    from pathlib import Path

    from content import is_published, parse_publication

    def stamp_of(path, key):
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}:"):
                return parse_publication(line.split(":", 1)[1].strip())
        raise AssertionError(f"no {key} in {path}")

    project = stamp_of("projects/data/caliper.md", "date")
    post = stamp_of("blog/posts/getting_paid_by_robots_x402.md", "publication_date")

    assert project is not None and post is not None
    assert project == post, "showcase and post must share one publication moment"

    assert not is_published(project, now=project - timedelta(minutes=1))
    assert is_published(project, now=project)
    assert is_published(post, now=post + timedelta(minutes=1))
