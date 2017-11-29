# This programs job is to grab data from Metropian table in Metropia database as well as 
# Facebook data from Facebook Graph API. Then, we utilize both sets of data to find attributes
# about Metropians that aren't already in the Metropian table. The most useful of this data is friends
# So this script will connect to a Neo4j database and using Neo4j driver module create a social
# graph of Metropian users and their friendships with other metropians.
# This script is made to first traverse the social network and take note of what data we already have.
# Therefore, it isn't adding redundant data just the data we already have

import requests
import json
import pyodbc
import csv
import sys
from datetime import datetime
try:
	from neo4j.v1 import GraphDatabase, basic_auth
except ImportError:
	print "Neo4j driver not found. Please run: pip install neo4j-driver"
	sys.exit(1)


class User:
	'''
	This class will contain data on all Metropia users that have used Facebook to create their accounts. Contains
	data regarding their facebook account, metropia account, as well as a couple other data members that are useful
	in analyzing a particular user through their social media.
	
	NOTE: While it looks more like a struct than a class, future plan is to move more functionality into this
	class in order to minimize the number of 
	'''
	def __init__(self, FacebookID, name='unknown',  token = None, MetropianID = 0, updated_time = None):  # Metropian ID defaults to 
		'''
		Inits User with FacebookID, name, token, and MetropianID. The only one that
		is one-hundred-percent necessary is FacebookID because that is how we get
		that user's data on Facebook.
		'''
		self.MetropianID = MetropianID
		self.FacebookID = FacebookID
		self.name = name
		self.token = token
		self.is_token_valid = False
		self.email = 'unknown'
		self.friends = []
		self.max_age = 0
		self.min_age = 0
		self.updated_time = updated_time

	def __str__(self):
		'''
		__str__ to print an instance of the User class. Will print out all data members of the instance.
		Only used for debugging purposes.
		'''
		print_str = 'MetropianID = {}\n'.format(self.MetropianID)
		print_str += 'FaceBookID = {}\n'.format(self.FacebookID)
		print_str += 'name = {}\n'.format(self.name)
		print_str += 'token = {}\n'.format(self.token)
		print_str += 'is_token_valid = {}\n'.format(self.is_token_valid)
		print_str += 'min_age = {}\n'.format(self.min_age)
		print_str += 'max_age = {}\n'.format(self.max_age)
		print_str += 'email = {}\n'.format(self.email)
		print_str += 'friends = {}\n'.format(self.friends)
		print_str += 'updated_time = {}\n'.format(self.updated_time)
		return print_str

class Relationship:
	'''
	This class will contain the relationship between two Facebook users. Right now that only relationship
	is friendship, but using this design we can define different relationships if need be.

	NOTE: While it looks more like a struct than a class, future plan is to move more functionality into this
	class in order to minimize the number of 
	'''
	def __init__(self, FacebookID1, FacebookID2):
		'''
		Inits Relationship with two FacebookID.
		'''
		self.FacebookID1 = FacebookID1
		self.FacebookID2 = FacebookID2

	def __str__(self):
		'''
		Only for debugging purposes.
		'''
		ret_str = "FacebookID1 = {}\n".format(self.FacebookID1)
		ret_str += "FacebookID2 = {}\n".format(self.FacebookID2)
		return ret_str


def Metropia_DB_connect():
	'''
	Will return a connection to the Metropia.dbo.Complete database on 192.168.1.95.
	'''
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.95;DATABASE=Complete;UID=mario;PWD=mario1234;')
	return cnxn

def Graph_DB_connect():
	'''
	Will return a connection to the Neo4j graph database running locally on Eddie's machine. Will
	transfer graph db to 95 eventually and will have to change this to access that server.
	'''
	driver = GraphDatabase.driver("bolt://192.168.1.95:7687", auth=basic_auth("neo4j", "SantaLucia123"))
	return driver

def get_metropian_db_data():
	'''
	Will connect to the database, select the MetropianID, FacebookID, and Facebook token for every account
	that was created through facebook. It will then call the method fill_metropian_data and return
	what that method returns.
	'''
	sql_statement = 'SELECT ID, LoginSourceID, LoginToken FROM metropian WHERE LogInTypeID = 2'
	connection = Metropia_DB_connect()
	cursor = connection.cursor()
	cursor.execute(sql_statement)
	ret_data = cursor.fetchall()
	cursor.close()
	connection.close()
	return fill_metropian_data(ret_data)


