from langgraph.graph import END, START, StateGraph

from models import GraphState
from nodes.describe_image import describe_image
from nodes.filter_india import filter_india
from nodes.host_image import host_image
from nodes.lens_search import lens_search
from nodes.merge_dedupe import merge_dedupe
from nodes.rank_output import rank_output
from nodes.shopping_search import shopping_search
from nodes.verify_availability import verify_availability


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("host_image", host_image)
    graph.add_node("lens_search", lens_search)
    graph.add_node("describe_image", describe_image)
    graph.add_node("shopping_search", shopping_search)
    graph.add_node("merge_dedupe", merge_dedupe)
    graph.add_node("filter_india", filter_india)
    graph.add_node("verify_availability", verify_availability)
    graph.add_node("rank_output", rank_output)

    graph.add_edge(START, "host_image")

    # True fan-out: lens_search doesn't need the caption, so it starts
    # alongside describe_image rather than waiting on it.
    graph.add_edge("host_image", "lens_search")
    graph.add_edge("host_image", "describe_image")
    graph.add_edge("describe_image", "shopping_search")

    # merge_dedupe only runs once both branches have finished.
    graph.add_edge("lens_search", "merge_dedupe")
    graph.add_edge("shopping_search", "merge_dedupe")

    graph.add_edge("merge_dedupe", "filter_india")
    graph.add_edge("filter_india", "verify_availability")
    graph.add_edge("verify_availability", "rank_output")
    graph.add_edge("rank_output", END)

    return graph.compile()
