from setuptools import setup, find_packages

requirements = [
]

test_requirements = [
    'pytest',
    'pytest-cov',
    'pytest-faulthandler',
    'pytest-mock',
    'pytest-qt',
    'pytest-xvfb',
]

setup(
    name='FuniiLabel',
    version='0.0.1',
    description="App to label video from the FUNii project",
    author="Alexis Fortin-Cote",
    author_email='alexisfcote@gmail.com',
    url='https://github.com/alexisfcote/FuniiLabel',
    packages=find_packages(),
    package_data={'funiilabel.images': ['*.png']},
    entry_points={
        'console_scripts': [
            'FuniiLabel=funiilabel.funiilabel:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='FuniiLabel',
    classifiers=[
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='pytest',
    setup_requires=["pytest-runner"],
    tests_require=test_requirements
)
