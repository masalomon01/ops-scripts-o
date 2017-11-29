# This code is for comparing the M+ network to current Metropia network and Google network.
import csv
import requests


# This method gets the input data from a csv and returns the data in a nested array. The method takes in the
# name of the file that it is reading from
def get_input_data(file_path):
	print 'reading input data'
	input_data = []
	with open(file_path, 'rb') as f:  # getting input data
		reader = csv.reader(f, delimiter=' ', quotechar='|')
		for row in reader:
			input_data.append(', '.join(row).split(','))  # turning the data into a list, and appending it to the main list
	return input_data


# This method gets three lists as inputs, and returns one list with all the data combined. This is just to combine all of the
# data into one list in the order wanted in the ouput csv.
def combine_lists(input_data, production, sandbox, google):
	print 'combining all of the data'
	all_data = []
	for i, item in enumerate(production):  # enumerating through production, could be any because they all have the same size
		all_data.append(input_data[i]+item+sandbox[i]+google[i])  # appending the three nested arrays combined into one array
	return all_data


# This method gets the input file name and an array of the input data. It will write that list to the csv with the path of the
# argument file_path
def write_output_data(file_path, input_data):
	print 'writing output data'
	with open(file_path, 'wb') as f:
		writer = csv.writer(f)
		for i in input_data:
			writer.writerow(i)


# This method gets passed the a dict for either metropia sandbox or production which contains
# the urls and ports for the different portal servers, a list of input data, and the url of the api debugger it then returns 
# the data from the respective server (sandbox or production)
def get_metropia_api_data(parade_url_dic, api_debugger_url, input_data):
	print 'getting data from: ' + api_debugger_url  # just to show if getting information from sandbox or production in log code prints out
	iterdata = iter(input_data)
	next(iterdata)  # to get past the headers
	count = 2  # this is equal to the row of the csv, just to keep track of where the code is
	api_data = []  # a list that will contain all of the api data

	for i in iterdata:  # iterating through all the data without the headers
		url = parade_url_dic[i[0]]  # getting the correct url and port number for the city
		api_paramaters = 'startlat=%s startlon=%s endlat=%s endlon=%s' % (i[1], i[2], i[3], i[4])  # these are the paramaters that have to change with each request
		api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
		response = requests.get(url+api_paramaters)  # concatenating the parade url and port number with the parameters
		if response.status_code != 200:  # if the error is something other than 400 or 200 will just exit because that is unexpected and shouldn't happen.
		    print('Status:', response.status_code)  # printing out useful debugging information
		    print url+api_paramaters
		    exit(1)
		elif not response.json():  # parade will not return anything if it can't find a route, so cannot give more information on why no route is found. Could be possible to when this hapens ping portal to see what the problem was.
			print 'Parade returned nothing with the following url: %s. Will skip this and continue.' % (url+api_paramaters)
			api_data.append(['NULL', 'NULL', 'NULL', 'NULL'])
			count = count + 1  # just to be consistent with count
			continue
		data = response.json()
		api_data.append([data[0]['DISTANCE'], data[0]['ESTIMATED_TRAVEL_TIME'], data[0]['FFROUTE_TRAVEL_TIME'], api_debugger_url+api_debugger_paramaters])  # appending distance, estimated travel time, benchmark travel time
		
		print count  # for logging purposes, count is the row of the csv file. Also printing out the url in case there is an error the person running the command can test it out in their browser
		print url+api_paramaters
		count = count + 1
	return api_data


