# This script writes to the Android, iOS, and RouteDebugging Bitbucket repository databases. It is to be put on a scheduler and run every day in order to have
# up to date data on the bitbucket repositories.

# High-Level Idea: This function works by first getting all data in the database and then all of the data in the Bitbucket repos and stores
# all of the information in dictionaries. The program goes through all of these dictionaries and compares which tickets are out of date in
# the database and which tickets aren't in the database at all. It then runs the corresponding SQL command in order to get up to date data
# in the database. 

import mysql.connector
from api import API
from datetime import datetime


# The purpose of this function is to get the standard route debugging nomenclature, which is to be extracted from the ticket title.
# the format is server, module, city, description. This function is passed in the title as a whole and returns 4 strings, one for 
# each aspect of the nomenclature. If there isn't the correct number of commas the function just returns 4 empty strings
def get_route_debugging_nomenclature(title):
	split_title = title.split(',')
	if(len(split_title) == 4): # if the correct number of commas it returns the standard nomenclature
		return [split_title[0], split_title[1], split_title[2], split_title[3]]
	else:
		return ['', '', '', '']


# This method creates and returns a connection to the MySQL database logged in with Eddie's account.
def DB_connect():
	cnxn = mysql.connector.connect(user='eddie', password='eddie1234',
	                              host='192.168.1.95', port = 3306,
	                              database='ops')
	return cnxn


# This method gets the current bitbucket data in the database and then returns it as a dictionary mapped with the Bitbucket ticket number.
def get_current_data(table_name, cnxn):
	sql_statement = 'select * from %s' % table_name  # the SQL statement that is to be run to get all of the information from the database
	data_tuple = []  # the data is originally returned as a list of tuples and is stored in this variable
	data_dict = {}  # the data is better handles as a dictionary, so code will transform the list of tuples into a dictionary if lists
	cursor = cnxn.cursor()

	cursor.execute(sql_statement)  # executing the sql and storing the data
	data_tuple = cursor.fetchall()

	for i in data_tuple:  # transforming the list of tuples into a dictionary of lists
		data_dict[i[0]] = list(i[1:])

	cursor.close()
	return data_dict  # returning the dictionary


# This method gets the current bitbucket information that is in a given repository. It is then stored in a dictionary of same format as the database dictionary returned by the
# get_current_data method. This allows us to be able to compare the data in Bitbucket with the data in the database. 
def get_new_data(repo_owner, repo, api):
	start = 0 # starting point for the tickets to access
	limit = 50 # number of tickets to access, Max is 50. When no limit it defaults to 15.
	data_dict = {}

	tickets = api.get_issues(repo_owner, repo, start, limit) # just to get the number of tickets (api.count). might create get count method but it would do basically the same thing
	
	while start < api.count:  # will iterate through every ticket in the repo
		tickets = api.get_issues(repo_owner, repo, start, limit) # creating an API object that contains the 50 issue objects
		for ticket in tickets:  # iterating through all of the tickets returned by th get_issues method
				print 'getting current data from repo: %s ticket: %d' % (repo, ticket.issue_id)
				if repo == 'route-debugging':  # route-debugging repo has to be different in order to account for nomenclature
					new_nomenclature = get_route_debugging_nomenclature(ticket.title) # getting the nomenclature
					server = new_nomenclature[0]
					module = new_nomenclature[1]
					city = new_nomenclature[2]
					description = new_nomenclature[3]
					data_dict[ticket.issue_id] = [ticket.title, server, module, city, description, ticket.priority, ticket.status, ticket.kind, ticket.created_date, ticket.updated_date]  # populating the bitbucket data dictionary
				else:  # if there is no need for route debugging nomenclature
					data_dict[ticket.issue_id] = [ticket.title, ticket.priority, ticket.status, ticket.kind, ticket.created_date, ticket.updated_date]  # populating the bitbucket data dictionary
		start = limit + start # starts at the next set of issues
	return data_dict # have this returning the new first_empty row value so it can be writting in the file.

