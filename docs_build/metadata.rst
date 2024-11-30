Water Level Data column meanings/metadata
=========================================


* wl_site_name
    * long_name: site name
    * description: name of the site, the flag values and meanings are enumerate(ds["site_name"][:])
    * units: None

* wl_date
    * _FillValue: 0
    * long_name: water level sampling date
    * units: days since 1899-01-01T00:00:00
    * missing_value: 0
    * origin: 1899-01-01T00:00:00
    * description: Note there are significant numbers of observations in 1900, this is likely a placeholder date, but we have not converted to NAN as it is unclear

* wl_gw_elevation
    * long_name: ground water elevation
    * units: m
    * description: The groundwater elevation at the site on the date provided. Provided by the data provider, otherwise calculated if a groundwater depth reading
    * scale_factor: 0.1
    * add_offset: 0
    * datum: NZVD2016
    * missing_value: -32768

* wl_depth_to_water
    * long_name: depth to water
    * units: m
    * description: The depth to water reading at the site on the date provided to either ground level or measuring point. Provided by the data provider, otherwise calculated if a groundwater elevation was provided.
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* wl_depth_to_water_cor
    * long_name: depth to water corrected
    * units: m
    * description: Depth to water from from ground surface e.g. corrected for collar height if available.
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* wl_water_elev_flag
    * long_name: water elevation quality flag
    * flag_values:
        * 0: no_data
        * 1: logger
        * 2: manual
        * 3: static_oneoff
        * 4: aquifer_test
        * 5: other
    * units: None

* wl_dtw_flag
    * long_name: depth to water quality flag
    * flag_values:
        * 0: no_data
        * 1: logger
        * 2: manual
        * 3: static_oneoff
        * 4: calculated_from_gw_elevation
        * 5: aquifer_test
        * 6: other
    * units: None

* wl_water_elev_flag
    * long_name: water elevation quality flag
    * flag_values:
        * 0: no_data
        * 1: logger
        * 2: manual
        * 3: static_oneoff
        * 4: aquifer_test
        * 5: other
    * units: None



Metadata column meanings/metadata
=================================


* site_name
    * long_name: name of the site
    * description: A unique identifier for each well, combining the well name and the source provider, where the well name is the name provided by the data provider and the source provider is the name of the data provider. For example, a well named "well1" from the source "source1" would have a site name of "well1_source1".
    * units: None

* rl_source
    * _FillValue: 0
    * long_name: source of reference level data (if not supplied)
    * flag_values:
        * 1: marlborough/marlborough_2018
        * 2: marlborough/marlborough_2020-2022
        * 3: marlborough/blenheim_2014
        * 4: canterbury/kaikoura_2016-2017
        * 5: manawatu-whanganui/whanganui-urban_2020-2021
        * 6: 8m_dem
        * 7: wellington/kapiti-coast_2021
        * 8: manawatu-whanganui/manawatu-whanganui_2022-2023
        * 9: manawatu-whanganui/manawatu-whanganui_2015-2016
        * 10: southland/southland_2020-2023
        * 11: manawatu-whanganui/palmerston-north_2018
        * 12: wellington/wellington_2013-2014
        * 13: hawkes-bay/hawkes-bay_2020-2021
        * 14: waikato/waikato_2021
        * 15: waikato/thames_2017-2019
        * 16: auckland/auckland-south_2016-2017
        * 17: taranaki/taranaki_2021
        * 18: waikato/hamilton_2019
        * 19: waikato/huntly_2015-2019
        * 20: auckland/auckland-north_2016-2018
        * 21: waikato/reporoa-and-upper-piako-river_2019
        * 22: bay-of-plenty/bay-of-plenty_2019-2022
        * 23: canterbury/christchurch_2020-2021
        * 24: northland/northland_2018-2020
        * 25: canterbury/canterbury_2020-2023
        * 26: canterbury/banks-peninsula_2023
        * 27: otago/coastal-catchments_2021
        * 28: nelson/top-of-the-south-flood_2022
        * 29: wellington/hutt-city_2021
        * 30: canterbury/selwyn_2023
        * 31: canterbury/canterbury_2018-2019
        * 32: wellington/upper-hutt-city_2021
        * 33: wellington/wellington-city_2019-2020
        * 34: tasman/tasman-bay_2022
        * 35: tasman/abel-tasman-and-golden-bay_2023
        * 36: otago/wanaka_2022-2023
        * 37: otago/otago_2016
        * 38: otago/central-otago_2022-2023
        * 39: wellington/porirua_2023
        * 40: hawkes-bay/gisborne-and-hawkes-bay-cyclone-gabrielle-river-flood_2023
        * 41: canterbury/timaru-rivers_2014
        * 42: west-coast/west-coast_2020-2022
        * 43: gisborne/gisborne_2023
        * 44: canterbury/hurunui-rivers_2013
        * 45: otago/queenstown_2021
        * 46: canterbury/christchurch-and-ashley-river_2018-2019
        * 47: canterbury/kaikoura-and-waimakariri_2022
        * 48: canterbury/canterbury_2016-2017
        * 49: canterbury/hawarden_2015
        * 50: canterbury/mackenzie_2015
        * 51: otago/central-otago_2021
        * 52: tasman/tasman_2020-2022
        * 53: gisborne/gisborne_2018-2020
        * 54: tasman/tasman_2008-2015
        * 55: southland/stewart-island-rakiura-oban_2021
        * 56: tasman/motueka-river-valley_2018-2019
        * 57: tasman/golden-bay_2017
        * 58: canterbury/christchurch-and-selwyn_2015
        * 59: otago/queenstown_2016
        * 60: otago/balclutha_2020
    * description: reference level was filled with the best avalible DEM source. A values like "canterbury/selwyn_2023" means the reference level was filled with LIDAR from the canterbury/selwyn survey in 2023 see: https://github.com/linz/elevation. A value of "8m dem" means the reference elevation was filled with https://data.linz.govt.nz/layer/51768-nz-8m-digital-elevation-model-2012/
    * missing_value: 0
    * units: None

