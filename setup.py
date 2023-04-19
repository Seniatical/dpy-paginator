from setuptools import setup

version = "v1.0.0-rc2"
PACKAGES = [
    'discord.ext.paginator',
]

setup(
    name='dpy-Paginator',
    version=version[1:],
    description='A pagination library for discord.py v2+',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    project_urls={
        'Issue Tracker': 'https://github.com/Seniatical/dpy-paginator/issues',
        'Homepage': 'https://github.com/Seniatical/dpy-paginator',
    },
    author='Seniatical',
    license='MIT License',
    packages=PACKAGES,
)