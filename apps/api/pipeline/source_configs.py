from core.config import settings

SOURCE_CONFIGS: dict[str, dict] = {
    "reddit": {
        "client_id": settings.REDDIT_CLIENT_ID,
        "client_secret": settings.REDDIT_CLIENT_SECRET,
        "user_agent": settings.REDDIT_USER_AGENT,
    },
}


def get_source_config(source_name: str) -> dict:
    return SOURCE_CONFIGS.get(source_name, {})
