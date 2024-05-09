Developing a National Depth to Water Dataset for New Zealand
#################################################################

.. include:: docs_build/last_updated.rst

Introduction and Background
=============================

Future Coasts Aotearoa is a NIWA led MBIE Endeabour research programme that combines expertise in Indigenous culture, economics, social, and physical sciences to tackle the issue of sea-level rise in coastal lowland communities by enhancing the evidence base for sea-level rise risks. It aims to build fit-for-purpose & holistic wellbeing evaluation tools, applying these tools in adaptive planning and decision-making frameworks for a range of case studies.
Our role at KSL, alongside GNS and the University of Canterbury, is to develop impact and adaptation thresholds for shallow groundwater and seawater intrusion, develop a national coastal groundwater hazard exposure assessment, and national and local models of seawater intrusion and water table shoaling with and without adaptation solutions such as pumped drainage.

As part of this, we have collected and processed a national depth to water dataset for New Zealand. This technical note outlines the data collected, the methods used to produce this dataset, and the potential use cases both within the project and externally.

Methodology
=============

Data was collected from regional councils and unitary authorities directly and using Tethys (https://github.com/tethys-ts, developed by Mike Kitteridge). The data was processed using Python; the resulting scripts are publicly available on GitHub: https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water. The details of the data collection and processing are outlined in greater detail below.

Data Summary
---------------

A data request was sent out to 16 New Zealand councils in March 2023; this included all 11 regional councils and five unitary authorities. The data request asked for all groundwater level data; this included sites additional to any NGMP monitoring sites, as well as any discontinuous or sporadic readings. The aim was to collect as much national data as possible, and therefore even sites with only one reading provided some use to us. We were open to receiving both groundwater depth and/or groundwater elevation data, but just asked that it was specified to reduce error during the data processing. Along with the groundwater level data we also requested standard metadata for each site.

Our minimum metadata requirements were:

- Unique site identifier (e.g. site number)
- Grid reference in NZTM
- Well depth

Our preferred metadata requirements included:

- Screen top & bottom depth
- Surveyed elevation of the ground surface at the measuring point
- The distance between the measuring point and the general ground surface.

The data was received in Excel and csv formats, with various degrees of completeness and processing. Data management and storage varied from council to council, which meant processing to standardise the data was required.

Alongside the direct requests to regional councils and unitary authorities, data was also pulled from Tethys. Tethys is a Python-based tool developed by Mike Kitteridge which allows any data stored by councils in Hilltop to be accessed and downloaded. For councils that had relevant and up-to-date data in Hilltop, it meant we did not have to rely on a response to the direct request, and saved time in the data collection and processing.

A brief summary of the data collected from each council is provided below. The data quality rating is based on the formatting of the data as well as the relative quality of the data provided.

+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Council                          | Data Provided                                                                                                                                                                                                              |
+==================================+============================================================================================================================================================================================================================+
| Auckland Council                 | Continuous monitoring data downloaded from online data portal. Extra data sent through in spreadsheets, including historical/closed sites. Metadata sent through in a separate spreadsheet.                                |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Bay of Plenty Regional Council   | Continuous monitoring data and static groundwater levels sent through in separate spreadsheets. Metadata sent through in two different spreadsheets                                                                        |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Environment Canterbury           | Continuous and spot readings sent through in spreadsheets based on monitoring data. Metadata sent through in a separate spreadsheet, with supporting supplementary information.                                            |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Gisborne District Council        | Available groundwater level data downloaded from Tethys. Separate data sent through from council, including discrete data and other data classified by the council as poor quality, with disclaimers surrounding the data. |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Hawkes Bay Regional Council      | Available groundwater level data downloaded from Tethys. Manual dip data, any sites missing from Tethys and extra metadata sent through from the council.                                                                  |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Horizons Regional Council        | Available groundwater level data downloaded from Tethys. Manual dip data and spot readings sent through by council, as well as metadata for the sites sent through. Any wells missing from Tethys were also provided.      |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Marlborough District Council     | Available groundwater level data downloaded from Tethys. Only data sent through from the council was in the form of a shapefile which contained static water level from drilling and some well metadata.                   |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Nelson City Council              | Any spot readings were sent through by the council with  metadata included.                                                                                       |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Northland Regional Council       | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Otago Regional Council           | Continuous and spot readings sent through in spreadsheets, along with metadata in separate spreadsheets.                                                                                                                   |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Environment Southland            | Available groundwater level data downloaded from Tethys. Dip readings sent through by the council, as well as any extra metadata and comments on the sites.                                                                |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Taranaki Regional Council        | Available groundwater level data downloaded from Tethys. Any missing sites sent through by the council, including both continuous and discrete data. Metadata also sent through.                                           |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Tasman District Council          | Available groundwater level data downloaded from Tethys. Any spot readings were sent through by the council with  metadata included.                                                                                       |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Waikato Regional Council         | All continuous groundwater level data sent through by the council, with a separate csv file for each well. Static readings for each well sent through, as well as metadata.                                                |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Wellington Regional Council      | Available groundwater level data downloaded from Tethys. Static readings with metadata sent through by the council as a spreadsheet and shapefile                                                                          |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| West Coast Regional Council      | Continuous and static groundwater level data sent through by the council, as well as metadata.                                                                                                                             |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Other: NZ Geotechnical database  | Continuous and static groundwater levels data sent through by NZGD, as well as associated metadata. These data were requested directly from Tonkin & Taylor which maintains the NZGD.                                      |
+----------------------------------+----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

Data Processing
------------------

The data was processed using Python. The scripts used to process the data are available on GitHub; these are open source, and we encourage others to use and adapt them for their own purposes, as well as flag any issues or areas of improvement. Please note that code for resampling elevation data for each site is not available, as this relies on internal scripts and tools specific to KSL.

The systematic approach to the data processing was as follows:

- Ingestion and Preliminary Cleaning
    - Individual scripts were developed for each council to cater to the unique formats of the datasets provided.
    - GWL data, alongside metadata, were ingested from two primary sources: direct council submissions and the Tethys platform, accessed via a Python API call.
    - Preliminary cleaning involved standardising data formats, renaming columns for consistency, and excising superfluous columns.
- Data Standardisation and Transformation
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

Results
=========

The resulting dataset is a national depth to water dataset for New Zealand; the groundwater level data and metadata are available as a complete dataset which can be used for national groundwater modelling, and to better understand the potential of shallow groundwater in New Zealand.
The dataset is available as an output of the open source GitHub code. If you are interested in the input datasets so you can run the code for yourself, please get in contact with us and we can provide them.

The dataset will be used within the Future Coasts project for a number of research aims and purposes including the development of national scale depth to water estimates and probability maps using statistical models to inform risk assessments.
We hope that making the data available here will reduce the barrier to entry for other researchers and organisations to use this data for their own purposes.
We envisage that this dataset will be useful for a range of other projects as it provides a cleaned and queryable national dataset of groundwater level data.


Statistical Analysis of datasets
-----------------------------------
The dataset comprises a comprehensive collection of groundwater monitoring sites, spanning a significant temporal range from as ealy as December 29, 1899. A statistical summary of the dataset is provided below.

.. include:: docs_build/tables/full_dataset_summary.rst

Investigating the dataset by source reveals distinct patterns in data collection and density.
Notably, Environment Canterbury (Ecan) stands out with the highest number of observations with many observations at each site.
This contrasts the New Zealand Geotechnical Database (nzgd) which has many fewer observations per site (frequently <= 2 readings/site).
Otago Regional Council (orc) provided data for fewer monitoring sites, but what is monitored has significant data density.
These variations highlight the diversity of monitoring efforts and data densities across different sources.
Collectively, these statistics underscore the heterogeneity of groundwater monitoring across regions, influenced by the varying goals (e.g. geotechnical investigations), methodologies, and resources of different data sources.
Further summary statistics of the data by the source are provided below.

.. include:: docs_build/tables/summary_by_source.rst

.. todo figure cumulative nrecords and n sites vs time (overall and by source)
.. todo spatial coverage of data (by n records)
.. todo cumulative data by nrecords/site (both nsites, and n data points)
.. todo data add data density layer calculation here???

Conclusions
=============

Preparing this dataset was a mammoth undertaking which took over a year between data collection, processing, and quality assurance and hundreds of staff hours.
This was a significant effort and component of the Future Coasts Aotearoa project.
The dataset is now available for use by other researchers and organisations, and we hope that it will be useful for a range of projects.

Unfortunately, despite our best intentions, we acknowledge that these data will likely fall out of date as new data is collected.
Access to fundamental groundwater data is essential for understanding the dynamics of groundwater systems and their interactions with the environment.
New Zealand's current groundwater monitoring network is diverse and fragmented, with each provider having unique monitoring objectives, methodologies, and data storage and management systems.
Some national approaches have been undertaken to standardise data collection and storage, such as the National Groundwater Monitoring Programme (NGMP) and the New Zealand Geotechnical Database (NZGD), but these are not comprehensive, do not cover the full breadth of groundwater monitoring data, and often have a primary focus (i.e. regional characterisation or geotechnical investigations, respectively).

The state of depth to water data in New Zealand provides a significant barrier and inefficiency to understanding and adapting to the impacts of climate change and sea-level rise on groundwater systems.
We recognise that this is not a unique conclusion and that many others have identified this issue before us and many others will identify it after us.

There are Significant Interest Groups (SIGs) whose primary purpose is to address this issue and we would encourage increased funding and support for these groups to make headway on data access and quality in the future.
That said, we cannot recommend waiting for a perfect national system to be in place -- researchers and organisations need access to these data now.
As a pragmatic interim solution we would recommend that some base standards be adopted:

#. All public data held by an organisation should be made available via a public API.
#. All public datasets should include metadata.  Ideally this metadata would be in a standard machine readable format, but as an interim solution, a simple publicly visible document discussing the data structure and any peculiarities would be a good start.
#. All public datasets should have a mechanism for users to report errors or issues with the data and these issues should be publicly visible. Even if organisations do not have the resources to fix all these issues, there is value in collating them. At the moment each researcher must discover these issues themselves, which is challenging and time consuming. Consider the value of forums like Stack Exchange or GitHub issues for this purpose in the software development world.
#. All public data held by an organisation should be available in a standard format. This could be as simple as CSV, but ideally would be a more structured format like JSON or XML. This would allow for easier integration with other datasets and tools.
#. All public dataset should have consistent +ve or -ve signs for depth to water above or below gwl. Ideally this would be a national standard, but minimally should be an organisational standard and documented.
#. All public datasets should have a consistent way of specifying the elevation of the measuring point. This could be as simple as a GPS elevation, but minimally should be documented.

Additionally, we would like to commend the NZGD for their work in providing a national database of geotechnical data. The dataset was of enormous value to this project, particularly in data sparce regions. We also have some specific additional recommendations for the NZGD: that they include additional fields to specify whether measurements at a point are relative to the average surrounding land surface or taken in foundation excavations. This is important because records from urban areas often show markedly different water depths compared to nearby observations. These discrepancies likely stem from variations in the drilling locations, such as greenfield sites versus foundation pits. To improve accuracy and consistency, we also urge the NZGD to mandate the provision of GPS elevation data for the bore collar as a minimum requirement.

#. As discussed above:
    #. A public API for the data would be of great value.
    #. As would a publicly visible mechanism for users to report issues, inconsistencies, and concerns with the data.
    #. We recommend that NZGD add the following fields 1: (minimum of gps) elevation of bore collar, 2. relative elevation of the bore collar to surrounding land surface.
Finally we have some specific recommendations for the dataset we have produced:

- Further quality assurance of the data, including cross-referencing the finalised data with councils.
- Further analysis of the data to identify any potential errors or outliers.
- Updating the dataset with new data as it becomes available.

Contributing and issues/bugs
==============================

We have made every attempt to ensure the quality of the data and code in this repository. However, inevitably, there will be issues with the data or code. If you find an issue, please raise an issue on the GitHub repository https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water/issues. If you would like to contribute to the code or data, please fork the repository and submit a pull request.  While we would like to commit to maintaining this dataset in the future, we are a small team and may not have the resources to do so. If you would like to become a longer term contributor to this dataset, please get in touch.

Limitations
=============
While we have made every attempt to ensure the quality of the data and code in this repository, we do not provide any explicit or implicit guarantee of the datasets produced or methods provided here.
We are aware of limitations of this work which are listed below:

- We have made a series of assumptions during the data processing; these are discussed above.
- The data is only as good as the data provided by the councils; we did not have the resources nor all the information to quality assure the data.
- For many sites, the elevation of the measuring point is unknown. We have used LiDAR data to estimate the elevation of the ground, but this will likely reduce the accuracy of the groundwater elevation.
- We have assumed that the depth to water from ground level is correct, and therefore any errors in the depth to water data will be reflected in the groundwater elevation values.
- As discussed, we have assumed any regional peculiarities when the information has been provided to us, but there may be other regional-specific aspects of the data that have been missed.
- The dataset is not exhaustive, and there may be more data available that has not been included in this dataset.

Acknowledgements
==================

This work could not have been completed without the support of the regional councils, unitary authorities, and other scientists who provided us with data and assistance. We would like to acknowledge the following people and organisations:

- We would like to acknowledge the regional councils and unitary authorities, especially their environmental data teams, for providing us with the required data, and for responding to our data requests and subsequent questions. We appreciate your work in collecting and maintaining this data. Thank you specifically to:
    - Freya Green from Auckland Council
    - Paul Scholes & Rochelle Gardner from Bay of Plenty Regional Council
    - Jennifer Tregurtha from Environment Canterbury
    - Julia Kendall from Gisborne District Council
    - Ale Cocimano from Hawkes Bay Regional Council
    - Michaela Rose from Horizons Regional Council
    - Charlotte Tomlinson from Marlborough District Council
    - Susie Osbaldiston & Sandrine Le Gars from Northland Regional Council
    - Marc Ettema from Otago Regional Council
    - Fiona Smith from Environment Southland
    - Sarah Avery from Taranaki Regional Council
    - Matt McLarin from Tasman District Council
    - Debbie Eastwood & Sung Soo Koh from Waikato Regional Council
    - Rob Van Der Raaij from Wellington Regional Council
    - Jonny Horrox from West Coast Regional Council
    - Simon Matthews from the New Zealand Geotechnical Database
    - Chris Strang from Nelson City Council
- Mike Kitteridge for his development of Tethys, and for providing assistance in using the platform and accessing data.
- The New Zealand Geotechnical Database for providing us with groundwater level data.
- Armandine Bosserelle for providing us with groundwater level data for the Waimakariri area.

This work was made possible by the Future Coasts Aotearoa programme, funded by the Ministry of Business, Innovation and Employment (MBIE) Endeavour Fund. We would like to acknowledge the support of the programme, NIWA, and the other researchers involved in the project.