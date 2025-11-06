 
# FOPS MAIN

## Tool requirements

## The FOPS tool requires a Linux environment with at least 4 GPUs and 400GB RAM and PyTorch installed.
To use it down load to a Linyx machine with at least 20GB space and GPU processors and 200-400GB RAM.
Befotre use check if torch is installed in one of the many ways shown below and install torch in your preferred method.
To check the installed PyTorch version, use one of the following methods:

## 1. Using Python Interpreter:
Open a Python interpreter (e.g., by typing python or python3 in your terminal) and execute the following commands:
Python

import torch
print(torch.__version__)
This will print the installed PyTorch version to your console. If PyTorch was installed with CUDA support, the output will also indicate the CUDA version, e.g., 1.9.0+cu102 means PyTorch version 1.9.0 with CUDA version 10.2.

## 2. From the Terminal (Linux/macOS):
You can directly execute the Python commands from your terminal without entering the interpreter:
Code

python -c "import torch; print(torch.__version__)"

## 3. Using pip (if installed via pip):
If you installed PyTorch using pip, you can use pip show to display package information, including the version:
Code

pip show torch
This command will output details about the torch package, including its version.

## 4. Using conda (if installed via Anaconda/Miniconda):
If you installed PyTorch using conda, you can list installed packages and filter for PyTorch:
Code

conda list -f pytorch
This will display information about the PyTorch package in your current conda environment, including its version. If you are working in a specific conda environment, you can specify it:
Code

conda list -n your_env_name -f pytorch