# This method updates the db depending on the differences between the current database data and the new data in bitbucket. It does this by first checking to see if the database has a certain ticket
# and then if it does, it checks to see if the data is up to date by comparing the UpdateDate of the Bitbucket data to the ModDate of the database data. It then runs SQL commands on the database
# in order to make the data up to date.
def update_db(current_data, new_data, cnxn, table_name):

	cursor = cnxn.cursor()
	for issue_id, attributes in new_data.iteritems():  # going through new_data because there is more of them
		print datetime.strptime(new_data[issue_id][-1].split('+')[0], "%Y-%m-%d %H:%M:%S")
		if not (issue_id in current_data):  # if we don't have the ticket in the database
			print '%d should be added' % issue_id
			if table_name == route_debugging_table:
				values = (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, issue_id, new_data[issue_id][0].replace('\'', '\'\''), new_data[issue_id][1], new_data[issue_id][2], new_data[issue_id][3], new_data[issue_id][4], new_data[issue_id][5], new_data[issue_id][6], new_data[issue_id][7], new_data[issue_id][8].split('+')[0], new_data[issue_id][9].split('+')[0])
				sql = '''insert into %s (%s.TicketID, %s.Title, %s.Server, %s.Module, %s.City, %s.Description, %s.Priority, %s.Status, %s.Kind, %s.AddDate, %s.ModDate) values (%d, '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')''' % values
			else:
				values = (table_name, table_name, table_name, table_name, table_name, table_name, table_name, table_name, issue_id, new_data[issue_id][0].replace('\'', '\'\''), new_data[issue_id][1], new_data[issue_id][2], new_data[issue_id][3], new_data[issue_id][4].split('+')[0], new_data[issue_id][5].split('+')[0])
				sql = '''insert into %s (%s.TicketID, %s.Title, %s.Priority, %s.Status, %s.Kind, %s.AddDate, %s.ModDate) values (%d, '%s', '%s', '%s',  '%s', '%s', '%s');''' % values
			cursor.execute(sql.encode('utf-8'))   # 
			cnxn.commit()
		elif (issue_id in current_data) and (current_data[issue_id][-1] < datetime.strptime(new_data[issue_id][-1].split('+')[0], "%Y-%m-%d %H:%M:%S")):  # if we have the ticket but the information is out of date
			print '%d should be updated' % issue_id
			if table_name == route_debugging_table:
				values = (table_name, table_name, new_data[issue_id][0].replace('\'', '\'\''), table_name, new_data[issue_id][1], table_name, new_data[issue_id][2], table_name, new_data[issue_id][3], table_name, new_data[issue_id][4], table_name, new_data[issue_id][5], table_name, new_data[issue_id][6], table_name, new_data[issue_id][7], table_name, new_data[issue_id][8].split('+')[0], table_name, new_data[issue_id][9].split('+')[0], table_name, issue_id)
				sql = '''update %s set %s.Title = '%s', %s.Server = '%s', %s.Module = '%s', %s.City = '%s', %s.Description = '%s', %s.Priority = '%s', %s.Status = '%s', %s.Kind = '%s', %s.AddDate = '%s', %s.ModDate = '%s' where %s.TicketID = %d''' % values
			else:
				values = (table_name, table_name, new_data[issue_id][0].replace('\'', '\'\''), table_name, new_data[issue_id][1], table_name, new_data[issue_id][2], table_name, new_data[issue_id][3], table_name, new_data[issue_id][4].split('+')[0], table_name, new_data[issue_id][5].split('+')[0], table_name, issue_id)
				sql = '''update %s set %s.Title = '%s', %s.Priority = '%s', %s.Status = '%s', %s.Kind = '%s', %s.AddDate = '%s', %s.ModDate = '%s' where %s.TicketID = %d''' % values
			cursor.execute(sql.encode('utf-8'))
			cnxn.commit()
		else:  # if the data is up to date.
			print '%d is chin-chilling' % issue_id

	cursor.close()


# "Declaring" all vairiables because I am a C programmer at heart
api = API("edwardrichter", "SantaLucia123")   # Creating an api object from the BitBucket API which needs to be in the same directory as this script
iOS_table = 'ops.ios_bitbucket'  # the name of the iOS bitbucket table
android_table = 'ops.android_bitbucket'  # the name of the android bitbucket table
route_debugging_table = 'ops.routedebugging_bitbucket'  # the name of the route_debugging table (hasn't been made yet)
current_android_data = {}  # the dictionary that stores the data in the Android table
current_iOS_data = {}  # the dictionary that stores the data in the iOS table
current_route_debugging_data = {}  # the dictionary that stores the data in the Route Debuggin table 
new_android_data = {}  # the dicionary that stores the current data in the Android bitbucket repo
new_iOS_data = {}  # the dicionary that stores the current data in the iOS bitbucket repo
new_route_debugging_data = {}  # the dicionary that stores the current data in the Route Debugging bitbucket repo

print 'getting current data from database'
cnxn = DB_connect()  # first database connection
current_android_data = get_current_data(android_table, cnxn)  # getting android data from database
current_iOS_data = get_current_data(iOS_table, cnxn)  # getting ios data from database
current_route_debugging_data = get_current_data(route_debugging_table, cnxn)  # getting route debugging data from database
cnxn.close()

print current_iOS_data
print current_android_data

print 'getting new data from bitbucket'
new_iOS_data = get_new_data('calmagchiu', 'qa-qc-ios', api)  # getting iOS data from bitbucket
new_android_data = get_new_data('calmagchiu', 'qa-qc-android', api)  # getting android data from bitbucket
new_route_debugging_data = get_new_data('masalomon', 'route-debugging', api) # getting route debugging data from android

print new_android_data
print new_iOS_data

print 'updating database data'
cnxn = DB_connect()  # connecting to the database the second time
print 'android'
update_db(current_android_data, new_android_data, cnxn, android_table)  # updating data in the android table
print 'ios'
update_db(current_iOS_data, new_iOS_data, cnxn, iOS_table)  # updating data in iOS table
print 'route debugging'
update_db(current_route_debugging_data, new_route_debugging_data, cnxn, route_debugging_table)
cnxn.close()