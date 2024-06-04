Developing a National Depth to Water Dataset for New Zealand
#################################################################

.. include:: last_updated.rst


Introduction and Background
=============================

Groundwater level data are a key input for a broad range of water resource investigation, management and research activities. Access to national groundwater level data in New Zealand is challenging, however, because the data are held in the various Regional Council and Unitary Authority databases and in the New Zealand Geotechnical Database under a wide array of data architectures. The quality of the data and metadata varies significantly; in some instances, the data are subject to rigorous quality assurance processes and include accurate measurement point elevations and spatial coordinates. In other instances, the data comprise single readings of unknown quality with no information on the measurement point elevation or even the depth of the well

Future Coasts Aotearoa is a NIWA led MBIE Endeavour research programme that combines expertise in Indigenous culture, economics, social, and physical sciences to tackle the issue of sea-level rise in coastal lowland communities by enhancing the evidence base for sea-level rise risks. Key groundwater science outputs include develop impact and adaptation thresholds for shallow groundwater hazards, a national coastal groundwater hazard exposure assessment, and national and local models of seawater intrusion and water table shoaling.

This technical note outlines the data collected, the methods used to produce and analyse a national depth to water dataset for New Zealand for the Future Coasts research programme. The dataset will be valuable for a range of applied science and research activities.

Methodology
=============

Data gathering scope
----------------------

Groundwater level data can be grouped into discrete measurements and regular monitoring. The former include spot values recorded during/immediately after well drilling, measurements taken during geotechnical investigations (e.g. Cone Penetration Tests, geotechnical bores and trial pits) and piezometric surveys undertaken by Regional Councils. The latter includes manual and instrument-based regular data collection programmes undertaken by Regional Councils, Unitary Authorities and some Territorial Authorities. Groundwater level readings are also collected in accordance with consent conditions for certain consented activities, but these data are typically stored in reports and spreadsheets as part of a large set of files in records management systems operated by Regional Council and Unitary Authority consenting and compliance teams and are hence not accessible without significant investment of resources. Our data collection was therefore constrained to discrete readings and regular monitoring data within Regional Council and Unitary Authority groundwater level databases and the New Zealand Geotechnical Database.

Data Request
---------------

A data request was sent out to 16 New Zealand councils in March 2023; this included all 11 regional councils and five unitary authorities. The data request sought all groundwater level data; this included sites additional to any NGMP monitoring sites, as well as any discontinuous or sporadic readings. The aim was to collect as much national data as possible, including sites with a single. We were open to receiving both groundwater depth and/or groundwater elevation data on the proviso that it was specified to reduce data processing error. We also requested standard metadata for each site, with a minimum metadata requirement of:

- Unique site identifier (e.g. site number)
- Grid reference in NZTM
- Well depth

Our preferred metadata requirements included:

- Screen top & bottom depth
- Surveyed elevation of the ground surface at the measuring point
- The distance between the measuring point and the general ground surface.

The data were received in Excel and csv formats, with various degrees of completeness and processing. Data management and storage varied from council to council hence processing to standardise the data was required.


