import os
import sys
import subprocess

"""
First, attempt to import hit. If that fails, try adding the hit source directory to the path
and try the import again. If that fails, try running "make hit" before importing.
"""

try:
    import hit
except ImportError:
    hit_dir = os.path.join(os.path.dirname(__file__), 'hitsrc')
    sys.path.append(hit_dir)
    try:
        import hit
    except ImportError:
        subprocess.run(['make', 'hit','bindings'], cwd=hit_dir)
        import hit

from hit import TokenType, Token
from app.moose.pyhit.pyhit import Node, load, write, parse, tokenize

