# Some tools made with python

> Don't forget to : source ./venv/bin/activate

<!-- markdownlint-disable MD036 -->
_(to create venv :  python3 -m venv venv)_
<!-- markdownlint-enable MD036 -->

To install dependancies

> pip install -r requirements.txt

## Gmail tool

Simple script to check message labels and remove InBox label for message at which a custom label has been added.
Command line parameters can be obtained with:
> python src/google/gmail.py --help

Message cleaning can be done with:
> python src/google/gmail.py --clean_doubled_labeled --burst_mode --dry_run

## App Flask / Check IP

[cf. README.md](src/myip/README.md)
