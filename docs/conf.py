# -- Project information -----------------------------------------------------
import os
import sys
import pydata_sphinx_theme

sys.path.insert(0, os.path.abspath('../src'))

print("Python sys.path:", sys.path)

project = 'GreenTo'
copyright = '2025, GreenTo'
author = 'GreenTo'
release = '0.1'

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon"  
]


templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

html_title = "GreenTo"

html_context = {
    "github_user": "lorenzopelanda",
    "github_repo": "geo-analysis",
    "github_version": "main",  
}

html_show_sourcelink = False
html_copy_source = False
html_sourcelink_suffix = ''


html_css_files = [
    'css/custom.css',
]

templates_path = ['_templates']

# -- Napoleon settings -------------------------------------------------------
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