* source
    * _FillValue: 0
    * long_name: source of data
    * flag_values:
        * 1: mdc
        * 2: hrc
        * 3: src
        * 4: gwrc
        * 5: wrc
        * 6: auk
        * 7: nzgd
        * 8: nrc
        * 9: ncc
        * 10: bop
        * 11: wcrc
        * 12: ecan
        * 13: orc
        * 14: gdc
        * 15: trc
        * 16: tdc
        * 17: hbrc
        * 18: tcc
    * missing_value: 0
    * units: None

* nztm_x
    * long_name: x coordinate
    * units: m
    * epsg: 2193

* nztm_y
    * long_name: y coordinate
    * units: m
    * epsg: 2193

* reading_count
    * long_name: number of readings
    * units: count

* mean_gwl
    * long_name: mean ground water level
    * units: m
    * datum: NZVD2016
    * description: calculated from this dataset for ease of use
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* median_gwl
    * long_name: median ground water level
    * units: m
    * datum: NZVD2016
    * description: calculated from this dataset for ease of use
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* std_gwl
    * long_name: std ground water level
    * units: m
    * datum: NZVD2016
    * description: calculated from this dataset for ease of use
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* max_gwl
    * long_name: max ground water level
    * units: m
    * datum: NZVD2016
    * description: calculated from this dataset for ease of use
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* min_gwl
    * long_name: min ground water level
    * units: m
    * datum: NZVD2016
    * description: calculated from this dataset for ease of use
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* well_depth
    * long_name: well depth
    * units: m
    * description: The depth of the well, if known, as provided by the data provider. There is not clarity on what this value represents, it may be the depth of the well screen, or the depth of the well casing, or the depth of the well itself and it may be from the ground surface, the measurement point, or similar
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -2147483648

* bottom_bottomscreen
    * long_name: bottom of bottom screen
    * units: m
    * description: The depth of the end of the bottom screen, if known. If there is only one screen in the well, the end of screen depth will be recorded in bottom_topscreen. If there is more than one screen in the well, this value is the depth at which the last screen ends. It is unclear if this value is from the ground surface, the measurement point, or similar.
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -2147483648

* dist_mp_to_ground_level
    * long_name: distance from measurement point to ground level
    * units: m
    * description: The distance from the measuring point to the ground surface, if known. If it is 0, the measuring point is at the ground surface.
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* rl_elevation
    * long_name: reference level elevation
    * units: m
    * description: The elevation of the reference level, if known.
    * datum: NZVD2016
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* top_topscreen
    * long_name: top of top screen
    * units: m
    * description: The depth of the top of the top screen, if known. If there is only one screen in the well, the top of screen depth will be recorded in top_topscreen. If there is more than one screen in the well, this value is the depth at which the first screen starts. It is unclear if this value is from the ground surface, the measurement point, or similar.
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -2147483648

* mean_dtw
    * long_name: mean depth to ground water level
    * units: m
    * description: calculated from this dataset for ease of use
    * convention: positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* median_dtw
    * long_name: median depth to ground water level
    * units: m
    * description: calculated from this dataset for ease of use
    * convention: positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* std_dtw
    * long_name: std depth to ground water level
    * units: m
    * description: calculated from this dataset for ease of use
    * convention: positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* max_dtw
    * long_name: max depth to ground water level
    * units: m
    * description: calculated from this dataset for ease of use
    * convention: positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* min_dtw
    * long_name: min depth to ground water level
    * units: m
    * description: calculated from this dataset for ease of use
    * convention: positive values (+) are below the ground surface, negative values (-) are above the ground surface (artesian)
    * scale_factor: 0.1
    * add_offset: 0
    * missing_value: -32768

* start_date
    * _FillValue: 0
    * long_name: start date
    * units: days since 1899-01-01T00:00:00
    * missing_value: 0
    * origin: 1899-01-01T00:00:00
    * description: start date of the reading calculated from this dataset for ease of use

* end_date
    * _FillValue: 0
    * long_name: end date
    * units: days since 1899-01-01T00:00:00
    * missing_value: 0
    * origin: 1899-01-01T00:00:00
    * description: end date of the reading calculated from this dataset for ease of use


