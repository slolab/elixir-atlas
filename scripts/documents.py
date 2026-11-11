import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from graph.extraction import EXTRACTIONS
from graph.paths import PROJECT_ROOT

paths = sorted({path for extraction in EXTRACTIONS for pattern in extraction.files for path in PROJECT_ROOT.glob(pattern)})
print("\n".join(path.relative_to(PROJECT_ROOT).as_posix() for path in paths if not path.name.endswith(".biotope.yaml")))
