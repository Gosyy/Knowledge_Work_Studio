# System Dependencies

KW Studio has Python and Node dependencies, but some product workflows also need operating-system packages.
These packages are not optional when the deployment is expected to perform independent Office/PDF rendering.

## Required Office/render stack

The current required Ubuntu/Debian package list is maintained in:

```text
infra/system-packages/ubuntu-render-stack.txt
```

The list includes:

```text
libreoffice-impress
libreoffice-calc
libreoffice-writer
poppler-utils
fontconfig
fonts-dejavu-core
fonts-liberation
```

Why these packages are required:

- `libreoffice-impress` converts generated PPTX decks to PDF for independent render QA.
- `poppler-utils` provides `pdftoppm`, which converts rendered PDFs to PNG images.
- `libreoffice-calc` and `libreoffice-writer` support future first-class XLSX and DOCX Office workflows.
- `fontconfig`, `fonts-dejavu-core`, and `fonts-liberation` make render output more stable across machines and containers.

## Install on Ubuntu/Debian workstations

Use the project-resident installer instead of ad hoc local commands:

```bash
bash scripts/dev/install_system_dependencies_ubuntu.sh
```

The installer:

- reads the package list from `infra/system-packages/ubuntu-render-stack.txt`;
- preserves proxy environment variables for `apt-get`/`sudo` environments;
- writes logs under `<repo>/logs`;
- mirrors output to the terminal;
- archives the log as `.log.tar.gz` and removes the raw `.log`.

Offline/intranet operators should point APT at the approved internal mirror before running the installer.
Do not encode local mirror URLs or profile-specific paths in repository files.

## Validate the installed render stack

After installation, run:

```bash
python scripts/kw_system_dependencies_check.py --repo-root . --validate-render-stack --require-ready --json
```

The validation does not only check that binaries exist.
It creates a small deterministic PPTX, renders it with LibreOffice, converts the result through the Office/PDF path, and verifies that rendered PNG output exists.

## Docker deployment image

The backend deployment image installs the same Office/render stack from `infra/system-packages/ubuntu-render-stack.txt`.
This keeps Docker smoke behavior aligned with workstation validation and avoids treating LibreOffice rendering as a hidden host-machine assumption.
