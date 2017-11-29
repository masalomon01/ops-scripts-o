# The function of this script is to use the App Figures API in order to download a report of how Metroipia
# is doing on both the App Store and the Google Play Store. We are using this service so we can compare the same stats to each other.
# This script will obtain the last time the tables it is writing to were updated, and get data from the last updated date to the current
# date minus 2 days. The minus 2 days is a necessary as a buffer becuase at the latest App Figures gets data 2 days late.

import requests
import csv
import datetime
import mysql.connector


# This method gets the review_data from end_date to the_day_before_date from whichever product key is passed in.
# It will access the review endpoint of the App FIgures API and then get the data, put it in a nested array and return that data.
def get_review_data(end_date, the_day_before_date, product_key):
	user = 'm.salomon@metropia.com' # credentials for App Figures
	pwd = 'metropia1234'
	client_key = '21336a056f0c4e889c8bb62fd63f25ec'
	page_num = 1  # this is necessary because if there is too much data the API returns the data in pages
	pages = 1
	# secret key: 4fbc8f47b564457bada6ac804be1b991

	end_date_string = end_date.strftime("%Y-%m-%d")  # creating string for the necessary dates so only have to do it once
	the_day_before_date_string = the_day_before_date.strftime("%Y-%m-%d")

	total_data = []  # initializing list which will store rating data

	# need this loop in order to continue to make requests if there are still more pages to get data from (if hit max will break out at bottom of loop)
	while True:

		# parameters used in API request
		parameters = '?start=%s&end=%s&products=%s&client_key=%s&page=%d' % (the_day_before_date, end_date, product_key, client_key, page_num)
		#parameters = '?products=%s&client_key=%s&page=%d' % (product_key, client_key, page_num)  test parameters for when there are multiple pages

		url_reviews = 'https://api.appfigures.com/v2/reviews/' + parameters  # creating the url
		print url_reviews  # for logging/debugging purposes
		response = requests.get(url_reviews, auth=(user, pwd))  # making a GET request
		if response.status_code != 200:  # if it returns anything that isn't 200 the code will print detail and exit. App Figures returns 500 if start_date < end_date which will happen if you run the script twice in one day.
			print 'Error on sales request. Status Code: %d' % response.status_code
			return total_data  # will return all of the data collected, usually will be an empty list.

		json_response = response.json()  # getting the data
		pages = json_response['pages']  # getting the number of pages
		reviews = json_response['reviews']  # getting an array of dictionaries of data about the reviews

		for i in reviews:  # iterating through all of the reviews in a given page
			# appending data
			if i['version'] == None:  # need to have this logic here because NULL won't have apostrophes around it, but a version will so need to figure out which one it is
				i['version'] = 'NULL'
			else:
				i['version'] = "'" + i['version'] + "'"
			total_data.append([i['author'], i['version'], i['title'], i['review'], i['stars'], i['store'], datetime.datetime.strptime(i['date'], "%Y-%m-%dT%H:%M:%S")])
		
		if page_num >= pages:  # if we are at the last page of the response we leave, if not we increate page # and keep going
			break
		else:
			page_num += 1

	return total_data  # returning the data



# This method gets passed all of the parameters in order to make an API request to App Figures. It then 
# gets that data, processes and calculates some data using other methods, and then returns a list
# of data in the format neede.
def get_data(end_date, the_day_before_date, product_key):
	user = 'm.salomon@metropia.com' # credentials for App Figures
	pwd = 'metropia1234'
	client_key = '21336a056f0c4e889c8bb62fd63f25ec'
	# secret key: 4fbc8f47b564457bada6ac804be1b991

	end_date_string = end_date.strftime("%Y-%m-%d")  # creating string for the necessary dates so only have to do it once
	the_day_before_date_string = the_day_before_date.strftime("%Y-%m-%d")

	total_data = {}  # initializing dictionaries that will store rating, sales, and total data
	rating_data = {}
	sales_data = {}

	# parameters used in API request
	parameters = '?start_date=%s&end_date=%s&products=%s&client_key=%s&group_by=date' % (the_day_before_date, end_date, product_key, client_key)

	url_sales = 'https://api.appfigures.com/v2/reports/sales/' + parameters  # creating url for API request
	url_ratings = 'https://api.appfigures.com/v2/ratings/' + parameters
	
	print url_sales  # gettting sales data
	response_sales = requests.get(url_sales, auth=(user, pwd))
	if response_sales.status_code != 200:
		print 'Error on sales request. Status Code: %d' % response_sales.status_code
		exit(1)
	
	print url_ratings  # getting rating data for this current week
	response_ratings = requests.get(url_ratings, auth=(user, pwd))
	if response_ratings.status_code != 200:
		print 'Error on ratings request. Status Code: %d' % response_ratings.status_code
		exit(1)

	sales_json_response = response_sales.json()  # getting sales data
	ratings_json_response = response_ratings.json()  # getting rating data

	for date, array in sales_json_response.iteritems():  # iterating through sales response
		if date != the_day_before_date.strftime("%Y-%m-%d"):  # making sure not to get first date
			sales_data[date] = [array['downloads'], array['updates']]  # populating dictionary

	for count, i in enumerate(ratings_json_response):  # iterating through ratings_json_response (which is actually an array)
		if i['date'] != the_day_before_date.strftime("%Y-%m-%d"):  # making sure not to get first date
			daily_average_rating = calc_daily_average_rating(count, ratings_json_response)  # getting the average of the day
			total_average_rating = calc_total_average_rating(i['stars'])  # getting the total average
			rating_data[i['date'].split('T')[0]] = [daily_average_rating, total_average_rating, i['stars'][4], i['stars'][3], i['stars'][2], i['stars'][1], i['stars'][0]]  # populating the dictionary

	return process_data(sales_data, rating_data)  # returning the processed data, which is an array with sales and ratings data


