from setuptools import find_packages, setup

import versioneer

with open("README.md", "r") as fp:
    LONG_DESCRIPTION = fp.read()

setup(
    name="omni_archive",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Simon-Martin Schroeder",
    author_email="sms@informatik.uni-kiel.de",
    description="A generic archive reader and writer for various archive formats.",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/moi90/omni_archive",
    packages=find_packages(),
    install_requires=[],
    python_requires=">=3.7",
    extras_require={
        "test": [
            # Pytest
            "pytest",
            "pytest-cov",
        ],
        "docs": [
            "sphinx >= 1.4",
            "sphinx_rtd_theme",
            "sphinx-autodoc-typehints>=1.10.0",
        ],
        "dev": ["black"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
    ],
)
