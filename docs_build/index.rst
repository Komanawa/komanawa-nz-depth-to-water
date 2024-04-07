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

A national set of depth to water measurements across New Zealand is a fundamental component of Future Coast Aotearoa. This technical report outlines the data collected, the methods used to produce this dataset, and the potential use cases both within the project and externally. We are publishing this dataset to 1) make it more widely available to the research community, 2) to provide a reference for this base dataset across the Future Coasts Aotearoa project, and 3) to initiate a conversation around the quality and availability of groundwater data in New Zealand.

Methodology
=============

Data was collected from regional councils directly and using Tethys (developed by Mike Kitteridge). The data was processed using Python; the resulting scripts are publicly available on GitHub. The details of the data collection and processing are outlined in greater detail below.

Data Source Summary
---------------------

A data request was sent out to all thirteen regional councils in March 2023. The data request asked for all groundwater level data; this included sites additional to any NGMP monitoring sites, as well as any discontinuous or sporadic readings. The aim was to collect as much national data as possible, and therefore even sites with only one reading provided some use to us. We were open to receiving both groundwater depth and/or groundwater elevation data, but just asked that it was specified to reduce error during the data processing. Along with the groundwater level data we also requested standard metadata for each site.

Our minimum metadata requirements were:
- Unique site identifier (e.g. site number)
- Grid reference in NZTM
- Well depth .. todo not sure if this was included... Paddy?

If present for the site, screen top & bottom depth, and the elevation of the measuring point were requested.

The data was received in Excel and csv formats, with various degrees of completeness and processing. Data management and storage varied from council to council, which meant processing to standardise the data was required.

Alongside the direct requests to regional councils, data was also pulled from Tethys. Tethys is a Python-based tool developed by Mike Kitteridge which allows any data stored by councils in Hilltop to be accessed and downloaded. For councils that had relevant and up-to-date data in Hilltop, it meant we did not have to rely on a response to the direct request, and saved time in the data collection process. Data from Tethys was downloaded as a csv file.

A brief summary of the data collected from each council is provided below. The data quality rating is based on the formatting of the data as well as the relative quality of the data provided.

+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Council                                      | Data Provided                                                                                                                                                                                                              | Data Quality |
+==============================================+============================================================================================================================================================================================================================+==============+
| Auckland Council                             | Continuous monitoring data downloaded from online data portal. Extra data sent through in spreadsheets, including historical/closed sites. Metadata sent through in a separate spreadsheet.                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Bay of Plenty Regional Council               | Continuous monitoring data and static groundwater levels sent through in separate spreadsheets. Metadata sent through in two different spreadsheets                                                                        | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Environment Canterbury                       | Continuous and spot readings sent through in spreadsheets based on monitoring data. Metadata sent through in a separate spreadsheet, with supporting supplementary information.                                            | Very high    |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Gisborne Regional Council                    | Available groundwater level data downloaded from Tethys. Separate data sent through from council, including discrete data and other data classified by the council as poor quality, with disclaimers surrounding the data. | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Hawkes Bay Regional Council                  | Available groundwater level data downloaded from Tethys. Manual dip data, any sites missing from Tethys and extra metadata sent through from the council.                                                                  | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Horizons Regional Council                    | Available groundwater level data downloaded from Tethys. Manual dip data and spot readings sent through by council, as well as metadata for the sites sent through. Any wells missing from Tethys were also provided.      | Low          |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Marlborough Regional Council                 | Available groundwater level data downloaded from Tethys. Only data sent through from the council was in the form of a shapefile which contained static water level from drilling and some well metadata.                   | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Northland Regional Council                   | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Otago Regional Council                       | Continuous and spot readings sent through in spreadsheets, along with metadata in separate spreadsheets.                                                                                                                   | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Environment Southland                        | Available groundwater level data downloaded from Tethys. Dip readings sent through by the council, as well as any extra metadata and comments on the sites.                                                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Taranaki Regional Council                    | Available groundwater level data downloaded from Tethys. Any missing sites sent through by the council, including both continuous and discrete data. Metadata also sent through.                                           | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Tasman Regional Council                      | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Waikato Regional Council                     | All continuous groundwater level data sent through by the council, with a separate csv file for each well. Static readings for each well sent through, as well as metadata.                                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Wellington Regional Council                  | Available groundwater level data downloaded from Tethys. Static readings with metadata sent through by the council as a spreadsheet and shapefile                                                                          | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| West Coast Regional Council                  | Continuous and static groundwater level data sent through by the council, as well as metadata.                                                                                                                             | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Other data sources: Amandine Bosserelle      | Extra data from the Waimakariri area was provided by Amandine Bosserelle. This included extra data from shallow monitoring wells specifically.                                                                             | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Other data sources: NZ Geotechnical database |.. todo Paddy to fill in                                                                                                                                                                                                    |              |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+