def fill_metropian_data(ret_data):
	'''
	Takes tuple data in ret_data, creates User instances using that data, populates ret_users array
	and then returns ret_users

	Args:
		ret_data: Tuple in array data containing data from Metropian table.
	Returns:
		An array of User objects with the same data that was passed in. 
	'''
	ret_users = []
	for i in ret_data:
		temp_user = User(MetropianID = i[0], FacebookID = i[1], token = i[2])
		ret_users.append(temp_user)
		
	return ret_users

def get_facebook_data(users):
	'''
	This function connects to the Facebook Graph API (using batch calls for performance), gets Facebook data regarding
	Metropia users and puts that data into the already created User objects in the user array.
	
	Args:
		users: array of User objects with no Facebook data
	Returns:
		Returns all of the edges that are going to be in the graph, which is an array of Relationship objects
	'''
	# initializing variables. My token is necessary for the batch call
	# but in every individual request the users' token will be used.
	token = 'EAAC3wQ22MwoBAEbXRcD4YWJwtQlR5gr4ssGVpzbdRRSfvGAazKr2iM4iVkeyBl0aFHryRuGHZBeDoZAR8Mm1DYNnC3lBGJIhpvIc8tvgOQVXGctQI6ohaZBhC0Y1jD0ZCSiR0qdnniwPWzCEbI2qqgcmfoYs9SJDTGR9VSyByclZCdigI8644'
	url = "https://graph.facebook.com"
	batch_list = []
	count = 0
	edges = []

	for i in users:  # appending every request (one for every user) that is going to be made to batch_list
		temp_dict = {
			'method': 'GET',
			'relative_url': 'me?fields=name,friends,email,age_range,updated_time&access_token=%s&include_headers=false' % i.token
		}
		batch_list.append(temp_dict)

	# A batch of requests has a maximum size of 50. Therefore, we will have to iterate through the
	# length of all the users divided by 50 because we can get 50 users
	# with one batched request. Then have to add one to the remainder of the users.
	for i in range(0, len(users)/50 + 1): 

		data_for_post = {  # the data in the body of the Post batch request
			'access_token' : token,  # my token for the request
			'batch': str(batch_list[i*50:(i+1)*50]),  # the next 50 requests
		}

		r = requests.post(url, data=data_for_post)
		for j, item in enumerate(r.json()):
			# will only add data if the status code of the particular request is 200
			# and if the element we are trying to access is inside the length of users.
			if item['code'] == 200 and ((50 * i + j) < len(users)):
				
				json_data = json.loads(item['body'])  # response data gets returned in JSON format in "body" field
				users[50 * i + j].is_token_valid = True
				age_range = json_data.get('age_range')  # age_range gives a JSON formated result with min_age and max_age
				users[50 * i + j].min_age = age_range.get('min', 0)
				users[50 * i + j].max_age = age_range.get('max', 0)
				users[50 * i + j].name = json_data.get('name')
				users[50 * i + j].email = json_data.get('email')
				temp_friends = extract_friends(json_data.get('friends', False))  # friends gives a json formatted result of all the friends
				users[50 * i + j].friends = temp_friends
				users[50 * i + j].updated_time = datetime.strptime(json_data.get('updated_time'), "%Y-%m-%dT%H:%M:%S+0000")  # getting last date the account was updated
				for k in temp_friends:  # iterating through all of a users friends
					temp_relationship = Relationship(users[50 * i + j].FacebookID, k)  # creating a new Relationship between the current user and their friend
					edges.append(temp_relationship)
			print 'on person {}'.format(50 * i + j)
		print 'on batch {}'.format(i)

	return edges
	

def extract_friends(friends):
	'''
	This function is given the JSON formated data in the "friends" response of the Graph API. It then extracts the friend
	data and returns an array of FacebookIDs which represents all of the friends that a particular user has
	
	Args:
		friends: JSON formated data of all the friends a user has
	Returns:
		An array of FacebookIDs representing all of a users friends
	'''
	if not friends or not friends['data']:  # if a user has no friends :(
		return []

	ret_data = []

	for i in friends['data']:
		ret_data.append(i['id'])

	return ret_data

