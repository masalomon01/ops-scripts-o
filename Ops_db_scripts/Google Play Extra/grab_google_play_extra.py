# The function of this script is to use the Google Cloud API to download reports from the Google play store. This script will download the monthly reports
# that Google provides from the Google Play Store, then those csv's are parsed in order to grab relevent data, and then all of the relevent data
# that is to be put in the database is inserted into the operation database.

import io
from apiclient.http import MediaIoBaseDownload
import json
import csv
from httplib2 import Http
from oauth2client.service_account import ServiceAccountCredentials
from apiclient.discovery import build
import datetime
import os
import mysql.connector
import sys

# This method gets respective data (defined by type_data and year_month passed in) from the Google Cloud. Once it downloads that csv it will open the csv
# and get all of the data and return it as a dict keyed by the date. It then deletes the csv that it downloaded from Google Cloud.
def get_data(year_month, type_data ,subtype_data, json_file):
	report_to_download =  type_data + '_com.metropia.activities_' + year_month + subtype_data + '.csv' # path in google bucket to report
	data_dict = {}  # this is where all of the data will be returned
	print type_data  # for debugging/logging purposes
	output_file_name = (type_data + subtype_data + '_' + year_month + '.csv').replace('/', '') # have to get rid of '/' beacuse can't have those in file name
	try:
		credentials = ServiceAccountCredentials.from_json_keyfile_name(json_file, 'https://www.googleapis.com/auth/devstorage.read_only')
	except:
		print 'Error occured while loading credentials from json_file. Most likely incorrect path. Path given is: %s' % json_file
		sys.exit(1)  # terminating with failure
	storage = build('storage', 'v1', http=credentials.authorize(Http())) # creating storage object
	result = storage.objects().get_media(bucket=cloud_storage_bucket, object=report_to_download) # gets payload data from Google Cloud

	print 'creating %s' % output_file_name # for debugging/logging purposes
	file_to_download = io.FileIO(output_file_name, mode='w') # initializes file_to_download so data can be written to a csv from bytes
	downloader = MediaIoBaseDownload(file_to_download, result, chunksize=1024*1024) # defining the downlaoder

	done = False  # variable to see when download is done
	while not done:
	    status, done = downloader.next_chunk() # goes through chunk by chunk until the entire file is downloaded, done will be set equal to true when the last chunk is downloaded
	file_to_download.close()  # once file is downloaded, we can close the FileIO

	data_initial = open(output_file_name)  # opens the recently downloaded file whose encoding is ISO-8859-1 (<-- not sure if relevant)
	data = csv.reader((line.replace('\0','') for line in data_initial), delimiter=",") # ignores all null lines in CSV file (<-- not sure if necessary)
	iter_data = iter(data)  # in order to skip the headers, have to make an iterable and skip the first row
	next(iter_data)  # skipping the first row

	
	for row in iter_data: # is going through all of the data
		try:
			data_dict[row[0]] = row[2:]  # creating the dictionary
		except IndexError, detail:  # if it doesn't have all of the data in the specific date
			continue

	data_initial.close()  # closing the file
	print 'deleting %s' % output_file_name
	os.remove(output_file_name)  # deleting the file downlaoded from Google, because it was already parsed for all relevent data 
	return data_dict  # returning the data

# This method takes in the lists of install, crash, and rating data and returns one list of all the data
# combined in the format we want. This makes it much easier to write the data into a csv and to write it to the
# database.
def combine_lists(install, crash, rating):
	total_data = []  # initializing the lists that I will use
	crash_list = []

	for date, array in rating.iteritems():  # iterating through rating because rating has every date in it, because it has the total average rating
		# there aren't crashes everyday, so it is possible that the crash list doesn't have every date, which is why checking is necessary
		if date in crash:  # if there is crash in that date
			crash_list = crash[date]
		else:  # if there is no crash data for that particular date
			crash_list = [0, 0]

		total_data.append(install[date] + crash_list + array + [date])  # appending all of the to the final list
	return total_data  # returning the array which contains all of the data


