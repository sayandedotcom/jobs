from langgraph.graph import END, StateGraph

from pipeline.nodes.dedup import dedup_node
from pipeline.nodes.extract import extract_node
from pipeline.nodes.fetch import fetch_node
from pipeline.nodes.filter import filter_node
from pipeline.nodes.store import store_node
from pipeline.state import PipelineState


def create_pipeline() -> StateGraph:
    """Build the LangGraph StateGraph for the generic scan pipeline.

    Linear flow:  fetch → filter → extract → dedup → store → END

    Each node receives PipelineState and returns a partial dict to merge.
    The graph is source-agnostic — the source_name in state determines which
    registered BaseSource is used in the fetch node.
    """
    graph = StateGraph(PipelineState)
    graph.add_node("fetch", fetch_node)
    graph.add_node("filter", filter_node)
    graph.add_node("extract", extract_node)
    graph.add_node("dedup", dedup_node)
    graph.add_node("store", store_node)

    graph.set_entry_point("fetch")
    graph.add_edge("fetch", "filter")
    graph.add_edge("filter", "extract")
    graph.add_edge("extract", "dedup")
    graph.add_edge("dedup", "store")
    graph.add_edge("store", END)

    return graph


async def run_pipeline(source_name: str, scan_run_id: str) -> dict:
    """Compile and invoke the pipeline for a single source scan.

    Args:
        source_name: Must match a registered source (e.g., 'reddit', 'linkedin')
        scan_run_id: DB row ID created by the scan trigger endpoint
    """
    graph = create_pipeline()
    compiled = graph.compile()
    result = await compiled.ainvoke(
        {
            "source_name": source_name,
            "scan_run_id": scan_run_id,
            "sub_sources": [],
            "raw_posts": [],
            "filtered_posts": [],
            "extracted_jobs": [],
            "new_listings": [],
            "matched_listings": [],
            "posts_found": 0,
            "posts_new": 0,
            "jobs_added": 0,
            "errors": 0,
        }
    )
    return result
