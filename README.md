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

- Python 2.7
- Scipy
- Numpy (should be installed when installing Scipy)
- Tifffile
- Pillow

Installation
------------

1. Change into the location where you want to put the project folder.

    ```bash
    cd ~/path/to/location/
    ```

2. Clone the repository.

    ```bash
    git clone git@github.com:MartinHjelmare/auto_acq.git
    ```

3. Test the program by running it with the -h option to see the usage info.

    ```bash
    python control.py -h
    ```

Upgrading
---------

1. Change into the repository location cloned during installation.
```bash
cd ~/path/to/location/auto-acq/
```
2. Update the repository to the latest version.
```bash
git pull --rebase
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
