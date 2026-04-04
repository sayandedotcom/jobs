from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pipeline.state import PipelineState

from core.database import get_pool

SIMILARITY_THRESHOLD = 0.92


async def dedup_node(state: PipelineState) -> dict:
    from core.config import settings

    pool = await get_pool()
    embeddings_model = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key=settings.GEMINI_API_KEY,
    )

    new_listings: list[dict] = []
    matched: list[tuple[str, str]] = []
    posts_new = 0

    existing_rows = await pool.fetch(
        "SELECT id, embedding_text FROM listings WHERE created_at > NOW() - INTERVAL '30 days'"
    )
    existing_embeddings = []
    if existing_rows:
        texts = [r["embedding_text"] for r in existing_rows]
        existing_embeddings = await embeddings_model.aembed_documents(texts)

    for post, job in state["extracted_jobs"]:
        existing = await pool.fetchrow(
            "SELECT id FROM raw_posts WHERE external_id = $1",
            post["external_id"],
        )
        if existing:
            continue

        posts_new += 1
        embed_text = f"{job['title']} {job['company']} {job.get('location', '')}"
        new_embedding = await embeddings_model.aembed_query(embed_text)

        best_score = 0.0
        best_listing_id = None
        for i, row in enumerate(existing_rows):
            if i < len(existing_embeddings):
                score = _cosine_similarity(new_embedding, existing_embeddings[i])
                if score > best_score:
                    best_score = score
                    best_listing_id = row["id"]

        if best_score >= SIMILARITY_THRESHOLD and best_listing_id:
            matched.append((post["external_id"], best_listing_id))
        else:
            new_listings.append(
                {
                    "post": post,
                    "job": job,
                    "embedding_text": embed_text,
                }
            )

    return {
        "new_listings": new_listings,
        "matched_listings": matched,
        "posts_new": posts_new,
    }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    mag_a = sum(x * x for x in a) ** 0.5
    mag_b = sum(x * x for x in b) ** 0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
