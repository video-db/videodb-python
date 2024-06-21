# package setup
import os
from setuptools import setup, find_packages

ROOT = os.path.dirname(os.path.abspath(__file__))


# Read in the package version per recommendations from:
# https://packaging.python.org/guides/single-sourcing-package-version/

about_path = os.path.join(ROOT, "videodb", "__about__.py")
about = {}
with open(about_path) as fp:
    exec(fp.read(), about)


# read the contents of README file
long_description = open(os.path.join(ROOT, "README.md"), "r", encoding="utf-8").read()


setup(
    name=about["__title__"],
    version=about["__version__"],
    author=about["__author__"],
    author_email=about["__email__"],
    description="VideoDB Python SDK",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url=about["__url__"],
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.1",
        "backoff>=2.2.1",
        "tqdm>=4.66.1",
    ],
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: Apache Software License",
    ],
)
