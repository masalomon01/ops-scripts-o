# This script will grab data from the Base Camp API in order to get data about the app/network/algorithm releases and then gets the relevant data and
# puts it into the database. This is in order to analyze the effects that various releases have on our users and product.

# High-Level Idea: This function works by first getting all data in the database and then all of the data in the app/network/algorithm  
# release Basecamp (has to access to different endpoints in order to get complete to-dos and incomplete to-dos) and stores all of the 
# information in two dictionaries. The program goes through both dictionaries and compares which todos are out of date in
# the database and which todos aren't in the database at all. It then runs the corresponding SQL command in order to get up to date data in the database.

# NOTE: "City" means all cities and "Module" means no specific module

import mysql.connector
from datetime import datetime
import requests
import json

# This method is to get the release nomenclature from the title of the todo list. If it follows the nomenclature, it will return
# an array with the appropriate data. If the todo list title doesn't follow the nomenclature will return null
def get_release_nomenclature(title):
	split_title = title.split(', ')
	if(len(split_title) == 5): # if the correct number of commas it returns the standard nomenclature
		return [split_title[0], split_title[1], split_title[2], split_title[3], split_title[4]]
	else:
		return None  # returns NULL if not correct number of commas


# This method creates and returns a connection to the MySQL database logged in with Eddie's account.
def DB_connect():
	cnxn = mysql.connector.connect(user='eddie', password='eddie1234',
	                              host='192.168.1.95', port = 3306,
	                              database='ops')
	return cnxn


# This method takes two parameters, table_name and cnxn. It uses the cnxn created in order to 
# access all of the data in the table named table_name. It then returns a dictionary with the primary
# key of the table as the key of the dictionary, with a list containing the rest of the row as the data
# of the dictionary.
def get_current_data(table_name, cnxn):
	sql_statement = 'select * from %s' % table_name  # the SQL statement that is to be run to get all of the information from the database
	data_tuple = []  # the data is originally returned as a list of tuples and is stored in this variable
	data_dict = {}  # the data is better handles as a dictionary, so code will transform the list of tuples into a dictionary if lists
	cursor = cnxn.cursor()
	cursor.execute(sql_statement)  # executing the sql and storing the data
	data_tuple = cursor.fetchall()

	for i in data_tuple:  # transforming the list of tuples into a dictionary of lists with the primary key being the key of the dict
		# FORMAT: data_dict[ReleaseLogID] = [Module, Server/App/Network, City, Description, Completed, AddDate, ModDate, ExpectedDate, Environment]
		data_dict[i[0]] = list(i[1:])
	
	cursor.close()
	return data_dict  # returning the dictionary


# This method takes three parameters, company_id, project_id, and end_string. The company_id is the id that basecamp gave to Metropia which 
# allows us to get our data from their API. the project_id is the project in Basecamp where we are getting data from. The end_string
# is how to differentiate between the two paths that this method has to go into. If we are trying to get incomplete to-do lists, then
# end string will be equal to an empty string, but if we are looking for completed to-do lists, then end_string will be equal to '/completed'
# in order to give the correct path in order to get the data that we want (https://github.com/basecamp/bcx-api/blob/master/sections/todolists.md) has API path info
# This method will return a dictionary with the todo list id as the key for the dicionary.
def get_new_data(company_id, project_id, end_string):
	data_dict = {}  # dict object which stores all of the data
	username = 'edwardrichter@email.arizona.edu'  # credentials for Eddie's Basecamp account
	pwd = 'SantaLucia123'

	todo_url = 'https://basecamp.com/%s/api/v1/projects/%s/todolists%s.json' % (company_id, project_id, end_string)  # creating the url for the basecamp API
	print 'making request to %s' % todo_url
	response = requests.get(todo_url, auth=(username, pwd))  # making the request

	if response.status_code != 200:  # if the request doesn't return 200 then report and exit
		print 'Error, status code was: %d' % response.status_code
		exit(1)

	todos = response.json()  # getting the json response and storing it

	for i in todos:  # iterating thorugh json response
		nomenclature = get_release_nomenclature(i['name'])  # checking/getting the nomenclature
		if nomenclature != None and i['id'] != example_id and i['id'] != test_id:  # if follows the nomenclature
			# have to format it somewhat awkwardly to stay consistent with the format of the database (might just change the order of the data in the db or use dict)
			if i['description'] == None:  # this is so i['description'] is still a string so can call replace method on it
				i['description'] = ''

			data_dict[i['id']] = [nomenclature[2].replace('\'', '\'\''), nomenclature[0].replace('\'', '\'\''), nomenclature[3].replace('\'', '\'\''), i['description'].replace('\'', '\'\''), i['completed'], datetime.strptime(i['created_at'].split('.')[0], "%Y-%m-%dT%H:%M:%S"), datetime.strptime(i['updated_at'].split('.')[0], "%Y-%m-%dT%H:%M:%S"), nomenclature[4].replace('\'', '\'\''), nomenclature[1].replace('\'', '\'\'')] 
		else:  # if doesn't follow the nomenclature
			print '%s is not following nomenclature with their title "%s", so will skip' % (i['creator']['name'], i['name'])  # won't get the data

	return data_dict  # returning the dictionary