# this method gets passed the url for the google api and and a list of input data, it then returns the data from
# the google api data in a list.
def get_google_api_data(url, input_data):
	print 'getting google data'
	iterdata = iter(input_data)
	next(iterdata)  # to get past the headers
	count = 2
	API_key = 'AIzaSyCtZ8znVQe6VR6gbNF3Rgo9sC35m99hRAg'  # API key, might store this in a file if the functionality of this script grows
	api_data = []

	for i in iterdata:  # iterating through all of the input data other than the headers
		paramaters = 'origins=%s,%s&destinations=%s,%s&key=%s' % (i[1], i[2], i[3], i[4], API_key)  # these are all of the paramaters that we are to change
		response = requests.get(url+paramaters)  # accessing the url plus the modified paramaters for this particular set of data
		print url+paramaters
		if response.status_code != 200:  # will exit if google returns anything other than 200
		    print('Status:', response.status_code)
		    print url+paramaters
		    exit(1)
		data = response.json()
		if data['rows'][0]['elements'][0]['status'] == 'OK':  # will have a route if status is ok
			api_data.append([round(data['rows'][0]['elements'][0]['distance']['value']*0.000621371, 2), round(data['rows'][0]['elements'][0]['duration']['value']/60.0, 0)])  # appending distance and duration and convering to minutes and miles
			print 'row: ' + str(count) + ' distance: ' + str(round(data['rows'][0]['elements'][0]['distance']['value']*0.000621371, 2)) + ' time: ' + str(round(data['rows'][0]['elements'][0]['duration']['value']/60.0, 0))
		else:
			api_data.append(['NULL', 'NULL'])  # it occasionally happens where google can't find a route (I don't know why I thought they were good)
			print 'The following URL could not get a route from google: %s' % (url+paramaters)
		count = count + 1

	return api_data


print 'starting the zayne train'

input_file_name = 'for_compare_routes.csv'
output_file_name = 'compare_output_data.csv'
production_api_debugger = 'http://production.metropia.com/v1/static/debug.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'  # hardcoded url and parameters for API debugger
sandbox_api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
google_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'  # the google API that is being used to calculate distance and time with free flow conditions
production_data = []
sandbox_data = []
google_data = []

hardcoded_parade_parameters = '/getroutes/departtime=02:00 speed=0 course=208 occupancy=1 vehicle_type= etag=true toll=true hot=true hov=true '  # these parameters are for all parade urls
parade_data = {  # contains all of the ip addresses and port numbers to make calls to parade. Should put this in JSON file if functionality of script grows
	'sandbox': {
		'Tucson': 'http://54.68.167.139:8103' + hardcoded_parade_parameters,
		'Austin': 'http://54.68.167.139:8102' + hardcoded_parade_parameters,
		'ElPaso': 'http://54.68.167.139:8107' + hardcoded_parade_parameters,
		'BayArea': 'http://54.68.167.139:8104' + hardcoded_parade_parameters,
		'Newyork': 'http://54.186.92.29:8105' + hardcoded_parade_parameters,  # using production NewYork because sandbox NewYork is down
		'Taipei': 'http://54.149.241.76:8109' + hardcoded_parade_parameters
	},
	'production': {
		'Tucson': 'http://54.68.1.188:8093' + hardcoded_parade_parameters,
		'Austin': 'http://54.218.124.159:8092' + hardcoded_parade_parameters,
		'Newyork': 'http://54.191.199.234:8095' + hardcoded_parade_parameters,
		'ElPaso': 'http://54.191.194.177:8097' + hardcoded_parade_parameters
	}
}

input_data = get_input_data(input_file_name)  # getting the input data from the input csv file. contains startlon, startlat, endlon, and endlat  
production_data = [['production_distance', 'production_estimated', 'production_benchmark', 'production_api_debugger']] + get_metropia_api_data(parade_data['production'], production_api_debugger, input_data)  # getting data from production
sandbox_data = [['sandbox_distance', 'sandbox_estimated', 'sandbox_benchmark', 'sandbox_api_debugger']] + get_metropia_api_data(parade_data['sandbox'], sandbox_api_debugger, input_data)  # getting data from sandbox
google_data = [['google_distance', 'google_estimated']] + get_google_api_data(google_url, input_data)  # getting the google data
write_output_data(output_file_name, combine_lists(input_data, production_data, sandbox_data, google_data))  # writing all of the data to the output csv file