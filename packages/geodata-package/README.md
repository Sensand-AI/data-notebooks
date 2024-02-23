make sure Setuptools and wheel are both installed.

Using this template package as guide: https://github.com/ArjanCodes/2023-package/blob/main/outline.md

Important keywords/parameters of setuptools to be aware of:
wheel (.whl): A pre-built (zip) binary file, which is ready to be installed, that contains all the necessary information (code itself and metadata) for python package manager to install the package. To create one you should run python setup.py bdist_wheel within the shell. bdist stands for binary distribution.
sdist (.tar.gz) : The source code distribution equivalent to wheel. A tar file (zip) that contains the source code together with the setup.py file, so the user can re-built it. To create a source distribution run python setup.py sdist

To create the wheels/ egg files, navigate to the parent fodler of the package (in this case geodata-package) and run `python setup.py bdist_wheel`. This will create a bunch of stuff and setup the build and dist folders.

To create a source distribution, run `python setup.py sdist` This will also create the `egg-info` folder and files.

Finally, to install locally, you can run:
`pip install .`
Then, use the run.py to play around with the package.