"""Template jinja tests."""

def is_subset_of(value, subset):
    """Check if a variable is a subset."""
    return set(value) >= set(subset)

def is_superset_of(value, superset):
    """Check if a variable is a superset."""
    return set(value) <= set(superset)

def create_builtin_tests():
    """Tests standard for the template rendering."""
    return (
        ('subset', is_subset_of),
        ('superset', is_superset_of),
    )
