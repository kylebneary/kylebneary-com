"""
Shared helpers for dated Markdown content (blog posts and projects).

Publication stamps in front-matter gate visibility: content dated in the
future is withheld until that moment passes. Since content is re-read from
disk on every request and nothing is cached, a scheduled item appears on its
own once the time arrives — no deploy, no cron job, nothing that has to fire
correctly at the moment of publication.
"""
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# Stamps without an explicit offset are wall-clock times in this zone, so
# "09:00" means 9am where the author is. Cloud Run runs in UTC, which is
# precisely why this can't be left to the server's local time.
DEFAULT_TZ = 'America/Chicago'


def site_timezone():
    """
    The zone bare publication stamps are interpreted in.

    Falls back to UTC rather than raising: a base image without a tz database
    would otherwise take down every page that reads dated content, which is
    all of them.
    """
    for name in (os.environ.get('SITE_TZ', DEFAULT_TZ), DEFAULT_TZ):
        try:
            return ZoneInfo(name)
        except (ZoneInfoNotFoundError, ValueError):
            continue
    return timezone.utc


def show_unpublished():
    """
    True when future-dated content should be shown anyway.

    Set SHOW_UNPUBLISHED=1 locally to preview scheduled content before its
    date. Production leaves it unset.
    """
    return os.environ.get('SHOW_UNPUBLISHED', '').lower() in {'1', 'true', 'yes'}


def parse_publication(value):
    """
    Parse a front-matter publication stamp into an aware datetime.

    Accepts a bare date ("2026-09-15", meaning midnight), a date and time
    ("2026-09-15 09:30" or "2026-09-15T09:30"), or either with an explicit
    offset ("2026-09-15T09:30-05:00"). Anything without an offset is read as
    local wall-clock time in the site timezone. Returns None if unparseable,
    which callers treat as "not dated".
    """
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.strip())
    except (ValueError, TypeError):
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=site_timezone())
    return stamp


def is_published(stamp, now=None):
    """ True once `stamp` has passed. An undated stamp is never published. """
    if stamp is None:
        return False
    if show_unpublished():
        return True
    return stamp <= (now or datetime.now(site_timezone()))