# This method takes in two dictionaries: sales and rating, and then returns a nested array that contains both sales and rating data
# it returns an array because it is easier to write arrays into csvs and databases than dictionaries
def process_data(sales, rating):
	total_data = []  # initializing total_data
	for date, array in sales.iteritems():  # iterating through sales (doesn't matter which one because both have same length)
		total_data.append([sales[date][0], sales[date][1], rating[date][0], rating[date][1], rating[date][2], rating[date][3], rating[date][4], rating[date][5], rating[date][6],  date])  # populating array
	return total_data


# this method takes in the count (element number of array) and the whole week of data in order to calculate the average rating of a particular day
def calc_daily_average_rating(count, week_data):
	daily_rating = [a - b for a, b in zip(week_data[count]['stars'], week_data[count - 1]['stars'])]  # creating a list of only one particular days ratings
	try:
		return (daily_rating[0] + daily_rating[1]*2 + daily_rating[2]*3 + daily_rating[3]*4+daily_rating[4]*5) / float(sum(daily_rating))  # calculating average daily rating
	except ZeroDivisionError:  # will divide by zero if there were no ratings on the current day
		return 'NULL'	


# this method takes in all of the rating data and calculates the average total rating
def calc_total_average_rating(data):
	try:
		return (data[0] + data[1] * 2 + data[2] * 3 + data[3] * 4 + data[4] * 5) / float(sum(data))
	except ZeroDivisionError:
		return 'NULL'

# this method takes in two parameters: file_name and date. data is a nested array which gets written to csv with the path
# defined by the file_name. This method will change in order to rewrite data to the database
def write_output(table_name, data):
	cnxn = DB_connect()  # connecting to the db
	cursor = cnxn.cursor()  # establishing a curso

	for i in data:  # iterating through all of the data
		if table_name == review_table_name:  # the sql changes depending on what table you are inserting into
			print i[6]   # for logging purposes
			values = (i[0].replace('\'', '\'\''), i[1], i[2].replace('\'', '\'\''), i[3].replace('\'', '\'\''), i[4], i[5], i[6]) 
			sql = 'insert into %s (%s.Author, %s.Version, %s.Title, %s.Description, %s.Rating, %s.Store, %s.AddDate)' % (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name)
			sql += ' values (\'%s\', %s, \'%s\', \'%s\', %s, \'%s\', \'%s\')' % values
			print sql
		else:
			print i[9]   # for logging purposes
			values = (i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[9])
			sql = 'insert into %s (%s.Downloads, %s.Updates, %s.DailyAverageRating, %s.TotalAverageRating, %s.TotalFiveStarCount, %s.TotalFourStarCount, %s.TotalThreeStarCount, %s.TotalTwoStarCount, %s.TotalOneStarCount, %s.ReportDate)' % (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name)
			sql += ' values (%s, %s, %s, %s, %s, %s, %s, %s, %s, \'%s\')' % values
		#print sql.encode('utf-8')
		cursor.execute(sql.encode('utf-8'))
		cnxn.commit()

def DB_connect():
	cnxn = mysql.connector.connect(user='eddie', password='eddie1234',
	                              host='192.168.1.95', port = 3306,
	                              database='ops')
	return cnxn


# This method gets a table_name, and returns the last time the table was updated, it will then return a date objcet
# that contains that data. This is necessary so no repeated data gets added to the db
def get_last_update_time(table_name):
	cnxn = DB_connect()  # connecting to the db
	cursor = cnxn.cursor()  # establishing a curso

	if table_name == review_table_name:  # have to differentiate because review table has datetime column while other tables just have date
		sql_statement = 'select %s.AddDate FROM %s order by %s.AddDate desc LIMIT 1;' % (table_name, table_name, table_name)  # getting the latest date
		cursor.execute(sql_statement)  # executing the sql and storing the data
		data = cursor.fetchone()[0]  # selecting the only value
		cursor.close()  # closing cursor
		cnxn.close()  # closing connection
		return data.date()
	else:
		sql_statement = 'select %s.ReportDate FROM %s order by %s.ReportDate desc LIMIT 1;' % (table_name, table_name, table_name)  # getting the latest date
		cursor.execute(sql_statement)  # executing the sql and storing the data
		data = cursor.fetchone()[0]
		cursor.close()
		cnxn.close()
		return data


day_ago = datetime.timedelta(days=-1) # defining timedelta objects
week_ago = datetime.timedelta(weeks=-1)
ios_product_key = '40995991116'  # defining product keys
google_product_key = '41046422052'
ios_store_table_name = 'ops.ios_store'  # defining table names
google_store_table_name = 'ops.google_store'
review_table_name = 'ops.review'

ios_last_update = get_last_update_time(ios_store_table_name)  # getting the last day each table was updated
google_last_update = get_last_update_time(google_store_table_name)
review_last_update = get_last_update_time(review_table_name)

end_date = datetime.date.today() + day_ago * 2  # need to have a 2 day buffer in case App Figures is late

iOS_data = get_data(end_date, ios_last_update, ios_product_key)  # getting ios data
google_data = get_data(end_date, google_last_update, google_product_key)  # getting google data
iOS_review_data = get_review_data(end_date, review_last_update - day_ago, ios_product_key)  # getting ios review data
google_review_data = get_review_data(end_date, review_last_update - day_ago, google_product_key)  # getting google review data

write_output(ios_store_table_name, iOS_data)  # writing ios data
write_output(google_store_table_name, google_data)  # writing google data
write_output(review_table_name, iOS_review_data + google_review_data)  # writing ios+google review data
