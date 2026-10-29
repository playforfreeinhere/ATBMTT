"""Open the application from the repository root."""
from pathlib import Path
import runpy
import sys

if __name__ == '__main__':
    project = Path(__file__).resolve().parent / 'ATBMTT-main' / 'ATBMTT-main'
    sys.path.insert(0, str(project))
    runpy.run_path(str(project / 'run_gui.py'), run_name='__main__')
