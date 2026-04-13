# Contributing to DisSModel

Thank you for your interest in contributing to DisSModel! We welcome contributions from the community to help improve this project.

## How to Contribute

### Reporting Bugs
If you find a bug, please create a new issue on GitHub. Be sure to include:
- A descriptive title.
- Steps to reproduce the bug.
- Expected behavior vs. actual behavior.
- Your environment details (OS, Python version, DisSModel version).

### Suggesting Enhancements
If you have an idea for a new feature or improvement, please open an issue and tag it as an "enhancement". Explain why the feature would be useful and how it should work.

### Pull Requests
1.  **Fork the repository** and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  Ensure the test suite passes (`pytest`).
4.  Make sure your code follows the project's coding style.
5.  Issue that pull request!

## Development Setup

1.  Clone the repository:
    ```bash
    git clone https://github.com/DisSModel/dissmodel.git
    cd dissmodel
    ```

2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  Install dependencies:
    ```bash
    pip install -e ".[dev]"
    ```

4.  Run tests:
    ```bash
    pytest tests/
    ```

## Coding Standards
- We follow PEP 8 guidelines.
- Use type hints where possible.
- Write docstrings for new functions and classes (NumPy style).

## License
By contributing, you agree that your contributions will be licensed under the MIT License.