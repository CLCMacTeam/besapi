
import os
import subprocess

# set working directory to folder this file is in:
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# set working directory to src folder in parent folder
os.chdir("../src")

import besapi
import bescli

print(f"besapi version: {besapi.__version__}")

if os.name == 'nt':
    subprocess.run('CMD /C python -m besapi ls clear ls conf "query number of bes computers" exit', check=True)
