"""Template jinja tests."""

def test_subset_of(value, subset):
    """Check if a variable is a subset."""
    return set(value) >= set(subset)

def test_superset_of(value, superset):
    """Check if a variable is a subset."""
    return set(value) <= set(superset)

def create_builtin_tests():
    """Tests standard for the template rendering."""
    return (
        ('subset', test_subset_of),
        ('superset', test_superset_of),
    )
