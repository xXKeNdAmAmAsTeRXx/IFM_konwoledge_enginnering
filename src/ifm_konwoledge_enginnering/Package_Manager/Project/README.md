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
