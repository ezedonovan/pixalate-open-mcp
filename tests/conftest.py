import os

# Set X_API_KEY before any imports to prevent validation errors during collection.
# Module-level imports in the package trigger load_config() which requires this env var.
os.environ.setdefault("X_API_KEY", "test-api-key")
