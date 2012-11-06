__all__ = []

# Import all attributes in config submodules into this module...
import os
for filename in os.listdir(os.path.dirname(__file__)):
    if filename != '__init__.py' and filename[-3:] == '.py':
        exec "from %s import *" % filename[:-3]
del filename
del os
