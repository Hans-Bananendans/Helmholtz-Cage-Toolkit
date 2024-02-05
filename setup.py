from setuptools import setup, find_packages

setup(
    name="helmholtz_cage_toolkit",
    version="0.2.0",
    description="A toolkit for large Helmholtz cage test setups, primarily aimed at testing spacecraft.",
    author="Johan Monster",
    author_email="jj.monster@hotmail.com",
    packages=["helmholtz_cage_toolkit/"],
    # packages=find_packages(),
    install_requires=[
        "matplotlib",
        "numpy",
        "pyadi-iio",
        "pyIGRF",
        "PyOpenGL",
        "PyQt5; python_version >= '5.15.10'",
        # "PySide6",  # Upgrade with care: qt_material does not like PyQt5 and PySide6 installed at the same time, and the performance drop for plotting seems much worse for PySide6
        "pyqtgraph",
        "qt_material",
        "scipy",
    ],
)