def write_to_graph_db(metropia_users_with_friends, non_metropia_facebook_users, relationships, metropia_users_with_friends_in_db, non_metropia_facebook_users_in_db, relationships_in_db):
	'''
	This function writes all of the data to the graph database. It is given Metropia users with friends, non metropia users, as well as relatioships.
	It first will create all of the nodes, and then go through the relationships and create one edge per relationships connecting
	the corresponding nodes.
	
	Args:
		metropia_users_with_friends: Array of User objects which are Metropia users who have facebook accounts that also have friends.
		non_metropia_facebook_users: set of FacebookIDs of Facebook users that Metropians are friends with but don't have Metropia Facebook accounts
		relationships: Array of Relatiosnhips objects representing edges.
	Returns:
		None
	'''
	driver = Graph_DB_connect()
	session = driver.session()

	for i in metropia_users_with_friends:
		match = False
		for j in metropia_users_with_friends_in_db:
			if i.FacebookID == j.FacebookID and i.updated_time == j.updated_time:
				match = True
				print 'chilling'
			elif i.FacebookID == j.FacebookID and i.updated_time > j.updated_time:
				match = True
				cypher_str = "MATCH (n { FacebookID:'%s' }) SET (n:User {is_metropian:'True', MetropianID:'%s', Name:'%s', Token:'%s', is_token_valid:'%s', min_age:'%s', max_age:'%s', email:'%s', updated_time:'%s'})" % (str(i.FacebookID), str(i.MetropianID), i.name.encode('utf-8'), str(i.token), i.is_token_valid, str(i.min_age), str(i.max_age), str(i.email), i.updated_time)
				print cypher_str
				session.run(cypher_str)
		if not match:
			print 'need to create a new node'
			cypher_str = "CREATE (n:User {FacebookID:'%s', is_metropian:'True', MetropianID:'%s', Name:'%s', Token:'%s', is_token_valid:'%s', min_age:'%s', max_age:'%s', email:'%s', updated_time:'%s'})" % (str(i.FacebookID), str(i.MetropianID), i.name.encode('utf-8'), str(i.token), i.is_token_valid, str(i.min_age), str(i.max_age), str(i.email), i.updated_time)
			print cypher_str
			session.run(cypher_str)

	for i in non_metropia_facebook_users:
		match = False
		for j in non_metropia_facebook_users_in_db:
			if i == j.FacebookID:
				match = True
				token = 'EAAC3wQ22MwoBAEbXRcD4YWJwtQlR5gr4ssGVpzbdRRSfvGAazKr2iM4iVkeyBl0aFHryRuGHZBeDoZAR8Mm1DYNnC3lBGJIhpvIc8tvgOQVXGctQI6ohaZBhC0Y1jD0ZCSiR0qdnniwPWzCEbI2qqgcmfoYs9SJDTGR9VSyByclZCdigI8644'
				url = "https://graph.facebook.com/{}?access_token={}".format(i, token)  # using my token to access the users name through Graph API
				r = requests.get(url)
				updated_time = datetime.strptime(r.json()['updated_time'], "%Y-%m-%dT%H:%M:%S+0000")
				name = str(r.json()['first_name'] + ' ' + r.json()['last_name'])
				if updated_time > j.updated_time:
					cypher_str = "MATCH (n {FacebookID:'%s'}) SET (n:User {is_metropian:'False', Name:'%s', updated_time:'%s'})" % (str(i), name, updated_time)
					print cypher_str
					session.run(cypher_str)

		if not match:
			token = 'EAAC3wQ22MwoBAEbXRcD4YWJwtQlR5gr4ssGVpzbdRRSfvGAazKr2iM4iVkeyBl0aFHryRuGHZBeDoZAR8Mm1DYNnC3lBGJIhpvIc8tvgOQVXGctQI6ohaZBhC0Y1jD0ZCSiR0qdnniwPWzCEbI2qqgcmfoYs9SJDTGR9VSyByclZCdigI8644'
			url = "https://graph.facebook.com/{}?access_token={}".format(i, token)  # using my token to access the users name through Graph API
			r = requests.get(url)
			updated_time = datetime.strptime(r.json()['updated_time'], "%Y-%m-%dT%H:%M:%S+0000")
			name = str(r.json()['first_name'] + ' ' + r.json()['last_name'])
			cypher_str = "CREATE (n:User {FacebookID:'%s', is_metropian:'False', Name:'%s', updated_time:'%s'})" % (str(i), name, updated_time)
			print cypher_str
			session.run(cypher_str)

	for i in relationships:
		match = False
		for j in relationships_in_db:
			if i.FacebookID1 == j.FacebookID1 and i.FacebookID2 == j.FacebookID2:
				match = True
				break
		if not match:
			print 'need to create a new relationship'
			cypher_str = "MATCH (a:User { FacebookID: '%s' }), (b:User { FacebookID: '%s' })" % (i.FacebookID1, i.FacebookID2)
			cypher_str += " CREATE (a)-[:FRIENDS]->(b)"
			print cypher_str
			session.run(cypher_str)
	session.close()

