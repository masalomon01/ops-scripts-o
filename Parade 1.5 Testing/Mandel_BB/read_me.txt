FILES NEEDED TO RUN MANDEL_ESTIMATION:
To run the script you'll need the following files in your local directory:
1. Mandel_Use_Cases.csv
2. wkt file for the city you want to get the use_cases for needs to read in the following format: 'links_wkt_' + city + '.csv' for example links_wkt_elpaso.csv
3. This script reads the Mandel_Turn_Pairs file from http://mandel.metropia.com/cities/qaqc/ please be sure the files are updated for correct results

PARAMETERS TO CONTROL IN MANDEL_ESTIMATION:
1. city = name of the city you want to run #only elpaso, tucson, austin allowed for now
3. case_count = This controls the number of cases per avaliable mandel usecase (so if 60 cases are applicable in the city and you choose two that's a total of 120 usecases)
3. concurrent = number of concurrent api calls to each api

OBJECTIVE OF MANDEL ESTIMATION:
The objective of this script is to systematically test the estimation of mandel and compare improvements vs not improvements in each testing iteration.
This program gathers the data to compare the response of Developer, Sandbox and Google. So that if an Engineer is working and commits an improvement,
this tool can be used to compare the responses in SB vs new committed Developer, and with the baseline google. 
This program also commits to a DB so that we can use periscope visualization to easily understand in an aggregate form where the status of each
commit is and keeps a record for future uses. 

MANDEL_ESTIMATION DOES THE FOLLOWING:

1. Reads a csv file with all possible mandel use cases 'Mandel_Use_Cases.csv'
2. Reads a city wkt file
3. Reads the Mandel Turn Links and creates the unique case ids for all turnpairs
4. Creates all the use case data by doing the following:
	a. Get's X unique cases defined by case_count or user input per each possible use_case.
	b. From those use cases the script finds the point(lat, lon) at the beggining of the from link and at the end of the to link
	c. It merges all necessary data to create the input file in order to ping route apis
5. Gets the corresponding Mandel Data for that turn pair at Peak hour and FF hour
6. Get's the sum of the Trace data of the From and To Links at Peak and FF Hour
7. Writes Data as Input File for Debugging or Checking if Necessary 'Mandel_BB_Input_' + city + '.csv'
8. Gets city specific API data to ping Parade Dev, SB and Google
9. Prepares individual data for each API (DEV, SB and Google) to enable multithreathing. 
10. Starts Multi threads for each API
	a. First the Thread enables you to control the number of concurrent calls to the APIS
	b. Then the main work area pings each server the number of concurrent times with each attribute and collects all responses in a list
11. Thread waits for all threads to finish before continuing 
12. All of the responses are formated into one row per unique query combining responses for optimization
13. Output is written into a csv 'Mandel_Testing_Results_' + city + '.csv'
14. Outputs are also written into the ops MariaDB in .95 in the office
