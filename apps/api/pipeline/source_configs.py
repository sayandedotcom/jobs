from core.config import settings

# Central config for all source constructors.
# Each key must match the source's get_source_name() return value and the 'sources' DB table.
# When adding a new source, add its env-var-backed kwargs here.
SOURCE_CONFIGS: dict[str, dict] = {
    "reddit": {
        "client_id": settings.REDDIT_CLIENT_ID,
        "client_secret": settings.REDDIT_CLIENT_SECRET,
        "user_agent": settings.REDDIT_USER_AGENT,
    },
    "hackernews": {},
    "greenhouse": {},
    "lever": {},
    "ashbyhq": {},
    "workable": {},
}


def get_source_config(source_name: str) -> dict:
    return SOURCE_CONFIGS.get(source_name, {})
