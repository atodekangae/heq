from setuptools import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / 'README.md').read_text()

repo_url = 'https://github.com/atodekangae/heq'

setup(
    name='heq',
    version='0.0.2',
    url=repo_url,
    description="Yet another 'jq for HTML'",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='atodekangae',
    author_email='atodekangae@gmail.com',
    py_modules=['heq'],
    python_requires='>=3.8',
    install_requires=[
        'lxml>=4',
        'parsimonious>=0.10.0',
    ],
    extras_require={
        'dev': ['pytest>=6.0,<7.0'],
    },
    entry_points={
        'console_scripts': [
            'heq=heq:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: Text Processing :: Markup :: HTML',
        'Environment :: Console'
    ]
)
