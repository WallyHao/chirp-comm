from setuptools import setup, find_packages

setup(
    name="chirp_comm",
    version="0.2",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scipy",
        "sounddevice",
    ],
)