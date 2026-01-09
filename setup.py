from setuptools import setup, find_packages

setup(
    name="soplos-welcome-live",
    version="2.0.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['*.glade', '*.ui', '*.css', '*.png', '*.svg', '*.jpg', '*.mo', '*.pot', '*.po'],
    },
    install_requires=[
        'PyGObject>=3.40.0',
        'psutil>=5.8.0',
    ],
    entry_points={
        'console_scripts': [
            'soplos-welcome-live=main:main',
        ],
    },
    scripts=['main.py'],
    author="Sergi Perich",
    author_email="info@soploslinux.com",
    description="Soplos Welcome Live 2.0 - Live ISO Welcome Application",
    license="GPL-3.0",
    url="https://soplos.org",
)
