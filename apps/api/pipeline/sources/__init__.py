"""Source auto-registration entry point.

Import every source module here so their @register_source decorators fire.
When adding a new source, add:
    import pipeline.sources.<module>  # noqa: F401
"""

import pipeline.sources.ashbyhq  # noqa: F401
import pipeline.sources.greenhouse  # noqa: F401
import pipeline.sources.hackernews  # noqa: F401
import pipeline.sources.himalayas  # noqa: F401
import pipeline.sources.lever  # noqa: F401
import pipeline.sources.reddit  # noqa: F401
import pipeline.sources.remotefirstjobs  # noqa: F401
import pipeline.sources.remoteok  # noqa: F401
import pipeline.sources.remotive  # noqa: F401
import pipeline.sources.teamtailor  # noqa: F401
import pipeline.sources.workable  # noqa: F401
