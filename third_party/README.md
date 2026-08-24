# Third-party dependencies

This directory contains an offline backup of the Python dependencies used by
Pixiv Bulk Downloader.

The packages stored in `packages/` are not part of the application source code
and are not imported directly by PBD. The application normally uses the
packages installed in the Python environment.

This backup preserves a known-working set of dependencies so that the runtime
environment can be reconstructed if the original package repositories or
specific package versions become unavailable.

This backup targets CPython 3.13 on Windows x64.

`requirements-lock.txt` records the exact package versions included in the
backup.

## Offline installation

From the project root:

```powershell
python -m pip install `
    --no-index `
    --find-links .\third_party\packages `
    -r .\third_party\requirements-lock.txt
```

## Playwright

Only the Python Playwright package and its Python dependencies are preserved
here. Google Chrome is not included in this backup.

PBD uses the locally installed Google Chrome browser.