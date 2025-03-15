from setuptools import setup, find_packages

setup(
    name="workday_timer",
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
            'workday_timer=workday_timer:main',
        ],
    },
    author="Your Name",
    description="A desktop timer application for tracking work hours",
    keywords="timer, desktop, work",
    python_requires=">=3.6",
)