# This method creates and returns a connection to the MySQL database logged in with Eddie's account.
def DB_connect():
	cnxn = mysql.connector.connect(user='eddie', password='eddie1234',
	                              host='192.168.1.95', port = 3306,
	                              database='ops')
	return cnxn


# This method writes the data to the output that we want. As of now it takes in a csv file name, but it is possible for it to take in a name of a 
# table and then write all of the data to a database (which is the future plan once the data is approved)
def write_to_output(data):
	cnxn = DB_connect()  # connecting to the db
	cursor = cnxn.cursor()  # establishing a cursor
	table_name = 'google_extra_store'  # the name of the table it is writing to 

	for i in data:  # iterating through all of the data
		values = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9], i[10], i[11], i[12])
		sql = 'insert into %s (%s.CurrentDeviceInstalls, %s.DailyDeviceInstalls, %s.DailyDeviceUninstalls, %s.DailyDeviceUpgrades, %s.CurrentUserInstalls, %s.TotalUserInstalls, %s.DailyUserInstalls, %s.DailyUserUninstalls, %s.DailyCrashes, %s.DailyANRs, %s.DailyAverageRating, %s.TotalAverageRating, %s.ReportDate)' % (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name)
		sql += ' values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, \'%s\')' % values
		#print sql.encode('utf-8')
		cursor.execute(sql.encode('utf-8')) 
		cnxn.commit()


# This table gets a table_name, and returns the last time the table was updated, it will then return a date objcet
# that contains that data. This is necessary so no repeated data gets added to the db
def get_last_update_time():
	cnxn = DB_connect()  # connecting to the db
	cursor = cnxn.cursor()  # establishing a cursor
	table_name = 'google_extra_store'
	sql_statement = 'select %s.ReportDate FROM %s order by %s.ReportDate desc LIMIT 1;' % (table_name, table_name, table_name)  # getting the latest date
	cursor.execute(sql_statement)  # executing the sql and storing the data
	data = cursor.fetchone()[0]  # getting the last date
	cursor.close()  # closing everything
	cnxn.close()
	return data  # returning the date object

client_email = '587666638625-mv4u63duf2ge9eqlstgnonglifrt0e2c@developer.gserviceaccount.com' # client email which sends us reports
json_file = 'Google Play Analytics-a1233ad04d40.json' # json file in directory that grants us access to the service account service
cloud_storage_bucket = 'pubsite_prod_rev_06472528785143111333' # the bucket that contains our google cloud storage (where the reports are stored.)

current_date = datetime.date.today() # getting the current date
first_day = current_date.replace(day=1) # getting the first day of the current month
last_date = first_day - datetime.timedelta(days=1) # going to the previous day of the first month, which will be in the last month
last_month = str(last_date)[5:7] # getting the month of the last month
last_year = str(last_date)[0:4] # getting the year of the last month (only would be different if it was december)

# this code is to be run every month. It is to get the last months data
# therefore the code will get the latest entry in the db and extract the month
# from that date object. Then, if the month in db is equal to the last month, then that
# means the code was already run this month and it has the most up to date data available
if get_last_update_time().month == int(last_month):
	print 'there is already up to date data in the db'
	print get_last_update_time()
	print last_month
	sys.exit(0)  # terminates successfully
else:
	print 'data should be updated'

install_data = get_data(last_year + last_month, 'stats/installs/installs' , '_overview', json_file) # gets raw data for installs
crash_data = get_data(last_year + last_month, 'stats/crashes/crashes' , '_overview', json_file) # gets raw data for crashes
rating_data = get_data(last_year + last_month, 'stats/ratings/ratings' , '_overview', json_file) # gets raw data for ratings

for data, array in rating_data.iteritems():  # replacing all 'NA' with NULL in the rating data
	if array[0] == 'NA':
		array[0] = 'NULL'

all_data = combine_lists(install_data, crash_data, rating_data)  # combining all of the data into one list in order to write it to the csv (or db)


write_to_output(all_data)  # writing all of the data to a csv