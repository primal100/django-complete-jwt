from setuptools import setup


# https://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
main_ns = {}
with open('django_complete_jwt/__init__.py') as f:
    exec(f.read(), main_ns)


setup(
    name=main_ns['app_name'],
    version=main_ns['__version__']
)
