auto_acq
========

[ ![License] [license-image] ] [license]
[ ![GitHub Issues] [issues-image] ] [issues]

This project is intended to be used together with the CAM interface of
Leica Microsystem's software LAS AF Matrix screener. The aim is to automate
the confocal image acquisition by controlling the microscope with a client
computer program that connects to the CAM server.

Prerequisites
-------------

- git
- Python 2.7
- Numpy
- Scipy
- Tifffile
- Pillow

Installation
------------

1. Change into the location where you want to put the project folder.

    ```bash
    cd ~/path/to/location/
    ```

2. Download and extract the lastest release.

    ```bash
    wget https://github.com/MartinHjelmare/auto_acq/archive/v0.1.0-alpha.tar.gz
    tar -zxvf v0.1.0-alpha.tar.gz
    ```

3. Test the program by running it with the -h option to see the usage info.

    ```bash
    cd auto_acq-0.1.0-alpha
    python control.py -h
    ```

Usage
-----

Run program with:

```bash
python control.py -i <dir> [options]
```

[issues-image]: http://img.shields.io/github/issues/MartinHjelmare/auto_acq.svg
[issues]: https://github.com/MartinHjelmare/auto_acq/issues

[license-image]: http://img.shields.io/badge/license-GPLv3-blue.svg
[license]: https://www.gnu.org/copyleft/gpl.html
