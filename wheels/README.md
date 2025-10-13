This directory is populated by `tools/env/dependency_doctor.py` during CI to cache wheels built from `requirements.txt`.
Binary wheel artifacts are intentionally excluded from source control; use the dependency doctor script (with
`--wheelhouse-only`) to refresh the cache locally when needed.