# this method takes in current_data, new_data, cnxn, and table_name. It compares the data currently in the db (current_data) with the
# data getting sent from Basecamps API (new_data) and checks to see what todo lists are out of date in the database, and which todo lists
# aren't in the todo list. It then executes the correct SQL statements in order to get up to date data in the db.
def update_db(current_data, new_data, cnxn, table_name):

	cursor = cnxn.cursor()
	for todo_id, attributes in new_data.iteritems():  # going through new_data because there is more of them
		if not (todo_id in current_data):  # if we don't have the ticket in the database
			print '%d should be added' % todo_id
			values = (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, todo_id) + tuple(attributes)
			sql = '''insert into %s (%s.ReleaseLogID, %s.Module, %s.`Server/App/Network`, %s.City, %s.Description, %s.Completed, %s.AddDate, %s.ModDate, %s.ExpectedDate, %s.Environment) values (%d, '%s', '%s', '%s', '%s', %s, '%s', '%s', '%s', '%s')''' % values
		elif (todo_id in current_data) and (current_data[todo_id][6] < new_data[todo_id][6]):  # if we have the ticket but the information is out of date
			print '%d should be updated' % todo_id
			values = (table_name, table_name, new_data[todo_id][0], table_name, new_data[todo_id][1], table_name, new_data[todo_id][2], table_name, new_data[todo_id][3], table_name, new_data[todo_id][4], table_name, new_data[todo_id][5], table_name, new_data[todo_id][6],table_name, new_data[todo_id][7], table_name, new_data[todo_id][8], table_name, todo_id)
			sql = '''update %s set %s.Module = '%s', %s.`Server/App/Network` = '%s', %s.City = '%s', %s.Description = '%s',%s.Completed = %s, %s.AddDate = '%s', %s.ModDate = '%s', %s.ExpectedDate = '%s', %s.Environment = '%s' where %s.ReleaseLogID = %d''' % values
		else:  # if the data is up to date.
			print '%d is chin-chilling' % todo_id
			continue

		# This will try to encode and execute the sql. If it failed it will note it in the log, but the code will still go on. This is just
		# because if someone messes up the nomenclature it doesn't stop the whole script
		try:
			#print sql.encode('utf-8')
			cursor.execute(sql.encode('utf-8'))
			cnxn.commit()
		except Exception, detail:
			print 'Execution of SQL failed. Here is detail: %s' % detail

	cursor.close()


# "Declaring" all vairiables because I am a C programmer at heart
release_log_table = 'ops.release_log'  # the name of the iOS bitbucket table
current_data = {}  # the dictionary that stores the data in the Android table
new_incomplete_data = {}  # the dicionary that stores all data for active (incomplete) to-do llists
new_completed_data = {}  # the dictionary that stores all data for inactive (complete) to-do lists
all_new_data = {}  # this will store the concatenation of new_incomplete_data and new_completed_data once they are populated
metropia_id = '2836926'  # our basecamp id
release_project_id = '9534778'  # the App/Network/Algorithm release project id
example_id = 39002308  # this is the id of the example of the nomenclature, it follows the nomenclature but have to ignore because it is just a dummy
test_id = 39173032  # this is the id of a test that I made

print 'getting current data from database'
cnxn = DB_connect()  # first database connection
current_data = get_current_data(release_log_table, cnxn)  # getting current data from db
cnxn.close()

print 'getting new data from basecamp'
new_incomplete_data = get_new_data(metropia_id, release_project_id, '')  # getting incomplete to-do list data from basecamp
new_completed_data = get_new_data(metropia_id, release_project_id, '/completed')  # getting complete to-do list data from basecamp
all_new_data = dict(new_incomplete_data.items() + new_completed_data.items())  # combining complete and incomplete to get all data from basecamp

print 'updating database data'
cnxn = DB_connect()  # second database connection
update_db(current_data, all_new_data, cnxn, release_log_table)  # updating data in the release_log table
cnxn.close()