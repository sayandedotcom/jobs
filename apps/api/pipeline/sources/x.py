from contextlib import suppress
from datetime import UTC, datetime
from typing import Any

import httpx
from pipeline.sources.base import BaseSource
from pipeline.sources.registry import register_source
from pipeline.state import RawPostData


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None

    with suppress(ValueError, TypeError):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

    for fmt in (
        "%a %b %d %H:%M:%S %z %Y",
        "%a, %d %b %Y %H:%M:%S %z",
    ):
        with suppress(ValueError):
            return datetime.strptime(value, fmt)

    return None


@register_source
class XService(BaseSource):
    API_BASE = "https://api.x.com/2"
    PAGE_SIZE = 100
    MAX_PAGES = 5
    TWEET_FIELDS = "author_id,created_at,entities,referenced_tweets,public_metrics"
    USER_FIELDS = "username,name"
    EXPANSIONS = "author_id,referenced_tweets.id,referenced_tweets.id.author_id"

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    def get_source_name(self) -> str:
        return "x"

    async def fetch_new_posts(
        self,
        sub_sources: list[dict],
        since: datetime | None = None,
    ) -> list[RawPostData]:
        if not self.bearer_token:
            return []

        seen_ids: set[str] = set()
        posts: list[RawPostData] = []
        user_cache: dict[str, tuple[str, str | None]] = {}

        async with httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Accept": "application/json",
            },
        ) as client:
            for sub in sub_sources:
                name = str(sub.get("name", "")).strip()
                if not name:
                    continue

                sub_type = sub.get("type", "search")
                if sub_type == "user":
                    fetched = await self._fetch_user_posts(
                        client, name, since, user_cache
                    )
                else:
                    fetched = await self._fetch_recent_search(client, name, since)

                for post in fetched:
                    if post["external_id"] in seen_ids:
                        continue
                    seen_ids.add(post["external_id"])
                    posts.append(post)

        return posts

    async def _fetch_recent_search(
        self,
        client: httpx.AsyncClient,
        query: str,
        since: datetime | None,
    ) -> list[RawPostData]:
        normalized_query = self._normalize_search_query(query)
        if not normalized_query:
            return []

        params = self._common_params()
        params["query"] = normalized_query
        return await self._fetch_pages(
            client,
            f"{self.API_BASE}/tweets/search/recent",
            params,
            since,
            token_param="next_token",
        )

    async def _fetch_user_posts(
        self,
        client: httpx.AsyncClient,
        name: str,
        since: datetime | None,
        user_cache: dict[str, tuple[str, str | None]],
    ) -> list[RawPostData]:
        user_id, username = await self._resolve_user(client, name, user_cache)
        if not user_id:
            return []

        return await self._fetch_pages(
            client,
            f"{self.API_BASE}/users/{user_id}/tweets",
            self._common_params(),
            since,
            username_hint=username,
            token_param="pagination_token",
        )

    async def _fetch_pages(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
        since: datetime | None,
        username_hint: str | None = None,
        token_param: str = "pagination_token",
    ) -> list[RawPostData]:
        posts: list[RawPostData] = []
        next_token: str | None = None
        pages_fetched = 0

        while pages_fetched < self.MAX_PAGES:
            request_params = dict(params)
            if next_token:
                request_params[token_param] = next_token

            payload = await self._get_json(client, url, request_params)
            if not payload:
                break

            fetched, reached_boundary = self._parse_posts_response(
                payload,
                since,
                username_hint=username_hint,
            )
            posts.extend(fetched)

            meta = payload.get("meta")
            if not isinstance(meta, dict):
                break

            next_token = meta.get("next_token")
            if not next_token or reached_boundary:
                break

            pages_fetched += 1

        return posts

    async def _resolve_user(
        self,
        client: httpx.AsyncClient,
        name: str,
        cache: dict[str, tuple[str, str | None]],
    ) -> tuple[str | None, str | None]:
        normalized = name.strip().lstrip("@")
        if not normalized:
            return None, None

        cache_key = normalized.lower()
        if cache_key in cache:
            return cache[cache_key]

        if normalized.isdigit():
            cache[cache_key] = (normalized, None)
            return cache[cache_key]

        payload = await self._get_json(
            client,
            f"{self.API_BASE}/users/by/username/{normalized}",
            {"user.fields": self.USER_FIELDS},
        )
        if not payload:
            return None, None

        data = payload.get("data")
        if not isinstance(data, dict):
            return None, None

        user_id = data.get("id")
        username = data.get("username")
        if not user_id:
            return None, None

        resolved = (
            str(user_id),
            str(username).lstrip("@") if username else None,
        )
        cache[cache_key] = resolved
        return resolved

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        url: str,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return None

        with suppress(ValueError):
            data = resp.json()
            if isinstance(data, dict):
                return data

        return None

    def _common_params(self) -> dict[str, Any]:
        return {
            "max_results": self.PAGE_SIZE,
            "tweet.fields": self.TWEET_FIELDS,
            "user.fields": self.USER_FIELDS,
            "expansions": self.EXPANSIONS,
        }

    def _normalize_search_query(self, query: str) -> str:
        normalized = " ".join(query.split())
        if normalized and "is:retweet" not in normalized:
            return f"{normalized} -is:retweet"
        return normalized

    def _parse_posts_response(
        self,
        payload: dict[str, Any],
        since: datetime | None,
        username_hint: str | None = None,
    ) -> tuple[list[RawPostData], bool]:
        data = payload.get("data")
        if not isinstance(data, list):
            return [], False

        includes = payload.get("includes")
        include_users = includes.get("users") if isinstance(includes, dict) else []
        include_posts = includes.get("tweets") if isinstance(includes, dict) else []
        user_map = self._build_lookup(include_users)
        post_map = self._build_lookup(include_posts)

        posts: list[RawPostData] = []
        reached_boundary = False

        for item in data:
            if not isinstance(item, dict):
                continue

            created_at = _parse_datetime(str(item.get("created_at", "")))
            if since and created_at and created_at < since:
                reached_boundary = True
                continue

            post = self._build_post(
                item,
                user_map,
                post_map,
                username_hint=username_hint,
                created_at=created_at,
            )
            if post is not None:
                posts.append(post)

        return posts, reached_boundary

    def _build_post(
        self,
        item: dict[str, Any],
        user_map: dict[str, dict[str, Any]],
        post_map: dict[str, dict[str, Any]],
        username_hint: str | None,
        created_at: datetime | None,
    ) -> RawPostData | None:
        post_id = item.get("id")
        if not post_id:
            return None

        author_id = str(item.get("author_id", ""))
        author = user_map.get(author_id, {})
        username = author.get("username") or (
            username_hint.lstrip("@") if username_hint else None
        )
        display_name = author.get("name")
        text = str(item.get("text", "")).strip()
        urls = self._extract_urls(item)
        has_content = bool(text or urls)

        raw_parts: list[str] = []
        if username:
            raw_parts.append(f"Author: @{username}")
        elif display_name:
            raw_parts.append(f"Author: {display_name}")
        if text:
            raw_parts.append(f"Text: {text}")
        if urls:
            raw_parts.append(f"URLs: {', '.join(urls)}")

        for reference in item.get("referenced_tweets") or []:
            if not isinstance(reference, dict):
                continue

            referenced = post_map.get(str(reference.get("id", "")))
            if not referenced:
                continue

            label = self._reference_label(reference.get("type"))
            referenced_author = user_map.get(str(referenced.get("author_id", "")), {})
            referenced_username = referenced_author.get("username")
            if referenced_username:
                label = f"{label} by @{referenced_username}"

            referenced_text = str(referenced.get("text", "")).strip()
            referenced_urls = self._extract_urls(referenced)
            details: list[str] = []
            if referenced_text:
                details.append(referenced_text)
            if referenced_urls:
                details.append(f"URLs: {', '.join(referenced_urls)}")
            if details:
                has_content = True
                raw_parts.append(f"{label}: {' | '.join(details)}")

        if not has_content:
            return None

        permalink = (
            f"https://x.com/{username}/status/{post_id}"
            if username
            else f"https://x.com/i/web/status/{post_id}"
        )

        metrics = item.get("public_metrics") or {}

        return {
            "external_id": f"x_{post_id}",
            "raw_content": "\n".join(raw_parts),
            "permalink": permalink,
            "author": username or display_name or None,
            "posted_at": created_at.isoformat() if created_at else None,
            "metadata": {
                "retweet_count": metrics.get("retweet_count", 0),
                "like_count": metrics.get("like_count", 0),
                "reply_count": metrics.get("reply_count", 0),
                "quote_count": metrics.get("quote_count", 0),
                "username": username,
                "display_name": display_name,
            },
        }

    def _build_lookup(self, items: Any) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        if not isinstance(items, list):
            return lookup

        for item in items:
            if not isinstance(item, dict):
                continue
            item_id = item.get("id")
            if item_id:
                lookup[str(item_id)] = item

        return lookup

    def _extract_urls(self, item: dict[str, Any]) -> list[str]:
        entities = item.get("entities")
        if not isinstance(entities, dict):
            return []

        urls: list[str] = []
        for entry in entities.get("urls") or []:
            if not isinstance(entry, dict):
                continue
            url = (
                entry.get("expanded_url")
                or entry.get("unwound_url")
                or entry.get("url")
            )
            if url and url not in urls:
                urls.append(str(url))

        return urls

    def _reference_label(self, ref_type: Any) -> str:
        if ref_type == "quoted":
            return "Quoted post"
        if ref_type == "replied_to":
            return "Reply context"
        if ref_type == "retweeted":
            return "Reposted post"
        return "Referenced post"
