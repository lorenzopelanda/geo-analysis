# -- Project information -----------------------------------------------------
import os
import sys

sys.path.insert(0, os.path.abspath('..'))

project = 'GreenTo'
copyright = '2025, GreenTo'
author = 'GreenTo'
release = '0.1'

# -- General configuration ---------------------------------------------------
extensions = ["sphinx.ext.autodoc", "sphinx.ext.todo", "sphinx.ext.viewcode"]

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

html_theme_options = { 
    "navbar_align": "left",
    "show_toc_level": 2,
    "show_source_link": False,
    "use_source_button": False,
    "source_link_position": "none",
    "source_repository": "",  
    "source_branch": "",      
    "source_directory": "",
}

html_css_files = [
    'css/custom.css',
]

templates_path = ['_templates']