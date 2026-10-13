"""Load only approved solution files using the trusted surrounding framework.

The policy receives observed world state and an accounted model interface.
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import types
from contextlib import contextmanager
from uuid import uuid4

EDITABLE_FILES = ("solution/config.py", "solution/prompts.py", "solution/policy.py")


class ObservedWorld:
    def __init__(self, world): self.__world = world
    @property
    def case_id(self): return self.__world.case_id
    @property
    def now(self): return self.__world.now
    @property
    def revision(self): return self.__world.revision
    @property
    def finished(self): return self.__world.finished
    def observe(self): return self.__world.observe()
    def call(self, tool, **arguments): return self.__world.call(tool, **arguments)
    def batch(self, actions): return self.__world.batch(actions)


class ModelAPI:
    """Charge requests in the host ledger; expose no client/key or mutable ledger."""
    def __init__(self, api, case_id):
        self.__api, self.__case_id, self.__episode = api, case_id, uuid4().hex
    @property
    def mode(self): return self.__api.mode
    def json(self, config, instructions, payload, schema, label):
        label = dict(label, case_id=self.__case_id, episode=self.__episode)
        return self.__api.json(config, instructions, payload, schema, label)
    def usage(self):
        rows = [r for r in self.__api.records if r["label"].get("episode") == self.__episode]
        return copy.deepcopy(self.__api.usage(rows))


def solution_sources(path):
    root = Path(path).resolve()
    if root.name == "solution": root = root.parent
    data = {}
    for relative in EDITABLE_FILES:
        file = root / relative
        if file.is_symlink() or not file.is_file():
            raise ValueError("Provide an ordinary file: " + relative)
        text = file.read_text(encoding="utf-8")
        compile(text, relative, "exec")
        data[relative] = text
    return data


@contextmanager
def load_solution(path):
    """Stage only three submitted modules; imports resolve to the trusted framework."""
    sources = solution_sources(path)
    digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    name = "_submitted_solution_" + uuid4().hex
    work_root = Path(__file__).resolve().parents[1] / ".runtime"
    work_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(work_root / "tiktoken"))
    with tempfile.TemporaryDirectory(prefix="ce-policy-", dir=work_root) as tmp:
        directory = Path(tmp)
        for relative, text in sources.items():
            (directory / Path(relative).name).write_text(text)
        package = types.ModuleType(name)
        package.__path__ = [str(directory)]
        sys.modules[name] = package
        try:
            config_module = importlib.import_module(name + ".config")
            policy = importlib.import_module(name + ".policy")
            config = config_module.make_config()
            config["submitted_implementation_sha256"] = digest
            if not callable(policy.solve) or not callable(policy.route):
                raise ValueError("solution/policy.py must define solve and route.")
            def solver(world, api, cfg, route):
                gateway = ModelAPI(api, world.case_id) if api is not None else None
                return policy.solve(ObservedWorld(world), gateway, cfg, route)
            yield config, policy.route, solver, digest, sources
        finally:
            for key in list(sys.modules):
                if key == name or key.startswith(name + "."): sys.modules.pop(key, None)


def check_protected(project):
    root = Path(project)
    manifest = json.loads((root / "RELEASE_MANIFEST.json").read_text())
    changes = []
    for relative, expected in manifest["protected_files"].items():
        file = root / relative
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            changes.append(relative)
    return changes
