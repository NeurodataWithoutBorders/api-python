from setuptools import setup
# from distutils.core import setup

setup(
    name = 'nwb',
    version = '1.0.6',
    url='https://github.com/NeurodataWithoutBorders/api-python',
    author='Jeff Teeters and Keith Godfrey',
    author_email='jteeters@berkeley.edu',
    description = 'Python API for Neurodata Without Borders (NWB) format',
    packages = ['nwb'],
    install_requires = ['h5py', 'jsonschema']
    )

