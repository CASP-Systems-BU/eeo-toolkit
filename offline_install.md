# How to Run on Machines With No Internet

This pipeline was developed to be used on an air-gapped cluster of machines, which for security reasons must be kept offline from the internet. This posed several unique challenges from an installation standpoint, which we solved as follows.

## Requirements
- Access to a machine with internet access (for downloading the necessary files/dependencies)
- A way of transferring data from the machine with internet access to the machines without internet access (e.g an external hard disk, a usb flash drive, etc.)

## Limitations
Since our machines had limited debian packages installed, commands like ```python -m venv venv``` were unable to be run successfully. Additionally, pip could not be directly installed, even by using the official script which base64 encodes the latest version, as this required modifying the global python library, something that our debian based linux distribution would not allow.

Our solution was to use Miniconda, a lightweight package manager that
1. creates a virtual environment, which includes the latest python and pip packages and
2. is installed locally to the user's profile, bypassing the need to modify the globally saved python packages

### step 1 - downloading conda
On the machine with online access download the script for conda install by running the command ```curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh``` if your machine is running on different hardware/OS, you can modify the url to fit your needs. Transfer this script to the offline machines.

### step 2 - install conda
run the install script downloaded, e.g ```sh Miniconda3-latest-Linux-x86_64.sh``` and follow the prompts. You should do this on both the online and offline machines to ensure that both are using the same python/pip versions.

### step 3 - download necessary python package dependencies
we have included these in the file **offline_requirements.txt**

On the online machine: run the following commands
```mkdir wheels && pip download -r offline_requirements.txt -d wheels/```

this pair of commands downloads all the necessary .whl files needed for pip to convert into the required binaries to be run on the machines.

Note that one of the packages also needs setuptools installed, this is done by the command ```pip download setuptools -d wheels```

At this point you can transfer the entire repository (including the wheels folder) from the online machine to the offline machines

### step 4 - installing the python packages
in this repository directory, install all the packages stored in the .whl files with the command ```pip install --no-index --find-links=wheels -r offline_requirements.txt```

you should do this on both the online machine and the offline machines, as you need to be able to run some code on the online machine to complete the next step.

### step 5 - download the OCR models
On the online machine, run ```python3 ./ocr/pipeline/run_pipeline.py``` with the necessary arguments so that the ocr_predictor can be initialized. I would recommend modifying the script by adding a sleep statement at line 119, at which point you can exit the script.

The important thing happening here is that doctr needs to download the models it uses to run ocr. these models are stored in ```~/.cache/doctr/models``` as .pt files. Copy these models over to the offline machines, placing them in the exact same directory

### step 6 - install complete
At this point, if all has gone correctly, you will be able to run the pipeline, and this entire repository, on machines that are not connected to the internet.