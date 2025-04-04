Kо̄manawa NZ Depth to Water
#########################################

a small repo that holds:

* The code used to produce a New Zealand wide depth to water dataset
* Versioning of and access to the dataset
* Full documentation of the dataset

:Author: |author|
:copyright: |copyright|
:Version: |release|
:Date: |today|
:Changelog entry: Initial release of the dataset
:Data access: Access the data via this package.

.. include:: last_updated.rst

.. toctree::
    :maxdepth: 2
    :hidden:

    Code documentation<autoapi/komanawa/nz_depth_to_water/index.rst>
    Dataset Technical Note<supporting_docs/Technial_note.rst>

.. include:: supporting_docs/limitations.rst

Data Access via Python
========================
Installation
---------------

**Option 1 - pip**

.. code-block:: bash

        pip install git+https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water.git

**Option 2 - clone the repository**

clone the repository and install the package as you see fit.

**Option 3 - Fork the repository**

Fork the repository and modify and use the code as you see fit.  If you have any improvements, please submit a pull request.

Code Example
---------------

.. code-block:: python

    from komanawa.nz_depth_to_water import get_nz_depth_to_water
    water_level_data, metadata = get_nz_depth_to_water()


Export the data to a csv files
--------------------------------

To export the data to a csv file, you can use the following code (assuming you have installed the package):

.. code-block:: bash

        python -m komanawa.nz_depth_to_water.export_to_csv

Alternatively, you can specify a folder to export the data:

.. code-block:: bash

        python -m komanawa.nz_depth_to_water.export_to_csv /path/to/folder

Contributing and issues/bugs
=============================

We have made every attempt to ensure the quality of the data and code in this repository. However, inevitably, there will be issues with the data or code. If you find an issue, please raise an issue on the GitHub repository. If you would like to contribute to the code or data, please fork the repository and submit a pull request.


.. include:: metadata.rst


Source key
====================

+------------+--------------------------------------+
| **Source** | **Full name**                        |
+============+======================================+
| auk        | Auckland Council                     |
+------------+--------------------------------------+
| bop        | Bay of Plenty Regional Council       |
+------------+--------------------------------------+
| gdc        | Gisborne District Council            |
+------------+--------------------------------------+
| hbrc       | Hawkes Bay Regional Council          |
+------------+--------------------------------------+
| hrc        | Horizons Regional Council            |
+------------+--------------------------------------+
| mdc        | Marlborough District Council         |
+------------+--------------------------------------+
| nrc        | Northland Regional Council           |
+------------+--------------------------------------+
| ncc        | Nelson City Council                  |
+------------+--------------------------------------+
| orc        | Otago Regional Council               |
+------------+--------------------------------------+
| src        | Environment Southland                |
+------------+--------------------------------------+
| trc        | Taranaki Regional Council            |
+------------+--------------------------------------+
| tdc        | Tasman District Council              |
+------------+--------------------------------------+
| tcc        | Tauranga City Council                |
+------------+--------------------------------------+
| wc         | Waikato Regional Council             |
+------------+--------------------------------------+
| gwrc       | Greater Wellington Regional Council  |
+------------+--------------------------------------+
| wcrc       | West Coast Regional Council          |
+------------+--------------------------------------+
| nzgd       | New Zealand Geotechnical database    |
+------------+--------------------------------------+
| ecan       | Environment Canterbury               |
+------------+--------------------------------------+

