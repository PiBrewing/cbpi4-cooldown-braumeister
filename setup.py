from setuptools import setup

setup(name='cbpi4-cooldown-braumeister',
      version='0.0.1.a2',
      description='CraftBeerPi Plugin',
      author='',
      author_email='',
      url='',
      include_package_data=True,
      package_data={
        # If any package contains *.txt or *.rst files, include them:
      '': ['*.txt', '*.rst', '*.yaml'],
      'cbpi4-cooldown-braumeister': ['*','*.txt', '*.rst', '*.yaml']},
      packages=['cbpi4-cooldown-braumeister'],
      install_requires=[
          "scipy"]
     )