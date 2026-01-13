from main import should_continue, parse_editor_response, construct_creator_prompt, update_feedback_history

# --- Parsing Tests ---

def test_parse_approved():
    response = "DECISION: APPROVED\nFEEDBACK: Good"
    decision, feedback = parse_editor_response(response)
    assert decision == "APPROVED"
    assert feedback == "Good"

def test_parse_rejected():
    response = "DECISION: REJECTED\nFEEDBACK: Too long"
    decision, feedback = parse_editor_response(response)
    assert decision == "REJECTED"
    assert feedback == "Too long"

def test_parse_malformed():
    response = "This is not a valid format"
    decision, feedback = parse_editor_response(response)
    # expect defaults
    assert decision == "REJECTED"
    assert feedback == "Error parsing feedback"

def test_parse_with_whitespace():
    response = "\n  DECISION:   APPROVED  \n   FEEDBACK:   Looks great!  \n"
    decision, feedback = parse_editor_response(response.strip())
    assert decision == "APPROVED"
    assert feedback == "Looks great!"


# --- Routing Tests ---

def test_should_continue_approved():
    state = {"decision": "APPROVED", "retry_count": 0, "max_retries": 5}
    assert should_continue(state) == "approved"

def test_should_continue_rejected_retry():
    state = {"decision": "REJECTED", "retry_count": 2, "max_retries": 5}
    assert should_continue(state) == "rejected"

def test_should_continue_max_retries_reached():
    state = {"decision": "REJECTED", "retry_count": 5, "max_retries": 5}
    assert should_continue(state) == "max_retries"

def test_should_continue_max_retries_exceeded():
    state = {"decision": "REJECTED", "retry_count": 6, "max_retries": 5}
    assert should_continue(state) == "max_retries"

def test_should_continue_custom_max_retries():
    state = {"decision": "REJECTED", "retry_count": 2, "max_retries": 2}
    assert should_continue(state) == "max_retries"

# --- Prompt Construction Tests ---

def test_construct_prompt_first_run():
    prompt = construct_creator_prompt(
        product="Soap", 
        audience="Everyone", 
        retries=0, 
        feedback="", 
        history=[]
    )
    assert "Write a short, punchy" in prompt
    assert "Soap" in prompt
    assert "Everyone" in prompt
    assert "rejected" not in prompt

def test_construct_prompt_retry():
    history = ["Too long", "No emoji"]
    prompt = construct_creator_prompt(
        product="Soap", 
        audience="Everyone", 
        retries=2, 
        feedback="Still no emoji", 
        history=history
    )
    assert "Your previous draft for 'Soap' was rejected" in prompt
    assert "Too long" in prompt
    assert "No emoji" in prompt
    assert "Most Recent Feedback: Still no emoji" in prompt


# --- State Update Tests ---

def test_update_history_adds_feedback():
    history = ["Old error"]
    new_hist = update_feedback_history(history, "New error")
    assert len(new_hist) == 2
    assert new_hist[0] == "Old error"
    assert new_hist[1] == "New error"

def test_update_history_ignores_good():
    history = ["Old error"]
    new_hist = update_feedback_history(history, "Good")
    assert len(new_hist) == 1
    assert new_hist[0] == "Old error" # Should not change

def test_update_history_ignores_empty():
    history = ["Old error"]
    new_hist = update_feedback_history(history, "")
    assert len(new_hist) == 1
    assert new_hist[0] == "Old error"


