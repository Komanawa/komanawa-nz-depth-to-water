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


Technical Note
######################


Introduction and Background
=============================

Future Coasts Aotearoa is a NIWA led MBIE Endeabour research programme that combines expertise in Indigenous culture, economics, social, and physical sciences to tackle the issue of sea-level rise in coastal lowland communities by enhancing the evidence base for sea-level rise risks. It aims to build fit-for-purpose & holistic wellbeing evaluation tools, applying these tools in adaptive planning and decision-making frameworks for a range of case studies.
Our role at KSL, alongside GNS and the University of Canterbury, is to develop impact and adaptation thresholds for shallow groundwater and seawater intrusion, develop a national coastal groundwater hazard exposure assessment, and national and local models of seawater intrusion and water table shoaling with and without adaptation solutions such as pumped drainage.

As part of this, we have collected and processed a national depth to water dataset for New Zealand. This technical report outlines the data collected, the methods used to produce this dataset, and the potential use cases both within the project and externally.

Methodology
=============
.. todo need a reference for tethys

Data was collected from regional councils and unitary authorities directly and using Tethys (developed by Mike Kitteridge ). The data was processed using Python; the resulting scripts are publicly available on GitHub. The details of the data collection and processing are outlined in greater detail below.

Data Summary
---------------

A data request was sent out to 15 New Zealand councils in March 2023; this included all 11 regional councils and four unitary authorities. The data request asked for all groundwater level data; this included sites additional to any NGMP monitoring sites, as well as any discontinuous or sporadic readings. The aim was to collect as much national data as possible, and therefore even sites with only one reading provided some use to us. We were open to receiving both groundwater depth and/or groundwater elevation data, but just asked that it was specified to reduce error during the data processing. Along with the groundwater level data we also requested standard metadata for each site.
Our minimum metadata requirements were:
- Unique site identifier (e.g. site number)
- Grid reference in NZTM
- Well depth

If present for the site, screen top & bottom depth, and the elevation of the measuring point were requested.

The data was received in Excel and csv formats, with various degrees of completeness and processing. Data management and storage varied from council to council, which meant processing to standardise the data was required.

Alongside the direct requests to regional councils and unitary authorities, data was also pulled from Tethys. Tethys is a Python-based tool developed by Mike Kitteridge which allows any data stored by councils in Hilltop to be accessed and downloaded. For councils that had relevant and up-to-date data in Hilltop, it meant we did not have to rely on a response to the direct request, and saved time in the data collection process. Data from Tethys was downloaded as a csv file.

A brief summary of the data collected from each council is provided below. The data quality rating is based on the formatting of the data as well as the relative quality of the data provided.
.. todo Evelyn can you qualify the data quality ratings, e.g. what makes a high quality dataset vs a low quality dataset?

+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Council                                      | Data Provided                                                                                                                                                                                                              | Data Quality |
+==============================================+============================================================================================================================================================================================================================+==============+
| Auckland Council                             | Continuous monitoring data downloaded from online data portal. Extra data sent through in spreadsheets, including historical/closed sites. Metadata sent through in a separate spreadsheet.                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Bay of Plenty Regional Council               | Continuous monitoring data and static groundwater levels sent through in separate spreadsheets. Metadata sent through in two different spreadsheets                                                                        | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Environment Canterbury                       | Continuous and spot readings sent through in spreadsheets based on monitoring data. Metadata sent through in a separate spreadsheet, with supporting supplementary information.                                            | Very high    |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Gisborne District Council                    | Available groundwater level data downloaded from Tethys. Separate data sent through from council, including discrete data and other data classified by the council as poor quality, with disclaimers surrounding the data. | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Hawkes Bay Regional Council                  | Available groundwater level data downloaded from Tethys. Manual dip data, any sites missing from Tethys and extra metadata sent through from the council.                                                                  | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Horizons Regional Council                    | Available groundwater level data downloaded from Tethys. Manual dip data and spot readings sent through by council, as well as metadata for the sites sent through. Any wells missing from Tethys were also provided.      | Low          |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Marlborough District Council                 | Available groundwater level data downloaded from Tethys. Only data sent through from the council was in the form of a shapefile which contained static water level from drilling and some well metadata.                   | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Northland Regional Council                   | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Otago Regional Council                       | Continuous and spot readings sent through in spreadsheets, along with metadata in separate spreadsheets.                                                                                                                   | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Environment Southland                        | Available groundwater level data downloaded from Tethys. Dip readings sent through by the council, as well as any extra metadata and comments on the sites.                                                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Taranaki Regional Council                    | Available groundwater level data downloaded from Tethys. Any missing sites sent through by the council, including both continuous and discrete data. Metadata also sent through.                                           | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Tasman District Council                      | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Waikato Regional Council                     | All continuous groundwater level data sent through by the council, with a separate csv file for each well. Static readings for each well sent through, as well as metadata.                                                | High         |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Wellington Regional Council                  | Available groundwater level data downloaded from Tethys. Static readings with metadata sent through by the council as a spreadsheet and shapefile                                                                          | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| West Coast Regional Council                  | Continuous and static groundwater level data sent through by the council, as well as metadata.                                                                                                                             | Medium       |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
| Other: NZ Geotechnical database              | Continuous and static groundwater levels data sent through by XXXX, as well as associated metadata.                                                                                                                                                                                        |              |
+----------------------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------------+
.. todo should armandine's data be included in this table or not do you think?

Data Processing
------------------

The data was processed using Python. The scripts used to process the data are available on GitHub; these are open source, and we encourage others to use and adapt them for their own purposes, as well as flag any issues or areas of improvement. Please note that code for resampling elevation data for each site is not available, as this relies on internal scripts and tools specific to KSL.

