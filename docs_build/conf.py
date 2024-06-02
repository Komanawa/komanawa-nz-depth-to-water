# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
from pathlib import Path

project = 'komanawa-nz-depth-to-water'
copyright = '2024, Komanawa Solutions Ltd.'
light_name = 'nz-depth-to-water'
project_dirname = 'nz_depth_to_water'
author = 'Patrick Durney, Matt Dumont, Evelyn Charlesworth'
sys.path.append(str(Path(__file__).parent.parent.joinpath('src', 'komanawa', project_dirname)))
print(sys.path)
from version import __version__

release = f'v{__version__}'
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ['sphinx.ext.todo', 'sphinx.ext.viewcode', 'sphinx.ext.autodoc',
              'sphinx.ext.autosummary']
extensions.append('autoapi.extension')

# Auto API settings
autoapi_implicit_namespaces = True  # Allow for implicit namespaces
autoapi_keep_files = True  # Keep the generated files (for debugging)
autoapi_ignore = []  # Ignore these files
autoapi_python_class_content = 'both'  # Include both the class docstring and the __init__ docstring
autoapi_dirs = ['../src/komanawa/']  # The directory to process
autoapi_options = ['members', 'inherited-members', 'show-inheritance', 'show-module-summary', 'imported-members',
                   'show-inheritance-diagram']

autoapi_member_order = 'groupwise'

autoapi_python_use_implicit_namespaces = True
templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- options for autodoc -----------------------------------------------------
add_module_names = False  # Don't add the module name to the class/function name
toc_object_entries_show_parents = 'hide'  # Hide the parent class in the TOC

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# import sphinx_pdj_theme
# html_theme = 'sphinx_pdj_theme'
# html_theme_path = [sphinx_pdj_theme.get_html_theme_path()]
# html_theme = 'sphinx_rtd_theme'
html_theme = 'pydata_sphinx_theme'

html_static_path = ['_static']
html_sidebars = {'**': [
    # 'globaltoc.html', # add global api
    # 'localtoc.html',
    # 'searchbox.html'
]}
html_theme_options = {
    "use_edit_page_button": False,
    "navbar_end": ["navbar-icon-links"],
    "logo": {
        "image_light": "_static/ksl_for_latex.png",
        "text": f"{light_name.title()} {release} Overview",
    },
    "show_toc_level": 2,
    "secondary_sidebar_items": ["page-toc", ],
    "navbar_align": "left",
    "icon_links": [
        {
            "name": "View on GitHub",
            "url": "#https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water#",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },

        {
            'name': 'Follow us on LinkedIn',
            'url': 'https://www.linkedin.com/company/k%C5%8Dmanawa-solutions-ltd/',
            'icon': "fa-brands fa-linkedin",
            "type": "fontawesome",
        },
        {
            "name": "Komanawa Solutions Ltd.",
            "url": "https://www.komanawa.com",
            "icon": "_static/just_symbol.png",
            "type": "local",
        },

    ],
}
html_show_sourcelink = False
html_context = {
    "default_mode": 'light'
}

variables_to_export = [
    "project",
    "copyright",
    'release',
    "author",
    'light_name',
]
frozen_locals = dict(locals())
rst_epilog = '\n'.join(map(lambda x: f".. |{x}| replace:: {frozen_locals[x]}", variables_to_export))
del frozen_locals
