from setuptools import setup, find_packages

setup(
    name="minitools",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "keyboard>=0.13.5",
        "Pillow>=9.0.0",
        "requests>=2.28.0",
        "numpy>=1.21.0",
    ],
    entry_points={
        'console_scripts': [
            'minitools=main:main',
        ],
    },
    author="Your Name",
    description="A desktop utility application",
    keywords="utility, desktop, tools",
    python_requires=">=3.6",
)