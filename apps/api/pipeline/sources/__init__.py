"""Source auto-registration entry point.

Import every source module here so their @register_source decorators fire.
When adding a new source, add:
    import pipeline.sources.<module>  # noqa: F401
"""

import pipeline.sources.arbeitnow  # noqa: F401
import pipeline.sources.ashbyhq  # noqa: F401
import pipeline.sources.authenticjobs  # noqa: F401
import pipeline.sources.greenhouse  # noqa: F401
import pipeline.sources.hackernews  # noqa: F401
import pipeline.sources.himalayas  # noqa: F401
import pipeline.sources.jobicy  # noqa: F401
import pipeline.sources.lever  # noqa: F401
import pipeline.sources.reddit  # noqa: F401
import pipeline.sources.recruitee  # noqa: F401
import pipeline.sources.remotefirstjobs  # noqa: F401
import pipeline.sources.remotewlb  # noqa: F401
import pipeline.sources.remoteok  # noqa: F401
import pipeline.sources.remotive  # noqa: F401
import pipeline.sources.smartrecruiters  # noqa: F401
import pipeline.sources.smashingjobs  # noqa: F401
import pipeline.sources.teamtailor  # noqa: F401
import pipeline.sources.weworkremotely  # noqa: F401
import pipeline.sources.workable  # noqa: F401
import pipeline.sources.workingnomads  # noqa: F401
import pipeline.sources.x  # noqa: F401
