# Package Manager

## Setup
```bash
cd src/ifm_konwoledge_enginnering/Package_Manager/Project
python -m pytest
```

## Usage
```bash
python manager.py install requests.txt --repo repo.json
```

### Options
- `--print-axioms` — print example axioms during KB construction
- `--state-out FILE` — write resulting state to file

### Examples
Run from the project directory:

```bash
python manager.py install examples/requests_example.txt --repo examples/repo_example.json
```

Note: `requests_example.txt` contains `app==2.0` and `tool`, which has no solution by design.

For a successful install, create a request file with one solvable request:

```bash
printf 'app\n' > /tmp/requests.txt
python manager.py install /tmp/requests.txt --repo examples/repo_example.json
python manager.py install /tmp/requests.txt --repo examples/repo_example.json --print-axioms
```

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
  the public install entry point and `install_empty.py` implements Task 4
- `src/package_manager/infrastructure/` — CLI, file parsing/state I/O, and
  the Z3 knowledge-base adapter under `solver/`
- `tests/` mirrors the `domain/`, `use_cases/`, and `infrastructure/` layers
- `manager.py` — command-line entry point

Task 6 workflows are not implemented by this structural refactor.
