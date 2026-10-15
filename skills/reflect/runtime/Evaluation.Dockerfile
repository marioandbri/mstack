FROM ghcr.io/astral-sh/uv:0.10.11 AS uv
FROM oven/bun:1.3.14 AS bun
# The builder checks the local base image ID before build; freeze the resulting ID before runs.
FROM mstack-reflect-eval:codex-0.160.0
RUN apt-get update && apt-get install -y --no-install-recommends git=1:2.39.5-0+deb12u3 ca-certificates=20250419~deb12u1 && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /uvx /usr/local/bin/
COPY --from=bun /usr/local/bin/bun /usr/local/bin/bun
RUN uv python install 3.13.2
COPY skills/reflect/runtime/pyproject.toml skills/reflect/runtime/uv.lock /opt/maintenance-runtime/
ENV UV_PROJECT_ENVIRONMENT=/opt/maintenance-runtime/.venv
RUN uv sync --locked --project /opt/maintenance-runtime
ENV PATH=/opt/maintenance-runtime/.venv/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_PYTHON=3.13.2
RUN /opt/maintenance-runtime/.venv/bin/python -c 'from pathlib import Path; script = "#!/bin/sh\nexec /opt/maintenance-runtime/.venv/bin/python \"$@\"\n"; [(p.write_text(script), p.chmod(0o755)) for p in (Path("/usr/local/bin/python"), Path("/usr/local/bin/python3"))]'
RUN /bin/bash -lc 'python --version && python3 -c "import sys,jsonschema,sqlite_vec; assert sys.version.split()[0] == \"3.13.2\"; assert sys.prefix == \"/opt/maintenance-runtime/.venv\""'
