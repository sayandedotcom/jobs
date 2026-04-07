from langgraph.graph import END, StateGraph

from pipeline.nodes.dedup import dedup_node
from pipeline.nodes.fetch import fetch_node
from pipeline.nodes.filter import filter_node
from pipeline.nodes.store import store_node
from pipeline.state import PipelineState


def create_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("fetch", fetch_node)
    graph.add_node("filter", filter_node)
    graph.add_node("dedup", dedup_node)
    graph.add_node("store", store_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "filter")
    graph.add_edge("filter", "dedup")
    graph.add_edge("dedup", "store")
    graph.add_edge("store", END)

    return graph


async def run_pipeline(source_name: str, scan_run_id: str) -> dict:
    graph = create_pipeline()
    compiled = graph.compile()
    result = await compiled.ainvoke(
        {
            "source_name": source_name,
            "scan_run_id": scan_run_id,
            "sub_sources": [],
            "raw_posts": [],
            "filtered_posts": [],
            "new_listings": [],
            "matched_listings": [],
            "posts_found": 0,
            "posts_new": 0,
            "jobs_added": 0,
            "errors": 0,
        }
    )
    return result
