# Package Manager

## Setup
```bash
cd src/ifm_konwoledge_enginnering/Package_Manager/Project
python -m pytest
```

## Usage

The CLI always uses `data/repos/repos/k12/repo_100.json`. It stores the current
environment in `state.txt` next to `manager.py`, so commands can be run from
any working directory. The state is created by the first successful `install`
or `remove` and reused by later commands. Request-file paths are still
resolved relative to the current working directory. See `--help` for command
syntax. Run the commands with a Python environment that has the project
dependencies installed; activate the project virtual environment first if
`python` is not available or does not include Z3.

```bash
python manager.py --help
python manager.py install --help
python manager.py remove --help
python manager.py list --help
python manager.py explain --help
```

### Commands

- `install [REQUESTS] [-r REQUEST]...` reads requests from a file and/or
  `--request` flags. If `state.txt` does not exist, installation starts from
  an empty environment; otherwise the existing environment is updated.
  Successful changes are saved automatically. `--print-axioms` prints
  repository axioms used by the solver. At least one request source is required.
- `remove PACKAGE...` removes one or more packages from the saved environment
  and saves the result. `--autoremove` also removes automatically installed
  packages that are no longer needed.
- `list` displays packages in the saved environment, including their versions
  and whether they are marked `manual`. It does not list every package
  available in the repository.
- `explain [REQUESTS] [-r REQUEST]...` checks requests against the fixed
  repository. For an impossible set it prints a minimal unsatisfiable core
  without changing the saved environment. A failed `install` prints the same
  kind of explanation. At least one request source is required.
- Repository validation warnings are suppressed by default. Add
  `--show-warnings` to `install`, `remove`, `list`, or `explain` to display them
  on stderr; repository validation still runs without the flag.

The state file contains one package per line as `name version [manual]`. The
optional `manual` marker distinguishes explicitly requested packages from
automatically installed dependencies. To start over, remove `state.txt`; the
next successful `install` creates a new state.

### Examples
Run these from the project directory. They use the fixed k12 repository:

```bash
# Install a package into the persistent environment.
printf 'async-generator\n' > /tmp/requests.txt
python manager.py install /tmp/requests.txt

# Install directly without creating a request file.
python manager.py install -r async-generator

# Display the saved environment.
python manager.py list

# Opt in to repository validation warnings.
python manager.py list --show-warnings

# Remove a package; the updated state is saved automatically.
python manager.py remove async-generator
python manager.py list

# Explain the intentionally unsatisfiable Task 4.5 request set.
python manager.py explain data/repos/repos/k12/requests_100.txt

# A failed install prints the same kind of explanation and exits non-zero.
python manager.py install data/repos/repos/k12/requests_100.txt

# Print repository axioms while installing.
python manager.py install /tmp/requests.txt --print-axioms
```

The `requests_100.txt` installation is **expected to fail**; it is the
unsatisfiable Task 4.5 example, not a successful-install demo. The request for
`umbra-io` cannot be resolved in this repository. Use `explain` to see the
minimal core. The `async-generator` request above is a successful example.

Successful commands (including `explain` when it reports an unsatisfiable set)
exit with status `0`. Invalid input and failed installations exit non-zero;
failed operations do not overwrite the saved state.

## Tests
```bash
python -m pytest
```

## Documentation

### Overall idea
This project is a small package manager built with a SAT/SMT solver (Z3).
It models a repository as a knowledge base of Boolean variables and logical
axioms, then uses Z3 to find the best installation plan.

### Main classes
- `Constraint` — one version condition, e.g. `>= 2.0`
- `Atom` — one package plus its constraints
- `Requirement` — OR of atoms (alternatives)
- `VersionInfo` — requires and conflicts for one version
- `Package` — name and all versions
- `Repository` — all packages plus metadata

### Workflow
1. Load repository JSON with `load_repository`
2. Validate and warn with `validate_repository`
3. Build Z3 knowledge base with `build_knowledge_base`
4. Add user requests as constraints
5. Set optimization objectives
6. Solve with Z3
7. Extract installed packages
8. Verify result with `verify`

### Architecture
- `src/package_manager/domain/` — models, versioning rules, errors, and
  solver-independent state verification
- `src/package_manager/use_cases/` — application workflows; `install.py` is
  the public install entry point; empty and stateful install, remove, and
  explain are exposed through the CLI
- `src/package_manager/infrastructure/` — CLI (fixed k12 repository and
  persistent project-local state), file parsing/state I/O, and
  the Z3 knowledge-base adapter under `solver/`
- `tests/` mirrors the `domain/`, `use_cases/`, and `infrastructure/` layers
- `manager.py` — command-line entry point

### Project structure
```text
Project/
├── manager.py
├── examples/
├── experiment.ipynb
├── src/package_manager/
│   ├── domain/
│   │   ├── errors.py
│   │   ├── model.py
│   │   ├── verification.py
│   │   └── versioning.py
│   ├── infrastructure/
│   │   ├── cli.py
│   │   ├── parsing.py
│   │   ├── state.py
│   │   └── solver/
│   │       ├── knowledge_base.py
│   │       └── objective_builders.py
│   └── use_cases/
│       ├── empty_install.py
│       ├── explain.py
│       ├── install.py
│       ├── install_with_state.py
│       └── remove.py
└── tests/
    ├── domain/
    │   ├── test_verification.py
    │   └── test_versioning.py
    ├── infrastructure/
    │   ├── test_apply_state.py
    │   ├── test_knowledge_base.py
    │   ├── test_parsing.py
    │   ├── test_state.py
    │   └── test_cli.py
    └── use_cases/
        ├── test_explain.py
        ├── test_install.py
        ├── test_install_change_plan.py
        ├── test_install_with_state.py
        └── test_remove.py
```
