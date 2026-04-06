"""Source auto-registration entry point.

Import every source module here so their @register_source decorators fire.
When adding a new source (e.g., LinkedIn), add:
    import pipeline.sources.linkedin  # noqa: F401
"""

import pipeline.sources.reddit  # noqa: F401
