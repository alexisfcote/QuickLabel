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
    name='quickLabel',
    version='0.0.1',
    description="App to label video from the quick project",
    author="Alexis Fortin-Cote",
    author_email='alexisfcote@gmail.com',
    url='https://github.com/alexisfcote/quickLabel',
    packages=find_packages(),
    package_data={'quicklabel.images': ['*.png'], 'models':['*.pkl']},
    entry_points={
        'console_scripts': [
            'quickLabel=quicklabel.quicklabel:main'
        ]
    },
    install_requires=requirements,
    zip_safe=False,
    keywords='quickLabel',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='pytest',
    setup_requires=["pytest-runner"],
    tests_require=test_requirements
)