Data Processing
------------------

The data was processed using Python. The scripts used to process the data are available on GitHub; these are open source, and we encourage others to use and adapt them for their own purposes, as well as flag any issues or areas of improvement. Please note that code for resampling elevation data for each site is not available, as this relies on internal scripts and tools specific to KSL.

The data processing steps are outlined below:
- A script was created for each council
- The data was ingested and cleaned
    - This included both the Tethys data and the data received directly from councils, where both was present
    - Cleaning the data involved formatting any datatypes, renaming columns, and removing any unnecessary columns
    - Depending on the format the data was received in, it was either processed into depth to water or elevation so that each dataset had both measurements present
    - Where elevation data was not provided, LiDAR data was sampled to calculate the elevation at each site
    - The data was checked for potentially erroneous readings, such as negative values or values that were outside the expected range
    - Any unwanted NaN values were removed
    - It was then combined into one dataset
- The metadata was ingested and cleaned
    - This involved the same steps as above, but also ensured the metadata site names matched the groundwater level data site names

.. todo paddy to add any extra notes or steps here

Data Assumptions and sources of ambiguity
--------------------------------------------

.. todo paddy


Results
=========

The resulting dataset is a national depth to water dataset for New Zealand; the groundwater level data and metadata are available as a complete dataset which can be used for national groundwater modelling, and to better understand the potential of shallow groundwater in New Zealand.
The dataset is available as an output of the open source GitHub code. If you are interested in the input datasets so you can run the code for yourself, please get in contact with us and we can provide them.

The dataset will be used within the Future Coasts project for .. todo Matt/paddy to fill in

We envisage that this dataset will be useful for a range of other projects as it provides a clean and queryable national dataset of groundwater level data. As new data becomes available, we hope to update the dataset and release new versions, depending on our resource availability. If you have extra data that has not been included in this national dataset, or are aware of more current data, please get in touch at admin@komanawa.com.


Data Access
--------------

The dataset is freely available on Figshare, and can be accessed here: `access the data on Figshare <todo>`_. In addition all of the code used to process the data is available on GitHub, and can be accessed here: `access the code on GitHub <todo>`_.  The Github repository also provides the entry point for any issues or bugs you may find in the data or code and provides a way to contribute to the dataset. Ongoing updating of this dataset is not guaranteed and subject to resource availability.


Data Model, Description and Scheme
-------------------------------------

The Data Model for the dataset is as follows:

#. Site metadata:
    - columns here .. todo paddy

#. Time dependent depth to water data
    - columns here .. todo paddy


.. todo paddy quality codes etc.


Dataset Overview
-------------------

.. todo maps of locations, density, variance, number of spot readings, number of higher frequency readings etc.


Conclusions and Recommendations
=====================================

.. todo  This was hard... better interoperability across data source to allow rapid response to things... Plug Tethys here....  Need to fund this shit.
.. todo  better and more conistant metadata needed... list for NZGD,





