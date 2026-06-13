"""Compatibility wrapper for running the packaged web app directly.

The actual FastAPI application lives in local_perplex.ui.web.app so static
assets and templates resolve correctly when installed as a package.
"""

from local_perplex.ui.web.app import app, main


if __name__ == "__main__":
    main()
