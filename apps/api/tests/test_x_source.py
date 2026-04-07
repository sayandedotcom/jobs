from datetime import UTC, datetime

import pytest
from pipeline.sources.x import XService


def test_parse_posts_response_builds_raw_post():
    service = XService("token")
    payload = {
        "data": [
            {
                "id": "101",
                "author_id": "1",
                "created_at": "2026-04-07T10:00:00Z",
                "text": "We're hiring a backend engineer",
                "entities": {
                    "urls": [
                        {
                            "expanded_url": "https://jobs.example.com/backend",
                        }
                    ]
                },
                "referenced_tweets": [{"type": "quoted", "id": "202"}],
            }
        ],
        "includes": {
            "users": [
                {"id": "1", "username": "acmejobs", "name": "Acme Jobs"},
                {"id": "2", "username": "acme", "name": "Acme"},
            ],
            "tweets": [
                {
                    "id": "202",
                    "author_id": "2",
                    "text": "Apply now",
                    "entities": {
                        "urls": [
                            {
                                "expanded_url": "https://apply.example.com/role",
                            }
                        ]
                    },
                }
            ],
        },
    }

    posts, reached_boundary = service._parse_posts_response(payload, since=None)

    assert reached_boundary is False
    assert len(posts) == 1
    assert posts[0]["external_id"] == "x_101"
    assert posts[0]["author"] == "acmejobs"
    assert posts[0]["permalink"] == "https://x.com/acmejobs/status/101"
    assert "We're hiring a backend engineer" in posts[0]["raw_content"]
    assert "https://jobs.example.com/backend" in posts[0]["raw_content"]
    assert "Quoted post by @acme: Apply now" in posts[0]["raw_content"]
    assert "https://apply.example.com/role" in posts[0]["raw_content"]


def test_parse_posts_response_filters_older_posts():
    service = XService("token")
    since = datetime(2026, 4, 7, 9, 30, tzinfo=UTC)
    payload = {
        "data": [
            {
                "id": "101",
                "author_id": "1",
                "created_at": "2026-04-07T10:00:00Z",
                "text": "Hiring now",
            },
            {
                "id": "102",
                "author_id": "1",
                "created_at": "2026-04-07T08:00:00Z",
                "text": "Old post",
            },
        ],
        "includes": {
            "users": [{"id": "1", "username": "acmejobs", "name": "Acme Jobs"}]
        },
    }

    posts, reached_boundary = service._parse_posts_response(payload, since=since)

    assert reached_boundary is True
    assert [post["external_id"] for post in posts] == ["x_101"]


def test_parse_posts_response_keeps_link_only_posts():
    service = XService("token")
    payload = {
        "data": [
            {
                "id": "303",
                "author_id": "1",
                "created_at": "2026-04-07T10:00:00Z",
                "text": "",
                "entities": {
                    "urls": [
                        {
                            "expanded_url": "https://jobs.example.com/frontend",
                        }
                    ]
                },
            }
        ],
        "includes": {
            "users": [{"id": "1", "username": "acmejobs", "name": "Acme Jobs"}]
        },
    }

    posts, _ = service._parse_posts_response(payload, since=None)

    assert len(posts) == 1
    assert "URLs: https://jobs.example.com/frontend" in posts[0]["raw_content"]


@pytest.mark.asyncio
async def test_fetch_new_posts_dedupes_search_and_user_results(monkeypatch):
    service = XService("token")
    post = {
        "external_id": "x_101",
        "raw_content": "Text: Hiring now",
        "permalink": "https://x.com/acmejobs/status/101",
        "author": "acmejobs",
        "posted_at": "2026-04-07T10:00:00+00:00",
    }

    async def fake_search(_client, _query, _since):
        return [post]

    async def fake_user(_client, _name, _since, _cache):
        return [post]

    monkeypatch.setattr(service, "_fetch_recent_search", fake_search)
    monkeypatch.setattr(service, "_fetch_user_posts", fake_user)

    posts = await service.fetch_new_posts(
        [
            {"name": "hiring backend", "type": "search"},
            {"name": "acmejobs", "type": "user"},
        ]
    )

    assert posts == [post]


@pytest.mark.asyncio
async def test_fetch_new_posts_returns_empty_without_token():
    service = XService("")

    posts = await service.fetch_new_posts(
        [{"name": "hiring backend", "type": "search"}]
    )

    assert posts == []
