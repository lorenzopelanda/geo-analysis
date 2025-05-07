import nox

@nox.session
def tests(session):
    """Execute unit tests with pytest."""
    session.install(".[dev]") 
    session.run("pytest", "tests/unit_tests")