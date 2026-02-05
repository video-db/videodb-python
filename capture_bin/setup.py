from setuptools import setup, Distribution

class BinaryDistribution(Distribution):
    """Forces the distribution to be platform-specific."""
    def has_ext_modules(foo):
        return True

VERSION = "0.2.4"

setup(
    name="videodb-capture-bin",
    version=VERSION,
    author="VideoDB",
    description="Binary container for VideoDB Capture runtime",
    packages=["videodb_capture_bin"],
    package_data={
        "videodb_capture_bin": ["bin/**/*"],
    },
    include_package_data=True,
    distclass=BinaryDistribution,
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires=">=3.8",
)
