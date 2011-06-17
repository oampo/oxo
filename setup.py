from distutils.core import setup
 
setup(name="oxo",
      version="0.1",
      author="Joe Turner",
      author_email="joe@oampo.co.uk",
      packages=["oxo"],
      scripts=["bin/oxo"],
      package_data={'oxo': ['resources/oxo.mustache',
                            'resources/css/*.css',
                            'resources/css/museo-sans/*',
                            'resources/css/pygments/*',
                            'resources/js/*.js']})
