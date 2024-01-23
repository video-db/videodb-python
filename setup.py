# package setup
import os
from setuptools import setup, find_packages

ROOT = os.path.dirname(__file__)


# Read in the package version per recommendations from:
# https://packaging.python.org/guides/single-sourcing-package-version/
def get_version():
    with open(os.path.join(ROOT, "videodb", "__init__.py")) as f:
        for line in f.readlines():
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip('''"''')


# read the contents of README file
long_description = open(os.path.join(ROOT, "README.md"), "r", encoding="utf-8").read()


setup(
    name="videodb",
    version=get_version(),
    author="videodb",
    author_email="contact@videodb.io",
    description="VideoDB Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/video-db/videodb-python",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.25.1",
        "backoff>=2.2.1",
        "tqdm>=4.66.1",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
    ],
)
