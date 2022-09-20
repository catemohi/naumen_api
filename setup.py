from setuptools import setup, find_packages
from os.path import join, dirname


setup(
    name='naumen_api',
    version='1.0',
    author="catemohi",
    author_email="catemohi@gmail.com",
    description="API CRM системы, основанное на парсинге DOM-дерева.",
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    long_description_content_type="text/markdown",
    url="https://github.com/catemohi/naumen-api",
    lecense='GNU General Public License v3.0',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.11.1',
        'certifi>=2022.9.14',
        'charset-normalizer>=2.1.1',
        'idna>=3.4',
        'requests>=2.28.1',
        'soupsieve>=2.3.2.post1',
    ],
    include_package_data=True,
)
