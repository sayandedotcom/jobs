import json

from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pipeline.state import ExtractedJob, PipelineState, RawPostData

EXTRACTION_PROMPT = """You are a job posting extraction assistant. Given a post, extract structured job information.

If the post is NOT a job posting (e.g., it's a discussion, question, or meta post), set is_job_posting to false.

For valid job postings, extract:
- title: The job title (e.g., "Senior React Developer")
- company: The company name (use "Not specified" if not mentioned)
- description: A clean summary of the job description and requirements (2-3 paragraphs)
- location: Location or "Remote" if remote (null if not mentioned)
- salary: Salary range if mentioned (null if not)
- job_type: One of "full-time", "part-time", "contract", "freelance", "internship" (null if unclear)
- apply_url: Application URL if provided (null if not)
- is_job_posting: true if this is a job posting, false otherwise

Respond with ONLY a JSON object, no markdown or explanation:

Post content:
{content}"""


async def extract_node(state: PipelineState) -> dict:
    """LangGraph node: uses Gemini 2.0 Flash LLM to extract structured job data from posts.

    Each filtered post is sent individually to the LLM with the extraction prompt.
    The LLM returns JSON which is parsed into ExtractedJob. Only posts where
    is_job_posting=true and title exists are kept.

    Scalability concern: each post is a separate LLM call (sequential).
    For high volume, consider batching or concurrent ainvoke calls with asyncio.gather.
    """
    from core.config import settings

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0,
    )

    extracted: list[tuple[RawPostData, ExtractedJob]] = []
    errors = state["errors"]

    for post in state["filtered_posts"]:
        try:
            message = HumanMessage(
                content=EXTRACTION_PROMPT.format(content=post["raw_content"])
            )
            response = await llm.ainvoke([message])
            text = response.content.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

            data = json.loads(text)
            job: ExtractedJob = {
                "title": data.get("title", ""),
                "company": data.get("company", "Not specified"),
                "description": data.get("description", ""),
                "location": data.get("location"),
                "salary": data.get("salary"),
                "job_type": data.get("job_type"),
                "apply_url": data.get("apply_url"),
                "is_job_posting": data.get("is_job_posting", False),
            }
            if job["is_job_posting"] and job["title"]:
                extracted.append((post, job))
        except Exception:
            errors += 1

    return {"extracted_jobs": extracted, "errors": errors}
