import os, sys
# Make the project root importable so `import agent.graph` etc. work under pytest.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
