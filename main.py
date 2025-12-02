from dotenv import load_dotenv
import argparse
import json
from typing import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END


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
    feedback_history: list[str]
    decision: str  # "APPROVED" or "REJECTED"
    retry_count: int
    max_retries: int


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
        # Combine all past feedback
        history_str = "\n".join(state.get("feedback_history", []))
        prompt = (
            f"Your previous draft for '{product}' was rejected.\n"
            f"Past Feedback History:\n{history_str}\n\n"
            f"Most Recent Feedback: {feedback}\n\n"
            "Please write a NEW caption that fixes these issues and respects "
            "ALL past feedback. Output ONLY the caption text."
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
    FEEDBACK: [One sentence explaining the reason if rejected, or "Good" if 
    approved]
    """

    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()

    # Parse response
    lines = content.split('\n')
    decision = "REJECTED"  # Default safe state
    feedback = "Error parsing feedback"

    for line in lines:
        if line.startswith("DECISION:"):
            decision = line.replace("DECISION:", "").strip().upper()
        if line.startswith("FEEDBACK:"):
            feedback = line.replace("FEEDBACK:", "").strip()

    # Append new feedback to history
    current_history = state.get("feedback_history", [])
    if feedback and feedback != "Good":
        current_history.append(feedback)

    return {
        "decision": decision,
        "editor_feedback": feedback,
        "feedback_history": current_history,
        "current_copy": copy_to_review 
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

    # Guardrail: Prevent infinite loops
    max_retries = state.get("max_retries", 5)
    if retries >= max_retries:
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

def run_workflow(product: str, audience: str, verbose: bool = False, max_retries: int = 5):
    if verbose:
        print("--- Starting Workflow ---")

    inputs = {
        "product_name": product,
        "target_audience": audience,
        "retry_count": 0,
        "current_copy": "",
        "editor_feedback": "",
        "feedback_history": [],
        "decision": "",
        "max_retries": max_retries
    }

    # stream() yields events as the graph processes them
    final_state = None
    for output in app.stream(inputs):
        for key, value in output.items():
            final_state = value
            if verbose:
                if key == "creator":
                    print(f"\nCREATOR generated draft #{value['retry_count']}:")
                    print(f"   \"{value['current_copy']}\"")
                elif key == "editor":
                    print("\nEDITOR review:")
                    print(f"   Decision: {value['decision']}")
                    print(f"   Feedback: {value['editor_feedback']}")

    if final_state and final_state.get("decision") == "APPROVED":
        output_json = {
            "adcp_version": "1.0",
            "task": "creative_generation",
            "payload": {
                "product_name": product,
                "target_audience": audience,
                "creative_assets": [
                    {
                        "type": "text_ad",
                        "content": final_state["current_copy"],
                        "metadata": {
                            "length": len(final_state["current_copy"]),
                            "sentiment": "energetic"
                        }
                    }
                ],
                "brand_safety_check": "passed"
            }
        }
        print(json.dumps(output_json, indent=2))
    else:
        # Handle failure case
        print(json.dumps({
            "adcp_version": "1.0",
            "task": "creative_generation",
            "error": "Max retries reached or workflow failed",
             "payload": {
                "brand_safety_check": "failed"
            }
        }, indent=2))


# --- 7. Run Script ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the Critic-Creator Agent Workflow")
    parser.add_argument("--product", type=str,
                        default="Omega 3 Fish Oil", help="Product name")
    parser.add_argument("--audience", type=str,
                        default="Health-conscious Seniors",
                        help="Target audience")
    
    parser.add_argument("-t", "--trace", action="store_true", 
                        help="Enable verbose logging")
    
    parser.add_argument("--max-retries", type=int, default=5, 
                        help="Maximum number of retries")
    
    args = parser.parse_args()

    run_workflow(
        product=args.product,
        audience=args.audience,
        verbose=args.trace,
        max_retries=args.max_retries
    )
