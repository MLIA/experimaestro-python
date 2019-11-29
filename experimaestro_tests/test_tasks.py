# --- Task and types definitions

import unittest
import os
from pathlib import Path
import logging

from experimaestro import *
from experimaestro.click import cli, TASK_PREFIX

from .utils import TemporaryDirectory, Experiment

# --- Define the tasks

from .tasks import *

# --- Defines the experiment

class MainTest(unittest.TestCase):
    def test_simple(self):
        with Experiment("helloworld"):
            # Submit the tasks
            hello = Say(word="hello").submit()
            world = Say(word="world").submit()

            # Concat will depend on the two first tasks
            concat = Concat(strings=[hello, world]).submit()

            Workspace.waitUntilTaskCompleted()
            self.assertEqual(Path(concat._stdout()).read_text(), "HELLO WORLD\n")
        

if __name__ == '__main__':
    import sys
    logging.warn(sys.path)
    unittest.main()
