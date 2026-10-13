"""Package only the three permitted solution files, never keys or runtime outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from framework.runtime import solution_sources, check_protected
from framework.fp_cases import FP_VERSION

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description="Create the source-only submission ZIP.")
    p.add_argument("--output", type=Path, default=ROOT / "submissions/solution.zip")
    args = p.parse_args()
    if args.output.exists(): p.error("Preserve the earlier submission; choose a fresh output filename.")
    sources = solution_sources(ROOT)
    changes = check_protected(ROOT)
    if changes: print("Restore protected files before submission; review candidates:", changes)
    manifest = dict(project_version=FP_VERSION, files={k:hashlib.sha256(v.encode()).hexdigest() for k,v in sources.items()},
        protected_source_changes=changes, final_grade="Final evaluation reruns submitted source on public + hidden cases; saved local scores are not graded.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
        for name, source in sources.items(): z.writestr(name, source)
        z.writestr("SUBMISSION_MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
    print(args.output)
    print("Included: three solution modules and an automatic manifest. No .env, keys, runs or framework files.")


if __name__ == "__main__": main()
