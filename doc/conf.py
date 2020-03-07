# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import pandasdmx

# -- Project information -----------------------------------------------------

project = 'pandaSDMX'
copyright = '2014–2020 pandaSDMX developers'
# The major project version, used as the replacement for |version|.
version = pandasdmx.__version__[:3]
# The full project version, used as the replacement for |release|.
release = pandasdmx.__version__


# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'IPython.sphinxext.ipython_console_highlighting',
    'IPython.sphinxext.ipython_directive',
]

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'alabaster'


# -- Options for sphinx.ext.intersphinx --------------------------------------

intersphinx_mapping = {
    'np': ('https://docs.scipy.org/doc/numpy/', None),
    'pd': ('https://pandas.pydata.org/pandas-docs/stable/', None),
    'py': ('https://docs.python.org/3/', None),
    'requests': ('http://2.python-requests.org/en/master/', None),
    'requests-cache': ('https://requests-cache.readthedocs.io/en/latest/',
                       None),
}


# -- Options for sphinx.ext.todo ---------------------------------------------

# If True, todo and todolist produce output, else they produce nothing.
todo_include_todos = True


# -- Options for IPython.sphinxext.ipython_directive -------------------------

# Specify if the embedded Sphinx shell should import Matplotlib and set the
# backend.
ipython_mplbackend = ''
