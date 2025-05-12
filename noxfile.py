from __future__ import annotations

from pathlib import Path

import nox


@nox.session(python=["3.10", "3.11", "3.12", "3.13"])
def tests(session: nox.Session) -> None:
    env = {
        "POETRY_VIRTUALENVS_PATH": str(Path(session.virtualenv.bin).parent),
    }

    session.run_install("poetry", "install", external=True, env=env)

    session.run("coverage", "run", "-m", "pytest", external="error")
    session.run("coverage", "report")
    session.run("coverage", "xml")
