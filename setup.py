from setuptools import setup, find_packages

setup(
    name="helmholtz_cage_toolkit",
    version="0.1.0",
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
        "PyQt5",
        # "PySide6",
        "pyqtgraph",
        "qt_material",
        "scipy",
    ],
#   scripts=[
#            "folder1/lib1",
#            "folder1/folderA/libA",
#            "folder2/lib2",
#            ]
)