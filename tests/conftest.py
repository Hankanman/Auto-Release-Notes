""" This file is used to configure the pytest test runner. It is used to add the src directory to the system path so that the tests can import the modules from the src directory. """

import os

# Append the src directory to the system path
BASE_PATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