def write_to_csv(users, relationships, headers):
	'''
	This function writes all of the data to a csv file. This is mostly for quick access to what data we are getting. Will take
	it out unless find a better use for it.
	
	Args:
		users: Array of User object containing all the users we want to put in the csv
		relationships: Array of Relationship objects containing all of the friendships we want in the csv
		headers: Headers for the csv
	Returns:
		None
	'''
	with open('test.csv', 'wb') as csvfile:
		writer = csv.writer(csvfile, delimiter=',')
		writer.writerow(headers)
		for i in users:
			row = [
				i.MetropianID, i.FacebookID, i.name.encode('utf-8'), i.token,
				i.is_token_valid, i.min_age, i.max_age, i.email
			]	
			writer.writerow(row)
		writer.writerow(['FacebookID1', 'FacebookID2'])
		for i in relationships:
			row = [i.FacebookID1, i.FacebookID2]
			writer.writerow(row)

def get_non_metropia_facebook_users(metropia_users_with_friends, relationships):
	'''
	This function will go through every relationship, and find Facebook accounts that are referenced in a Relationship
	object, that are not in the metropia_users_with_friends array. When this happens. It means that that particular
	Facebook account is not a Metropia account, they are just a friend of a Metropian. Therefore we will still
	put them in the graph database, but we will just have less information about them. These are the users that 
	we are going to want to target in marketing.
	
	Args:
		relationship: an array of all Relationship objects
		metropia_users_with_friends: an array of all Metropia User objects with friends
	Returns:
		a set of the Facebook accounts that are not Metorpians
	'''
	extra = []
	for i in relationships:
		match = False
		for j in metropia_users_with_friends:
			if i.FacebookID2 == j.FacebookID:
				match = True
				break
		if match == False:
			extra.append(i.FacebookID2)

	return set(extra)  # returning a set in order to get rid of duplicates


def get_graph_data():
	driver = Graph_DB_connect()
	session = driver.session()
	node_cypher_str = 'MATCH (n:User) Return n'
	edge_cypher_str = 'MATCH (n1:User)-[thang:FRIENDS]->(n2:User) RETURN n1.FacebookID, n2.FacebookID'
	node_result = session.run(node_cypher_str)
	edge_result = session.run(edge_cypher_str)
	session.close()
	metropia_users_with_friends = []
	non_metropia_facebook_users = []
	relationships = []

	for record in node_result:
		if record["n"]["is_metropian"] == 'True':
			temp_user = User(FacebookID=record['n']['FacebookID'], name=record['n']['name'], token=record['n']['token'], MetropianID = record['n']['MetropianID'], updated_time = datetime.strptime(record['n']['updated_time'], "%Y-%m-%d %H:%M:%S"))
			metropia_users_with_friends.append(temp_user)
		else:
			temp_user = User(FacebookID=record['n']['FacebookID'], name=record['n']['name'], updated_time = datetime.strptime(record['n']['updated_time'], "%Y-%m-%d %H:%M:%S"))
			non_metropia_facebook_users.append(temp_user)
	for record in edge_result:
		temp_relationship = Relationship(FacebookID1 = record['n1.FacebookID'], FacebookID2 = record['n2.FacebookID'])
		relationships.append(temp_relationship)
	
	return metropia_users_with_friends, non_metropia_facebook_users, relationships

def main():
	users = []  # data we are grabbing from Metropia database and our database
	metropia_users_with_friends = []
	relationships = []
	non_metropia_facebook_users = []

	metropia_users_with_friends_in_db = []  # data we are grabbing from graph database
	relationships_in_db = []
	non_metropia_facebook_users_in_db = []
	headers = ['MetropianID', 'FaceBookID', 'name', 'token', 'valid token', 'min_age', 'max_age', 'email']
	print 'starting'
	print 'accessing graph db'
	metropia_users_with_friends_in_db, non_metropia_facebook_users_in_db, relationships_in_db = get_graph_data()
	print 'accessing old db'
	users = get_metropian_db_data()
	print 'getting facebook data'
	relationships = get_facebook_data(users)
	print 'extracting users with friends'
	metropia_users_with_friends = [ i for i in users if i.friends ]
	non_metropia_facebook_users = get_non_metropia_facebook_users(metropia_users_with_friends, relationships)
	#print 'writing to csv'
	#write_to_csv(metropia_users_with_friends, relationships, headers)
	print 'writing to database'
	write_to_graph_db(metropia_users_with_friends, non_metropia_facebook_users, relationships, metropia_users_with_friends_in_db, non_metropia_facebook_users_in_db, relationships_in_db)

if __name__ == '__main__':
	main()