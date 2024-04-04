Komanawa NZ Depth to Water
#########################################

a small repo that holds:

* The code used to produce a New Zealand wide depth to water dataset
* Versioning of and access to the dataset
* Full documentation of the dataset

.. toctree::
    :maxdepth: 2
    :hidden:

    Code documentation<autoapi/komanawa/komanawa-nz-depth-to-water/index.rst>

Data Access and versions
###########################

:Version: 1.0.0
:Date: 2024-04-04
:Description: Initial release of the dataset
:Changelog entry: Initial release of the dataset
:Data access: `access the data on Figshare <todo>`_


Contributing and issues/bugs
##############################

We have made every attempt to ensure the quality of the data and code in this repository. However, inevitably, there will be issues with the data or code. If you find an issue, please raise an issue on the GitHub repository. If you would like to contribute to the code or data, please fork the repository and submit a pull request.


Technical Report
######################

.. todo evelyn here is the place to frame the technical report.

Introduction and Background
=============================

Future Coasts Aotearoa is a NIWA led MBIE Endeabour research programme that combines expertise in Indigenous culture, economics, social, and physical sciences to tackle the issue of sea-level rise in coastal lowland communities by enhancing the evidence base for sea-level rise risks. It aims to build fit-for-purpose & holistic wellbeing evaluation tools, applying these tools in adaptive planning and decision-making frameworks for a range of case studies.
Our role at KSL, alongside GNS and the University of Canterbury, is to develop impact and adaptation thresholds for shallow groundwater and seawater intrusion, develop a national coastal groundwater hazard exposure assessment, and national and local models of seawater intrusion and water table shoaling with and without adaptation solutions such as pumped drainage.

As part of this, we have collected and processed a national depth to water dataset for New Zealand. This technical report outlines the data collected, the methods used to produce this dataset, and the potential use cases both within the project and externally.

Methodology
=============

Data was collected from regional councils directly and using Tethys (developed by Mike Kitteridge). The data was processed using Python; the resulting scripts are publicly available on GitHub. The details of the data collection and processing are outlined in greater detail below.

Data Summary
---------------

A data request was sent out to all thirteen regional councils in March 2023. The data request asked for all groundwater level data; this included sites additional to any NGMP monitoring sites, as well as any discontinuous or sporadic readings. The aim was to collect as much national data as possible, and therefore even sites with only one reading provided some use to us. Along with the groundwater level data we also requested standard metadata for each site.
Our minimum metadata requirements were:
- Unique site identifier (e.g. site number)
- Grid reference in NZTM
- Well depth

If present for the site, screen top & bottom depth, and the elevation of the measuring point were requested.

The data was received in Excel and csv formats, with various degrees of completeness and processing. Data management and storage varied from council to council, which meant processing to standardise the data was required.

Alongside the direct requests to regional councils, data was also pulled from Tethys. Tethys is a Python-based tool developed by Mike Kitteridge which allows any data stored by councils in Hilltop to be accessed and downloaded. For councils that had relevant and up-to-date data in Hilltop, it meant we did not have to rely on a response to the direct request, and saved time in the data collection process. Data from Tethys was downloaded as a csv file.

A brief summary of the data collected from each council is provided below.

