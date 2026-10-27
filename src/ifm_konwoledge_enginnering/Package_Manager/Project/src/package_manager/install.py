import json

from package_manager.errors import NoSolutionError
from package_manager.kb import build_knowledge_base, encode_requirement
from package_manager.model import Repository
from package_manager.versioning import parse_requirement
import z3


def install(repo: Repository, request_strings: list[str]) -> list[tuple[str, str]]:
    # Parse Requests
    requests = [parse_requirement(req) for req in request_strings]

    # Build KB
    variables, opt, axioms = build_knowledge_base(repo)

    #Add requirements
    for req in requests:
        opt.add(encode_requirement(req, repo, variables))

    # Package Order
    obsolescence = {}
    for package in repo.packages:
        versions = repo.versions_of(package)
        for idx, version in enumerate(versions):
            obsolescence[(package, str(version))] = idx

    # Expressions to optimize
    requested_pkgs = {atom.package for req in requests for atom in req.alternatives}

    requested_terms = [
        obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
        for (p, v) in variables
        if p in requested_pkgs
    ]
    expr_requested = z3.Sum(requested_terms) if requested_terms else z3.IntVal(0)

    count_terms = [z3.If(v, 1, 0) for v in variables.values()]
    expr_count = z3.Sum(count_terms) if count_terms else z3.IntVal(0)

    other_terms = [
        obsolescence[(p, v)] * z3.If(variables[(p, v)], 1, 0)
        for (p, v) in variables
        if p not in requested_pkgs
    ]
    expr_other = z3.Sum(other_terms) if other_terms else z3.IntVal(0)

    # set optimization
    opt.set(priority="lex")
    opt.minimize(expr_requested)
    opt.minimize(expr_count)
    opt.minimize(expr_other)

    # Solve Request and Repository
    if opt.check() != z3.sat:
        raise NoSolutionError()

    model = opt.model()
    installed = [(p,v) for (p,v), var in variables.items() if z3.is_true(model.eval(var))]

    return installed