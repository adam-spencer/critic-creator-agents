import os
from dotenv import load_dotenv
import operator
from typing import TypedDict, Annotated, Union

# LangChain / LangGraph Imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

"""
TODO
====
  I'm happy with the basic structure of this script, but unhappy with the
  performance.

  I think the issue with the current state is that there's no memory between
  steps: the editor agent doesn't really need memory but the editor needs to
  at least be aware of its past mistakes in order to prevent a loop of errors.

  The current prompts are also drafts, some refinement (+ new rules) would be
  very useful.

"""

# --- 1. Configuration ---

# Load API key from .env file
load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7
)


# --- 2. Define the State ---

class AgentState(TypedDict):
    product_name: str
    target_audience: str
    current_copy: str
    editor_feedback: str
    decision: str  # "APPROVED" or "REJECTED"
    retry_count: int


# --- 3. Define the Nodes (Agents) ---

def creator_agent(state: AgentState):
    """
    The Creator generates ad copy. It checks if there is existing feedback
    to refine the previous attempt.
    """
    product = state["product_name"]
    audience = state["target_audience"]
    feedback = state.get("editor_feedback", "")
    retries = state.get("retry_count", 0)

    # Contextual Prompting
    if retries == 0:
        prompt = (
            f"Write a short, punchy social media ad caption for '{product}'. "
            f"Target audience: {audience}. "
            "Output ONLY the caption text."
        )
    else:
        prompt = (
            f"Your previous draft for '{product}' was rejected.\n"
            f"Feedback: {feedback}\n\n"
            "Please write a NEW caption that fixes these issues. "
            "Output ONLY the caption text."
        )

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "current_copy": response.content.strip(),
        "retry_count": retries + 1
    }


def editor_agent(state: AgentState):
    """
    The Editor reviews the copy against strict rules.
    It outputs a strict format that we can parse with standard Python.
    """
    copy_to_review = state["current_copy"]

    rules = """
    1. Must be under 15 words.
    2. Must contain exactly one emoji.
    3. Must NOT contain hashtags.
    4. Must mention the product name explicitly.
    """

    # We instruct the LLM to use a specific format for easy parsing
    prompt = f"""
    Review this ad copy: "{copy_to_review}"

    Check against these rules:
    {rules}

    Respond in EXACTLY this format:
    DECISION: [APPROVED or REJECTED]
    FEEDBACK: [One sentence explaining the reason if rejected, or "Good" if approved]
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    # --- Standard Library Parsing ---
    # We parse the string response without needing extra libraries
    lines = content.split('\n')
    decision = "REJECTED"  # Default safe state
    feedback = "Error parsing feedback"

    for line in lines:
        if line.startswith("DECISION:"):
            decision = line.replace("DECISION:", "").strip().upper()
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()

    return {
        "decision": decision,
        "editor_feedback": feedback
    }


# --- 4. Define the Router Logic ---

def should_continue(state: AgentState):
    """
    Decides if the loop should continue, stop, or force quit.
    """
    decision = state["decision"]
    retries = state["retry_count"]

    if decision == "APPROVED":
        return "approved"

    # Guardrail: Prevent infinite loops (Standard safety practice)
    if retries >= 5:
        return "max_retries"

    return "rejected"


# --- 5. Build the Graph ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("creator", creator_agent)
workflow.add_node("editor", editor_agent)

# Add Edges
workflow.set_entry_point("creator")
workflow.add_edge("creator", "editor")

# Conditional Edge
workflow.add_conditional_edges(
    "editor",
    should_continue,
    {
        "approved": END,
        "rejected": "creator",
        "max_retries": END
    }
)

# Compile
app = workflow.compile()


# --- 6. Execution Helper ---

def run_workflow(product: str, audience: str):
    print("--- Starting Workflow ---")

    inputs = {
        "product_name": product,
        "target_audience": audience,
        "retry_count": 0,
        "current_copy": "",
        "editor_feedback": "",
        "decision": ""
    }

    # stream() yields events as the graph processes them
    for output in app.stream(inputs):
        for key, value in output.items():
            if key == "creator":
                print(f"\nCREATOR generated draft #{
                      value['retry_count']}:")
                print(f"   \"{value['current_copy']}\"")
            elif key == "editor":
                print("\nEDITOR review:")
                print(f"   Decision: {value['decision']}")
                print(f"   Feedback: {value['editor_feedback']}")

    print("\n--- Workflow Complete ---")

# --- 7. Run Example ---


if __name__ == "__main__":
    # Example that usually requires 1-2 loops to get right
    run_workflow(
        product="Omega 3 Fish Oil",
        audience="Health-conscious Seniors"
    )
