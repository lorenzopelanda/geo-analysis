import nox

@nox.session(python=["3.8", "3.9", "3.10", "3.11"])
def tests(session):
    """Execute unit tests with pytest."""
    session.install(".[dev]") 
    session.run("pytest", "tests/unit_tests")