Alongside the direct requests to regional councils and unitary authorities, data was also pulled from Tethys (https://github.com/tethys-ts), which allows hilltop based data to be accessed and downloaded. For councils that had relevant and up-to-date data in Hilltop, it meant we did not have to rely on a response to the direct request, and saved time in the data collection and processing.

A brief summary of the data collected from each council is provided below.

.. include:: ../tables/data_provided_summary.rst


Data Processing
------------------

The data was processed using Python. The scripts used to process the data are available on GitHub; these are open source, and we encourage others to use and adapt them for their own purposes, as well as flag any issues or areas of improvement.


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
    - The datasets were given a quality rating based on their type and source

.. todo is there a quality rating for the datasets?  If so, where is it? and describe...

    - The data was checked for any duplicates and removed
- Metadata Synthesis and Alignment
    - Metadata processing paralleled the data cleaning steps, with additional emphasis on ensuring alignment between site names in the metadata and the GWL data.
    - The metadata schema encapsulated a comprehensive array of fields, ranging from well names and depths to spatial coordinates and screening details.
    - Groundwater elevations were meticulously derived from ground elevation plus collar height (where available) minus depth to water, except for instances where councils provided elevations in NZVD2016.
- Data Aggregation and Quality Assurance
    - The processed data from various sources were coalesced into a singular dataset. This aggregation involved strategic merging and deduplication, governed by predefined rules to ensure data integrity.
    - Quality control measures, including data and metadata checks, were instituted to uphold accuracy and reliability.
- Storing and Accessing Processed Data
    - The culminated GWL data and metadata were systematically stored in an HDF5 store, facilitating ease of access and analysis.
    - Provisions were made to recalculate and update the stored data as necessary, ensuring the database can remain current and reflective of the most recent submissions.
- Assumptions and Usage Considerations
    - A fundamental assumption is that depth-to-groundwater measurements below the ground surface are positive, with negative readings indicative of artesian conditions. This necessitated sign adjustments and validation against council records.
    - In cases where well depth information was unavailable, wells were presumed shallow rather than being excluded from the dataset.

.. todo How does this manifest in the output database - is there a particular value assigned?

    - Specific regional peculiarities, such as the assumed + 100 m offset for coastal groundwater elevations provided by the Otago Regional Council, were duly considered and adjusted.
    - For wells where the maximum depth to water exceeded the reported well depth, an assumption was made that the well depth equaled the maximum depth to water plus an additional 3 metres.

.. todo got here in integrating ZE edits

Statistical Analysis of Water Table Variation
-------------------------------------------------
The end use case of this dataset is to produce maps of steady-state depth to water (DTW) at a national scale, aiding in the identification of areas at risk of groundwater inundation. Simple statistical analyses were performed to uncover any prominent traits within the data by undertaking the following steps:

-  Categorization by Depth:
    - The dataset was divided into three depth categories:
    - Category 1: Sites with DTW less than 10 meters.
    - Category 2: Sites with DTW between 10 and 30 meters.
    - Category 3: Sites with DTW greater than 30 meters.

- Sub-setting by Number of Readings:
    - Only sites with more than 30 readings were considered for further analysis. This threshold was chosen as a rule of thumb to ensure a reliable calculation of the standard deviation.

- Statistical Calculations:
    - For each site in the subset, the following statistical measures were computed:
        - Mean: The average depth to water.
        - Standard Deviation: A measure of the variation in water levels.
        - Minimum: The lowest recorded water level.
        - Maximum: The highest recorded water level.

- Grouping by Mean DTW:
    - The data was further grouped by the mean DTW to analyze combined statistics across different groups. This grouping allows for a comparison of water level characteristics across sites with similar mean DTW values.

This structured approach to data analysis ensures a comprehensive understanding of the depth to water across various sites. By categorising, sub-setting, and computing key statistics, we can identify patterns and traits that are crucial for assessing groundwater inundation risks on a national scale.

Results and discussion
============================

The resulting dataset is a national depth to water dataset for New Zealand; the groundwater level data and metadata are available as a complete dataset which can be used for national groundwater modelling, and to better understand the potential of shallow groundwater in New Zealand.
The dataset is available as an output of the open source GitHub code. If you are interested in the input datasets so you can run the code for yourself, please get in contact with us and we can provide them.

The dataset will be used within the Future Coasts project for a number of research aims and purposes including the development of national scale depth to water estimates and probability maps using statistical models to inform risk assessments.
We hope that making the data available here will reduce the barrier to entry for other researchers and organisations to use this data for their own purposes.
We envisage that this dataset will be useful for a range of other projects as it provides a cleaned and queryable national dataset of groundwater level data.


Description of Dataset
-----------------------------------
The dataset comprises a comprehensive collection of groundwater monitoring sites, spanning a significant temporal range from as early as December 29, 1899, however as shown in the figure below, the dataset is overwhelmingly composed of younger data (with more than half of the sites and records being measured after the mid-late 2000s.  The cumulative number of sites and records shown by data source is available in the supplementary material and `GitHub repository <https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water>`_.

.. figure:: ../_static/cumulative_n_records.png
   :alt: Cumulative number of records by source
   :align: center

A statistical summary of the dataset is provided below.

.. include:: ../tables/full_dataset_summary.rst

Investigating the dataset by source reveals distinct patterns in data collection and density.
Notably, Environment Canterbury (Ecan) stands out with the highest number of observations with many observations at each site.
This contrasts the New Zealand Geotechnical Database (nzgd) which has many fewer observations per site (frequently <= 2 readings/site).
Otago Regional Council (orc) provided data for fewer monitoring sites, but what is monitored has significant data density.
These variations highlight the diversity of monitoring efforts and data densities across different sources.
Collectively, these statistics underscore the heterogeneity of groundwater monitoring across regions, influenced by the varying goals (e.g. geotechnical investigations), methodologies, and resources of different data sources.
Further summary statistics of the data by the source are provided below.


.. include:: ../tables/by_source_summary.rst



.. todo spatial coverage of data (by n records)
.. todo data add data density layer calculation here???



Statistical Description of Depth to Water Variance
-------------------------------------------------------

For the sake of brevity the detailed results of the statistical analysis of the depth to water variance are provided in the supplementary material and are available on the `GitHub repository <https://github.com/Komanawa-Solutions-Ltd/komanawa-nz-depth-to-water>`_.

We will provide a brief summary of the results here. All depth categories have the potential for water to reach the surface. For depth category 3 (deep wells > 30m), and likely for category 2 (well depth >10 m), this likely indicates semi-confined to confined artesian conditions. In depth category 1 (shallow wells, < 10m), the depth to water exhibits little variation in the shallower bins, suggesting wells that are near a boundary condition or wells with high specific yields. As depth increases, the variability in the depth to water also increases, as evidenced by larger ranges and higher standard deviations. For instance, in depth category 1, the standard deviation median increases from 0.077 in the <0.1m bin to 0.48 in the 6.36m bin. Notably, the skewness suggests a tendency towards shallower water levels in many records, despite the large possible ranges in depth. This is observed in the negative skewness values that become more pronounced with increasing depth, indicating that while the average water levels are deeper, there are frequent instances of shallower depths. The kurtosis values further highlight the presence of notable outliers and extreme values. As depth increases, the kurtosis medians remain high or increase, indicating distributions with frequent extreme values. This pattern is consistent across other depth categories, where deeper bins show increased kurtosis, suggesting that extreme values become more apparent with depth. Overall, the statistics indicate that as depth increases, not only does the variability in water levels increase, but the presence of outliers and extreme values also becomes more pronounced. Finally, the statistics suggest the data is skewed and leptokurtic, meaning the data is not normally distributed and the mean and standard deviation are not necessarily representative of the data.

.. include:: ../tables/stats_depth_cat_1.rst

The above table already shows the data does not follow a gaussian distribution, as the skewness and kurtosis values are not close to 0 and 3 respectively.
The statistics suggest the data is skewed and leptokurtic, meaning the data is not normally distributed and the mean and standard deviation are not necessarily representative of the data.


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

Finally we have some specific recommendations that could be undertaken to improve the dataset we have produced:

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


.. include:: supplmental_information.rst