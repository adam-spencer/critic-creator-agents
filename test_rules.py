from main import check_deterministic_rules

def test_check_deterministic_rules():
    product = "Omega 3"
    
    # Pass case
    assert check_deterministic_rules("Buy Omega 3 today! 🐟", product) == []

    # Fail: Too long
    long_copy = "This is a very long copy that will surely exceed the fifteen words limit set by the rules 🐟"
    failures = check_deterministic_rules(long_copy, product)
    assert any("too long" in f for f in failures)

    # Fail: No emoji
    failures = check_deterministic_rules("Buy Omega 3 today!", product)
    assert any("exactly one emoji" in f for f in failures)

    # Fail: Too many emojis
    failures = check_deterministic_rules("Buy Omega 3 today! 🐟🐠", product)
    assert any("exactly one emoji" in f for f in failures)
    
    # Fail: Hashtags
    failures = check_deterministic_rules("Buy #Omega3 today! 🐟", product)
    assert any("hashtags" in f for f in failures)

    # Fail: No product name
    failures = check_deterministic_rules("Buy fish oil today! 🐟", product)
    assert any("mention the product name" in f for f in failures)

    print("All deterministic rule tests passed!")


