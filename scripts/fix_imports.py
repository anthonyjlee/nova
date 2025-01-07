"""Script to fix memory_types imports."""

import os
import fileinput
import sys

def fix_imports(directory):
    """Fix memory_types imports in Python files."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with fileinput.FileInput(filepath, inplace=True) as file:
                    for line in file:
                        # Replace the import while preserving the imported names
                        if "from ...memory.memory_types import" in line:
                            # Extract what's being imported
                            imports = line.split("import")[1].strip()
                            # Create new import line
                            new_line = f"from ...core.types.memory_types import {imports}\n"
                            sys.stdout.write(new_line)
                        else:
                            sys.stdout.write(line)

if __name__ == "__main__":
    fix_imports("src/nia/agents/specialized")