.. todo this could probably be deleted and replaced with the systematic approach below? seems unnecessary to have both?

The data processing steps are outlined below:

- A script was created for each council
    - The data was ingested and cleaned
    - This included both the Tethys data and the data received directly from councils, where both was present
    - Cleaning the data involved formatting any datatypes, renaming columns, and removing any unnecessary columns
    - Depending on the format the data was received in, it was either processed into depth to water or elevation so that each dataset had both measurements present
    - The data was checked for potentially erroneous readings, such as negative values or values that were outside the expected range
    - Any unwanted NaN values were removed
    - Finally, water levels from all sources were then then combined into one dataset
    - Where elevation data was not provided, LiDAR data was sampled to calculate the elevation at each site
- The metadata was ingested and cleaned
    - This involved the same steps as above, but also ensured the metadata site names matched the groundwater level data site names

More fully the systematic approach was as follows:

- Ingestion and Preliminary Cleaning
    - Individual scripts were developed for each council to cater to the unique formats of the datasets provided.
    - GWL data, alongside metadata, were ingested from two primary sources: direct council submissions and the Tethys platform, accessed via a Python API call.
    - Preliminary cleaning involved standardising data formats, renaming columns for consistency, and excising superfluous columns.
- Data Standardization and Transformation
    - The data was processed to ensure the presence of both depth-to-water and elevation measurements. In instances where elevation data was absent, LiDAR data was utilised to ascertain site elevation.
    - Anomalies such as negative values or readings beyond expected ranges were meticulously examined and rectified. Erroneous NaN values were also purged from the dataset.
    - All spatial data were transformed into the NZGD 2000 Transverse Mercator projection and NZVD2016 vertical datum.
    - The data was resampled to a consistent temporal resolution, ergo standardised to daily intervals.
    - The data was amalgamated into a singular dataset, with each record containing both depth-to-water and groundwater elevation measurements.
    - The datasets were given a quality rating based on their type and source
    - The data was checked for any duplicates and removed
- Metadata Synthesis and Alignment
    - Metadata processing paralleled the data cleaning steps, with additional emphasis on ensuring alignment between site names in the metadata and the GWL data.
    - The metadata schema encapsulated a comprehensive array of fields, ranging from well names and depths to spatial coordinates and screening details.
    - Groundwater elevations were meticulously derived from ground elevation plus collar height (where available) minus depth to water, except for instances where councils provided elevations in NZVD2016.
- Data Aggregation and Quality Assurance
    - The processed data from various sources were coalesced into a singular dataset. This aggregation involved strategic merging and deduplication, governed by predefined rules to ensure data integrity.
    - Quality control measures, including data and metadata checks, were instituted to uphold the data's accuracy and reliability.
- Storing and Accessing Processed Data
    - The culminated GWL data and metadata were systematically stored in an HDF5 store, facilitating ease of access and analysis.
    - Provisions were made to recalculate and update the stored data as necessary, ensuring the database remained current and reflective of the most recent submissions.
- Assumptions and Considerations
    - A fundamental assumption is that depth-to-groundwater measurements below the ground surface are positive, with negative readings indicative of artesian conditions. This necessitated sign adjustments and validation against council records.
    - In cases where well depth information was unavailable, wells were presumed shallow rather than being excluded from the dataset.
    - Specific regional peculiarities, such as the assumed + 100 m offset for coastal groundwater elevations provided by the Otago Regional Council, were duly considered and adjusted.
    - For wells where the maximum depth to water exceeded the reported well depth, an assumption was made that the well depth equaled the maximum depth to water plus an additional 3 metres.

Statistical Analysis of datasets
-----------------------------------
.. todo Paddy to create this section which will be a summary of the statistics of the datasets, e.g. number of sites, number of readings per source, etc.



Results
=========

The resulting dataset is a national depth to water dataset for New Zealand; the groundwater level data and metadata are available as a complete dataset which can be used for national groundwater modelling, and to better understand the potential of shallow groundwater in New Zealand.
The dataset is available as an output of the open source GitHub code. If you are interested in the input datasets so you can run the code for yourself, please get in contact with us and we can provide them.

The dataset will be used within the Future Coasts project for the development of national scale depth to water estimates and probability maps using statistical models to inform risk assessments.. todo Matt/paddy to fill in

We envisage that this dataset will be useful for a range of other projects as it provides a cleaned and queryable national dataset of groundwater level data. As new data becomes available, we hope to update the dataset and release new versions, depending on our resource availability. If you have extra data that has not been included in this national dataset, or are aware of more current data, please get in touch.

Limitations and Future Work
=============================
.. todo Evelyn, can you please fill this in with the limitations and future work for the dataset?

Acknowledgements
==================
We would like to acknowledge the regional councils and unitary authorities, specifically their environmental data teams, for providing us with the required data, and for responding to our data requests and subsequent questions. We appreciate your work in collecting and maintaining this data.
Thank you to:
- Auckland Council
- Bay of Plenty Regional Council
- Environment Canterbury
- Gisborne District Council
- Hawkes Bay Regional Council
- Horizons Regional Council
- Marlborough District Council
- Northland Regional Council
- Otago Regional Council
- Environment Southland
- Taranaki Regional Council
- Tasman District Council
- Waikato Regional Council
- Wellington Regional Council
- West Coast Regional Council

We would like to acknowledge Mike Kitteridge for his development of Tethys, and for providing assistance in using the platform and accessing data.
We would like to acknowledge the New Zealand Geotechnical Database for providing us with groundwater level data.
We would like to thank Armandine Bosserelle for providing us with groundwater level data for the Waimakariri area.

.. todo is there anyone I'm missing?