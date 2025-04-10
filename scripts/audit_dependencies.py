#!/usr/bin/env python3
import subprocess
import json
import sys


def main():
    print("Analyzing Poetry dependencies...")

    # Get the dependency tree
    result = subprocess.run(
        ["poetry", "show", "--tree", "--no-ansi"], capture_output=True, text=True
    )

    tree_output = result.stdout

    # Check for multidict specifically
    print("\nChecking for multidict dependency issues...")
    multidict_result = subprocess.run(
        ["poetry", "show", "--tree", "multidict"], capture_output=True, text=True
    )

    if "multidict" in multidict_result.stdout:
        print("Found multidict in dependencies:")
        print(multidict_result.stdout)
    else:
        print(
            "Direct multidict dependency not found, checking indirect dependencies..."
        )

    # Check what depends on multidict
    deps_result = subprocess.run(
        ["poetry", "show", "--why", "multidict"], capture_output=True, text=True
    )

    if deps_result.returncode == 0:
        print("\nPackages requiring multidict:")
        print(deps_result.stdout)
    else:
        print("\nCould not determine what depends on multidict.")

    print("\nSuggested solutions:")
    print("1. Update your pyproject.toml to relax version constraints")
    print("2. Run 'poetry update multidict' to update to a compatible version")
    print(
        "3. Consider adding an explicit compatible version of multidict to your dependencies"
    )


if __name__ == "__main__":
    main()
