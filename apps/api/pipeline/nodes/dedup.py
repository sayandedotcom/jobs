from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pipeline.source_configs import get_source_config
from pipeline.sources.registry import get_source
from pipeline.sources.utils import cosine_similarity
from pipeline.state import PipelineState

from core.database import get_pool

SIMILARITY_THRESHOLD = 0.92


async def dedup_node(state: PipelineState) -> dict:
    from core.config import settings

    pool = await get_pool()
    source_name = state["source_name"]

    source_row = await pool.fetchrow(
        "SELECT id FROM sources WHERE name = $1",
        source_name,
    )
    source_id = source_row["id"] if source_row else None

    config = get_source_config(source_name)
    source = get_source(source_name, **config)

    if source and not source.use_embedding_dedup():
        return await _exact_dedup_only(state, pool, source_id)

    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY,
    )

    new_listings: list[dict] = []
    matched: list[tuple[str, str]] = []
    posts_new = 0

    existing_rows = await pool.fetch(
        """SELECT id, "embeddingText" FROM listings WHERE "createdAt" > NOW() - INTERVAL '30 days'"""
    )
    existing_embeddings = []
    if existing_rows:
        texts = [r["embeddingText"] or "" for r in existing_rows]
        existing_embeddings = await embeddings_model.aembed_documents(texts)

    for post in state["filtered_posts"]:
        if source_id:
            existing = await pool.fetchrow(
                """SELECT id FROM raw_posts WHERE "sourceId" = $1 AND "externalId" = $2""",
                source_id,
                post["external_id"],
            )
        else:
            existing = await pool.fetchrow(
                """SELECT id FROM raw_posts WHERE "externalId" = $1""",
                post["external_id"],
            )
        if existing:
            continue

        posts_new += 1
        embed_text = post["raw_content"][:500]
        new_embedding = await embeddings_model.aembed_query(embed_text)

        best_score = 0.0
        best_listing_id = None
        for i, row in enumerate(existing_rows):
            if i < len(existing_embeddings):
                score = cosine_similarity(new_embedding, existing_embeddings[i])
                if score > best_score:
                    best_score = score
                    best_listing_id = row["id"]

        if best_score >= SIMILARITY_THRESHOLD and best_listing_id:
            matched.append((post["external_id"], best_listing_id))
        else:
            new_listings.append(
                {
                    "post": post,
                    "embedding_text": embed_text,
                }
            )

    return {
        "new_listings": new_listings,
        "matched_listings": matched,
        "posts_new": posts_new,
    }


async def _exact_dedup_only(state: PipelineState, pool, source_id: str | None) -> dict:
    new_listings: list[dict] = []
    posts_new = 0

    for post in state["filtered_posts"]:
        if source_id:
            existing = await pool.fetchrow(
                """SELECT id FROM raw_posts WHERE "sourceId" = $1 AND "externalId" = $2""",
                source_id,
                post["external_id"],
            )
        else:
            existing = await pool.fetchrow(
                """SELECT id FROM raw_posts WHERE "externalId" = $1""",
                post["external_id"],
            )
        if existing:
            continue

        posts_new += 1
        new_listings.append(
            {
                "post": post,
                "embedding_text": None,
            }
        )

    return {
        "new_listings": new_listings,
        "matched_listings": [],
        "posts_new": posts_new,
    }
