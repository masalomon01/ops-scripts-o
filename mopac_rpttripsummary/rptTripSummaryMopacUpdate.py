#please make sure that the mopac file to be read here is up to date
import pypyodbc
import urllib2
import json
import csv
import itertools
import datetime
import time

with open('mopac links dec15.csv', 'rb') as csvfile: 
#with open('test.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	your_list = list(reader)
	mopac = set(itertools.chain(*your_list))
	map(int, mopac)
	mopac = [int(value) for value in mopac]

with open('mopac links dec15.csv', 'rb') as csvfile:
	reader = csv.reader(csvfile)
	your_list = list(reader)
	mopac2 = set(itertools.chain(*your_list))
	map(int, mopac2)
	mopac2 = [int(value) for value in mopac2]

connection = pypyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.95; DATABASE=DataMint; UID=mario;PWD=mario1234') # connecting to the office machine via ODBC
cursor = connection.cursor() # initializing cursor

opener = urllib2.build_opener()
# Old mopac boundary had 5993 trips out of possible 19132 dates 0811 to 1024  new boundary has 9531 trips
#query_network1 = "select First_Name, eMail, APIID, MetropianID from rptTripSummary where TripMetroCity='Austin' and mopactrip is NULL and convert(varchar(8),LocalReservationTime,112) >='20150902' and CONVERT(varchar(8), LocalReservationTime, 112) <='20151024'"
query_network1 = "select TripMetroCity, eMail, APIID, MetropianID, TripSummaryID from rptTripSummary where TripMetroCity='Austin' and convert(varchar(8),LocalReservationTime,112) >='20160301'"
cursor.execute(query_network1)
rows = cursor.fetchall()
tot_rows = len(rows)
print tot_rows
#print rows
def get_mopaccopde_timestamp_APIID ():
	count = 0
	for row in rows:
		APPID = row[2]
		TripSummaryID = row[4]
		MetropianID = str(row[3])
		count = count + 1
		#print APPID
		#print MetropianID
		mopac_trip_data = []
		#if '1trip' in APPID:
			#id1 = APPID[:3]
			#id2 = APPID[3:6]
			#trip = APPID[7:]
		if '2015' or '2016' in APPID:
			#print len(MetropianID)
			if len(MetropianID) == 4:	
				id1 = '00' + MetropianID[:1]
				id2 = MetropianID[-3:]
				trip = APPID
			elif len(MetropianID) == 3:
				id1 = '000'
				id2 = MetropianID[:3]
				trip = APPID
			elif len(MetropianID) == 2:
				id1 = '000'
				id2 = "0" + MetropianID[:2]
				trip = APPID
			else: #len(MetropianID) == 1
				id1 = '000'
				id2 = "00" + MetropianID[:1]
				trip = APPID

			#print id1, id2, trip 
			try:
				url = "http://lab.smartrek.webfactional.com/.reservation/" + id1 + "/" + id2 + "/1trip_" + trip
				trip_info = json.load(opener.open(url))
				actual_traj = trip_info.get('trajectory', [])
				parade_traj = trip_info.get('route')
				if len(actual_traj) > 75:
				
					actualroute = set(link[6] for link in actual_tr_aj if link != (-1)) 
					parade_route = set(link.get('link') for link in parade_traj[0:-1]) 
					linksid = set(link[6] for link in actual_traj)
					linksfollowed = str(float(len(actual_route & parade_route))/len(parade_route) * 100)
					if (linksid & set(mopac)):
						actualmopac = str(1)
					else:
						actualmopac = str(0)
					if (parade_route & set(mopac)):
						parademopac = str(1)
					else:
						parademopac = str(0)

					try:
						benchmarkroute = "http://production.smartrek.webfactional.com/v1/business/route"
						startlon = str(trip_info.get('startlon'))
						startlat = str(trip_info.get('startlat'))
						endlon = str(trip_info.get('endlon'))
						endlat = str(trip_info.get('endlat'))
						benchmarkroute = (benchmarkroute + ".json?startlat=" + startlat + "&startlon=" + startlon + "&endlat=" + endlat + "&endlon=" + endlon + "&departtime=2:00&speed=0&course=0")
						benchmark_info = json.load(urllib2.urlopen(benchmarkroute))
						benchmark_data = benchmark_info.get('data', [])
						benchmark_links = set([links['link'] for links in benchmark_data['route']])
						if (benchmark_links & set(mopac2)):
							benchmarkmopac = str(1)
						else:
							benchmarkmopac = str(0)
					except urllib2.HTTPError:
						print 'unknown error http error 552 on %s trip' % benchmarkroute
						continue
					except KeyError:
					 	print 'No route found in the API Debugger'
					except Exception, detail:
						print detail

					test = parademopac + actualmopac + benchmarkmopac
					now = datetime.datetime.utcnow()
					now = now.strftime("%Y-%m-%d %H:%M:%S")
					#APPID = str(APPID)
					write_to_db (APPID, test, now, parademopac, actualmopac, benchmarkmopac, TripSummaryID)
					#mopac_trip_data += [APPID, test, str(now)]

					print count, APPID, test, now, url, benchmarkroute
					#print linksfollowed, test, now
					#(APPID, test, now)
			except IndexError:
				print 'weird old route'
			except Exception, detail:
				print detail 
			except urllib2.HTTPError:
				print 'unknown error http error 552 on %s trip' % url
#get_mopaccopde_timestamp_APIID()

def write_to_db (APPID, test, now, parademopac, actualmopac, benchmarkmopac, TripSummaryID):
	#get_mopaccopde_timestamp_APIID(APPID, test, now)
	#print APPID, test, now
	# cursor.execute("insert into rptTripSummary (MoPacTrip) values (0) select APIID from rptTripSummary where APIID = ?", (APPID))
	# cnxn.commit()
	try:
		write_sql = "update rptTripSummary set mopactrip = '%s', mopackTripUpdate = '%s', mopacParade = '%s', mopacActual = '%s', mopacBenchmark = '%s' where APIID = '%s' and TripMetroCity='Austin' and TripSummaryID = '%s'" % (test, now, parademopac, actualmopac, benchmarkmopac, APPID, TripSummaryID)
		cursor.execute(write_sql)
		connection.commit()
	except Exception, detail:
           print detail



#write_to_db(APPID, test, now)

get_mopaccopde_timestamp_APIID()



