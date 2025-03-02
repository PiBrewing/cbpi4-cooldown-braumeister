# read the contents of your README file
from os import path

from setuptools import setup

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="cbpi4-cooldown-braumeister",
    version="0.0.1.a14",
    description="CraftBeerPi Plugin",
    author="",
    author_email="",
    url="",
    include_package_data=True,
    package_data={
        # If any package contains *.txt or *.rst files, include them:
        "": ["*.txt", "*.rst", "*.yaml"],
        "cbpi4-cooldown-braumeister": ["*", "*.txt", "*.rst", "*.yaml"],
    },
    packages=["cbpi4-cooldown-braumeister"],
    install_requires=["scipy==1.15.2"],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
