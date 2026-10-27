#!/usr/bin/env python3
"""Run the CPU LIME-to-propagator CLI from a source checkout."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'python'))
from lqcd_cpu.propagator import main

if __name__ == '__main__':
    main()
