
import pyodbc
import mandrill

def pullingdata():
	# **** Connect to the DB and get necessary data *****
	cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.95;DATABASE=DataMint;UID=mario;PWD=mario1234')
	cursor = cnxn.cursor()
	# email, first name, min saved, co2 saved, distance, points, market
	cursor.execute("select eMail, First_Name, round(sum(TimeSavedinSecond/60), 0) as 'minsaved', round(sum(CO2Saving), 0) as 'co2saved', round(sum(routedistance), 0) as 'distance', sum(userEarnedCredit) as 'points' , TripMetroCity FROM [DataMint].[dbo].[rptTripSummary] WHERE LocalStartTime >= DATEADD(month, datediff(month, 0, getdate())-1, 0) AND LocalStartTime <  DATEADD(DAY, DATEDIFF(day, 0, getdate()), 0) AND abs(actualMin5 - EstimateTravelTime)/NULLIF(EstimateTravelTime,0) > .5 AND metropianid = 335 or metropianid = 1147 GROUP BY eMail, First_Name, TripMetroCity")
	rows = cursor.fetchall()
	userdata = []
	for row in rows:
		lista = [str(row[0]), row[1].encode('utf-8'), row[2], int(row[3]), int(row[4]), row[5], str(row[6])]
		userdata.append(lista)


	# trip city, city hours saved, city co2 saved, city trees planted
	cursor.execute("select TripMetroCity, round(sum(TimeSavedinSecond)/3600, 0) as 'hourssaved', round(sum(CO2Saving), 0) as 'co2saved', round(sum(CO2Saving)/100, 0) as 'treesplanted' FROM [DataMint].[dbo].[rptTripSummary] WHERE LocalStartTime >= DATEADD(month, datediff(month, 0, getdate())-1, 0) AND LocalStartTime <  DATEADD(DAY, DATEDIFF(day, 0, getdate()), 0) GROUP BY TripMetroCity")
	rows = cursor.fetchall()
	citydata = []
	for row in rows:
		listb = [str(row[0]), row[1], int(row[2]), int(row[3])]
		citydata.append(listb)

	citydata.pop(0)

	alldata = []
	for row in userdata:
		city = row[6]
		for x in citydata:
			if city == x[0]:
				totdata = [row[0], row[1], row[2], row[3], row[4], row[5], row[6], x[1], x[2], x[3]]
				alldata.append(totdata)

	dictall = []
	for row in alldata:
		data={}
		data['email'] = row[0]
		data['first_name'] = row[1]
		data['min_saved'] = row[2]
		data['co2saved'] = row[3]
		data['distance'] = row[4]
		data['points'] = row[5]
		data['tripcity'] = row[6]
		data['city_hours'] = row[7]
		data['city_co2'] = row[8]
		data['city_trees'] = row[9]
		dictall.append(data)
		print data

	return dictall


#pullingdata()
def mandrill_send():
	rows=pullingdata()
	for row in rows:
		mandrill_client = mandrill.Mandrill('7Nia_5qzBNOY_keuEb7O5g')
		template_content = [{'content': 'example content', 'name': 'POINTS'}]
		message = {'global_merge_vars': [{'content': row.get('points'), 'name': 'POINTS'}, {'content': row.get('min_saved'), 'name': 'TIMESAVED'}, {'content': row.get('co2saved'), 'name': 'COSAVED'}, {'content': row.get('distance'), 'name': 'DISTANCE'}, {'content': row.get('tripcity'), 'name': 'CITY'}, {'content': row.get('city_hours'), 'name': 'CITYHOURS'}, {'content': row.get('city_co2'), 'name': 'CITYCO'}, {'content': row.get('city_trees'), 'name': 'CITYTREES'}], 
		'tags': ['new-weekly-stats-austin-may'], 
		'to': [{'email': row.get('email'),'name': row.get('first_name'),'type': 'to'}]}
		result = mandrill_client.messages.send_template(template_name='new-weekly-stats-austin-may', template_content=template_content, message=message, async=False, ip_pool='Main Pool')

mandrill_send()
