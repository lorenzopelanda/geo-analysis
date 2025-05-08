# Contributing to GreenTo

Thank you for your interest in contributing to **GreenTo**! Follow this guide to set up the development environment, run tests, and propose changes.

---

## Requirements

Make sure you have the following tools installed:

- **Python 3.10** or higher
- **pip** for package management
- **virtualenv** (optional but recommended)
- **Git**

---

## Setting up the development environment

1. **Clone the repository**:
    ```bash
    git clone https://github.com/lorenzopelanda/geo-analysis.git
    cd geo-analysis
    ```

2. **Create a virtual environment** (optional but recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install project dependencies**:
    ```bash
    pip install -e .
    ```

4. **Install development dependencies** (optional, for contributors):
    ```bash
    pip install .[dev]
    ```
---

## Running tests

We use **pytest** for unit testing and **nox** to automate testing workflows. To run the tests:

1. **Run all tests and checks with nox**:
    ```bash
    nox
    ```

    ```bash
    nox -s tests-3.10
    ```
    
    to test the functions on a specified Python version


2. **Generate a code coverage report**:
    ```bash
    pytest --cov=src tests/
    ```

---

## Type checking

We use **mypy** to ensure type safety and code integrity. Run mypy to check for type errors.

Make sure your code passes all type checks before submitting a pull request.

---

## Code formatting

To maintain a consistent code style, we use **Black** and **isort**. Before submitting a pull request, run the following commands to format the code:

1. **Run Black**:
    ```bash
    black src tests
    ```

2. **Sort imports with isort**:
    ```bash
    isort src tests
    ```
---

## Writing unit tests

For every new function or feature, you must write corresponding unit tests using **pytest**. Place your tests in the `tests/unit_tests/` directory and follow these guidelines:

- Use descriptive test names that explain what the test is verifying.
- Mock external dependencies where necessary using `unittest.mock`.
- Ensure your tests cover edge cases and potential failure scenarios.

Example test structure:
```python
import pytest
from greento.module import function_to_test

def test_function_to_test():
    result = function_to_test(input_data)
    assert result == expected_output
```

---

## Proposing changes

1. **Create a branch for your changes**:
    ```bash
    git checkout -b descriptive-branch-name
    ```

2. **Make the necessary changes** and add tests to cover new features or fixes.

3. **Run the tests** to ensure everything works correctly using **pytest** and **nox**

4. **Create a clear and concise commit**:
    ```bash
    git add .
    git commit -m "Short description of the change"
    ```

5. **Push the branch to the remote repository**:
    ```bash
    git push origin descriptive-branch-name
    ```

6. **Open a pull request** on GitHub and describe the changes you made.

---

## Code guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/) for code style, with the exception of the maximum line length.
- The maximum line length is set to **88 characters**, as configured in the `pyproject.toml` file.
- Use **type hints** to improve code readability and maintainability.
- Write tests for every new feature or bug fix.
- Document your changes in the `CHANGELOG.md` file.

---

## Libraries used

- **pytest**: for unit testing
- **pytest-cov**: for code coverage
- **Black**: for code formatting
- **isort**: for sorting imports
- **mypy**: for type checking
- **nox**: for automating testing workflows

---

Thank you for your interest in GreenTo!