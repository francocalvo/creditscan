# Superflow Justfile
# Common tasks for the Superflow project

# List available recipes
default:
    @just --list

clean:
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    find . -type d -name ".pytest_cache" -exec rm -rf {} +
    find . -type d -name ".coverage" -exec rm -rf {} +
    find . -type d -name "htmlcov" -exec rm -rf {} +
    find . -type d -name ".mypy_cache" -exec rm -rf {} +

garage-bootstrap:
    bash scripts/garage-bootstrap.sh

watch:
    bash scripts/dev-watch.sh
