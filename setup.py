#! /usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="canonicalwebteam.cookie_service",
    version="1.0.5",
    author="Canonical webteam",
    author_email="webteam@canonical.com",
    url="https://github.com/canonical/canonicalwebteam.cookie-service",
    description=("Flask extension to integrate with shared cookie service."),
    packages=find_packages(),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    install_requires=["Flask>=1.0.2", "requests>=2.20.0"],
    license="LGPL-2.1"
)
