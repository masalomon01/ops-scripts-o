import urllib2, json, gzip, StringIO, csv, time, MySQLdb, datetime, requests, threading, sys, multiprocessing
from threading import Thread
from Queue import Queue
from multiprocessing import Process
from datetime import datetime, timedelta
import calendar
from collections import defaultdict


def open_gzip(url):
	request = urllib2.Request(url)
	request.add_header('Accept-encoding', 'gzip')
	opener = urllib2.build_opener()
	f = opener.open(request)
	compresseddata = f.read()
	compressedstream = StringIO.StringIO(compresseddata)
	gzipper = gzip.GzipFile(fileobj=compressedstream)
	data = gzipper.read()
	list_trace = json.loads(data)
	return list_trace


def get_trace_data(mandel_data, city, date):
	print 'Getting all the TRACE Data youll need'
	td_ff = '/trace/trace_TT_8.json.gz'
	td_peak = '/trace/trace_TT_69.json.gz'
	non_td = '/FFTT.csv'
	url = 'http://mandel.metropia.com/cities/' + city + '/' + str(date)
	trace_ff_dict = dict(enumerate(open_gzip(url+td_ff)))
	trace_peak_dict = dict(enumerate(open_gzip(url+td_peak)))
	request = urllib2.urlopen(url+non_td)
	FFTT_trace = list(csv.reader(request))
	all_trace_dict = dict((int(x[0]), float(x[1])) for x in FFTT_trace[1:])
	trace_data = []
	iterdata = iter(mandel_data)
	next(iterdata)
	tdlinks = int(len(trace_peak_dict) - 1)

	for i in iterdata:
		if int(i[8]) > tdlinks:
			if int(i[8]) in all_trace_dict:
				fromlink_peak = all_trace_dict[int(i[8])] 
			else:
				fromlink_peak = 'x'
		elif int(i[8]) < tdlinks:
			if int(i[8]) in trace_peak_dict:
				fromlink_peak = trace_peak_dict[int(i[8])] 
			else:
				fromlink_peak = 'x'
		if int(i[9]) > tdlinks:
			if int(i[9]) in all_trace_dict:
				tolink_peak = all_trace_dict[int(i[9])] 
			else:
				tolink_peak = 'x'
		elif int(i[9]) < tdlinks:
			if int(i[9]) in trace_peak_dict:
				tolink_peak = trace_peak_dict[int(i[9])] 
			else:
				tolink_peak = 'x'
		if fromlink_peak == 'x' or tolink_peak == 'x':
			print 'no match', i[8], fromlink_peak, i[9], tolink_peak
			i.append('no_trace_value_found')
		else:
			trace_peak_value = fromlink_peak + tolink_peak
			i.append(trace_peak_value)

		if int(i[8]) > tdlinks:
			if int(i[8]) in all_trace_dict:
				fromlink_ff = all_trace_dict[int(i[8])] 
			else:
				fromlink_ff = 'x'
		elif int(i[8]) < tdlinks:
			if int(i[8]) in trace_ff_dict:
				fromlink_ff = trace_ff_dict[int(i[8])] 
			else:
				fromlink_ff = 'x'
		if int(i[9]) > tdlinks:
			if int(i[9]) in all_trace_dict:
				tolink_ff = all_trace_dict[int(i[9])] 
			else:
				tolink_ff = 'x'
		elif int(i[9]) < tdlinks:
			if int(i[9]) in trace_ff_dict:
				tolink_ff = trace_ff_dict[int(i[9])] 
			else:
				tolink_ff = 'x'
		if fromlink_ff == 'x' or tolink_ff == 'x':
			print 'no match', i[8], fromlink_ff, i[9], tolink_ff
			i.append('no_trace_value_found')
		else:
			trace_ff_value = fromlink_ff + tolink_ff
			i.append(trace_ff_value)

		trace_data.append(i)
	return trace_data


def get_mandel_delay(final_use_case_data, city, date):
	print 'Getting all the Mandel Data youll need'
	td_ff = '/mandel/maneuver_delay5_8.json.gz'
	td_peak = '/mandel/maneuver_delay5_69.json.gz'
	non_td = '/maneuver_delay_999.json'
	url = 'http://mandel.metropia.com/cities/' + city + '/' + str(date)
	list_mandel_nontd = json.load(urllib2.urlopen(url+non_td))
	mandel_peak_dict = dict(enumerate(open_gzip(url+td_peak) + list_mandel_nontd))
	mandel_ff_dict = dict(enumerate(open_gzip(url+td_ff) + list_mandel_nontd))
	mandel_data = []
	iterdata = iter(final_use_case_data)
	next(iterdata)
	for i in iterdata:
		if int(i[7]) in mandel_peak_dict:
			peak = mandel_peak_dict[int(i[7])]*.01
			i.append(peak)
		else:
			i.append('no_value_found')
		if int(i[7]) in mandel_ff_dict:
			ff = mandel_ff_dict[int(i[7])]*.01
			i.append(ff)
		else:
			i.append('no_value_found')

		mandel_data.append(i)
	return mandel_data


def write_output_data(file_path, input_data):
	print 'writing the following ' + file_path
	with open(file_path, 'wb') as f:
		writer = csv.writer(f)
		for i in input_data:
			writer.writerow(i)


def get_input_data(file_path):
	print 'reading input data', file_path
	input_data = []
	with open(file_path, 'rb') as f:  # getting input data
		reader = csv.reader(f)
		input_data = list(reader)
	return input_data


def get_mandel_id_data():
	print 'Getting Mandel Turn Link Pairs'
	url = 'http://mandel.metropia.com/cities/qaqc/' + city + '/turn_link_pairs.csv'
	request = urllib2.urlopen(url)
	mandel_id_data = csv.reader(request)
	mandel_id_data = list(mandel_id_data)
	tagged_data = []
	iterdata = iter(mandel_id_data)
	next(iterdata)
	for i in iterdata:
		usecase_id = i[4]+'&'+i[5]+'&'+i[3]
		i.append(usecase_id)
		tagged_data.append(i)
	return tagged_data


def get_unique_usecases(usecase):
	print 'getting the ' + str(case_count) + ' samples per each of the 68 possible use cases'
	iterdata = iter(usecase)
	next(iterdata)  # to get past the headers
	allcases =[]
	count = 1
	for i in iterdata:
		case = get_30(i[0], i[7])
		for x in case:
			if len(x) != 0:
				y = [city, x[13], x[12], x[15], x[14], '17:15', '02:00', x[0], x[1], x[2], x[10], x[11]]	# city, startlat, startlon, endlat, endlon, rush time, ff time, mandel id, from link, to link, caseid, casename
				allcases.append(y)
		#print count
		count = count + 1
		#print case
	print 'Total use cases for this round are ' + str(len(allcases))
	return allcases


def get_30(usecaseid, use_case_name):
	usecases = []
	iterdata = iter(mandel_id_data)
	next(iterdata)
	count = 0
	for i in iterdata:
		if usecaseid == i[10]:
			i.append(use_case_name)
			while count < case_count: #this controls the number of samples per use case **
				x = get_points(i[1], i[2], i)
				usecases.append(x)
				count = count + 1
				break
		else:
			continue
	return usecases


def get_points(fromlink, tolink, case):
	iterdata = iter(wkt_data)
	next(iterdata)

	for i in iterdata:
		if fromlink == i[0]:
		   wkt = i[4]
		   stripped = wkt[12:-1]
		   points = stripped.split(",")
		   start = points[0]
		   startlon = start.split(" ")[0]
		   startlat = start.split(" ")[1]

		elif tolink == i[0]:
			wkt = i[4]
			stripped = wkt[12:-1]
			points = stripped.split(",")
			end = points[-1]
			endlon = end.split(" ")[1]
			endlat = end.split(" ")[2]
		
	case.append(startlon) # if you get an error for calling a variable before assigned you are probably using the wrong wkt file
	case.append(startlat) #to do try and catch the error
	case.append(endlon)
	case.append(endlat)

	return case

def get_apis(city):
	apis = []
	SB_Parade_austin = 'http://54.187.235.23:8102'
	SB_Parade_elpaso = 'http://54.187.235.23:8107'
	SB_Parade_tucson = 'http://54.187.235.23:8103'
	DEV_atx = 'http://54.218.80.167:8102/sp'
	DEV_ep = 'http://54.218.80.167:8107/sp'
	DEV_tuc = 'http://54.218.80.167:8103/sp'
	google_url = 'https://maps.googleapis.com/maps/api/distancematrix/json?'
	if city == 'austin':
		apis.append(SB_Parade_austin)
		apis.append(DEV_atx)
	elif city == 'elpaso':
		apis.append(SB_Parade_elpaso)
		apis.append(DEV_ep)
	elif city == 'tucson':
		apis.append(SB_Parade_tucson)
		apis.append(DEV_tuc)
	else:
		print 'Excuse me wtf city did you chose? you can only pick austin, tucson or elpaso'
	apis.append(google_url)
	return apis


def get_thread_data(input_data, server):
    thread_list = []
    count = 1
    iter_input_data = iter(input_data)
    next(iter_input_data)
    if "54.187.235.23" in server: 
        for i in iter_input_data:
        	sb_parameters_ff = '/getroutes/departtime=02:00 speed=0 course=208 occupancy=1 vehicle_type= etag=true toll=true hot=true hov=true '  # these parameters are for all parade urls
        	sb_parameters_peak = '/getroutes/departtime=17:15 speed=0 course=208 occupancy=1 vehicle_type= etag=true toll=true hot=true hov=true '  # these parameters are for all parade urls
        	api_paramaters = 'startlat=%s startlon=%s endlat=%s endlon=%s' % (i[1], i[2], i[3], i[4])  # these are the paramaters that have to change with each request
        	api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
        	SB_api_deb = sandbox_api_debugger+api_debugger_paramaters
        	SB = i + [server+sb_parameters_peak+api_paramaters, "SB", count, SB_api_deb, server+sb_parameters_ff+api_paramaters]
        	count = count + 1
        	thread_list.append(SB)
    elif "/sp" in server:
        for i in iter_input_data:
            payload_ff = { "start_lat": i[1], "start_lon": i[2], "end_lat": i[3], "end_lon": i[4], "departure_time": "02:00", "toll": "true" }
            payload_peak = { "start_lat": i[1], "start_lon": i[2], "end_lat": i[3], "end_lon": i[4], "departure_time": "17:15", "toll": "true" }
            api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
            DEV_api_deb = dev1_api_debugger+api_debugger_paramaters
            DEV = i + [server, "DEV", count, DEV_api_deb, payload_peak, payload_ff]
            count = count + 1
            thread_list.append(DEV)
    elif "maps.googleapis" in server:
    	for i in iter_input_data:
    		API_key = 'AIzaSyCtZ8znVQe6VR6gbNF3Rgo9sC35m99hRAg'  # API key, might store this in a file if the functionality of this script grows
    		if city == 'austin':
    			time = 6
    		else:
    			time = 5
    		dt = datetime.strptime(i[5], "%H:%M") + timedelta(hours=time)
    		dt_now = datetime.now()
    		dt = dt.replace(year=dt_now.year, month=dt_now.month, day=dt_now.day) + timedelta(days=1)
    		departure_time = calendar.timegm(dt.utctimetuple())
    		paramaters = 'origins=%s,%s&destinations=%s,%s&departure_time=%s&traffic_model=best_guess&key=%s' % (i[1], i[2], i[3], i[4], departure_time, API_key)  # these are al of the paramaters that we are to change
    		GOOG = i + [server+paramaters, "GOOG", count]
    		count = count + 1
    		thread_list.append(GOOG)
    else:
        print "Excuse me WTF is this input? get_thread_data ", server
        exit(1)

    return thread_list


def call_thread(data):
    for i in range(concurrent):
        t = Thread(target=go_to_work)
        t.daemon = True
        t.start()
    try:
        print "Let's GO to Work Main Threads Starting", len(data)
        for l in data:
                q.put(l)
        q.join()
    except KeyboardInterrupt:
        sys.exit(1)

def go_to_work():
	global l_responses
	while True:
		data = q.get()
		city = data[0]
		url = data[16]
		system = data[17]
		testcase = data[18]
		#if testcase == 12 and system == "DEV":
		#	print data
		if system == "SB":
			api_deb = data[19]
			url_peak = data[16]
			url_ff = data[20]
			response = get_response_SB(url_peak, url_ff, api_deb)
		elif system == "DEV":
			api_deb = data[19]
			payload_peak = data[20]
			payload_ff = data[21]
			response = get_response_DEV(url, payload_peak, payload_ff, api_deb)
		elif system == "GOOG":
			response = get_response_GOOG(url)
		else:
			"Excuse me WTF happened here not SB or DEV? ", data
		if (testcase%50) == 0:
			print testcase, system, city
		response = [item for sublist in response for item in sublist]
		#print [city, system, testcase] + response
		write_data = [testcase, system] + data[0:16] + response
		l_responses.append(write_data)
		#write_to_csv(write_data)
		q.task_done()


def get_response_GOOG(url):
	api_data = []
	try:
		response = requests.get(url, timeout=10)
		status = response.status_code
		data = response.json()
		if status != 200:
			print "Google 400"
			api_data.append(['400', '400', '400'])
		elif data['rows'][0]['elements'][0]['status'] == 'NOT_FOUND': 
			print 'Google returned nothing with the following url: %s. Will skip this and continue.' % (url)
			api_data.append(['NOT_FOUND', 'NOT_FOUND', 'NOT_FOUND'])
		else:
			api_data.append([round(data['rows'][0]['elements'][0]['distance']['value']*0.000621371, 2), round(data['rows'][0]['elements'][0]['duration_in_traffic']['value'], 0), round(data['rows'][0]['elements'][0]['duration']['value'], 0)])  # appending distance and duration and convering to minutes and miles
	except requests.exceptions.Timeout:
		api_data.append(['timeout', 'timeout', 'timeout'])
	except:
		api_data.append(['error', 'error', 'error'])
	return api_data


def get_response_DEV(url, payload_peak, payload_ff, api_deb):
	api_data = []
	try:
		headers = {'content-type': 'application/json'}
		response_peak = requests.post(url, data=json.dumps(payload_peak), headers=headers, timeout=60)
		response_ff = requests.post(url, data=json.dumps(payload_ff), headers=headers, timeout=60)
		data = json.loads(response_peak.content)
		data2 = json.loads(response_ff.content)
		if response_peak.status_code != 200 and response_ff.status_code != 200:  # if the error is something other than 400 or 200 will just exit because that is unexpected and shouldn't happen.
			status = str(response_peak.status_code)
			api_data.append([status, status, status, status, api_deb])
		elif not response_peak.json() and not response_ff.json():  # parade will not return anything if it can't find a route, so cannot give more information on why no route is found. Could be possible to when this hapens ping portal to see what the problem was.
			print 'Parade returned nothing with the following url: %s. Will skip this and continue.' % (payload)
			api_data.append(['NULL', 'NULL', 'NULL', 'NULL', api_deb])
		elif response_peak.status_code == 200 and len(data['data']['route']) >= 9 or response_ff.status_code == 200 and len(data2['data']['route']) >= 9:
			api_data.append(['not desired route', 'not desired route', 'not desired route', 'not desired route', api_deb])
		elif response_peak.status_code == 200 and response_ff.status_code == 200:
			api_data.append([data['data']['distance'], round(data['data']['estimated_travel_time']*60.0,0), data2['data']['distance'], round(data2['data']['estimated_travel_time']*60.0,0), api_deb])
		else:
			api_data.append(['cornercase', 'cornercase', 'cornercase', 'cornercase', api_deb])
	except requests.exceptions.Timeout:
		api_data.append(['timeout', 'timeout', 'timeout', 'timeout', api_deb])
	except ValueError:
		print 'something funky with this case'
		api_data.append(['funky', 'funky', 'funky', 'funky', api_deb])
	except:
		api_data.append(['error', 'error', 'error', 'error', api_deb])

	return api_data


def get_response_SB(url_peak, url_ff, api_deb):
	api_data = []
	try:
		response_peak = requests.get(url_peak, timeout=60)
		response_ff = requests.get(url_ff, timeout=60)
		data = response_peak.json()
		data2 = response_ff.json()
		if response_peak.status_code != 200 and response_ff.status_code != 200:
			status = str(response_peak.status_code)
			api_data.append([status, status, status, status, api_deb])
		elif not response_peak.json() and not response_ff.json():
			print 'Parade returned nothing with the following url: %s. Will skip this and continue.' % (url_peak)
			api_data.append(['NULL', 'NULL', 'NULL', 'NULL', api_deb])
		elif response_peak.status_code == 200 and len(data[0]['ROUTE']) >= 9 or response_ff.status_code == 200 and len(data2[0]['ROUTE']) >= 9:
			api_data.append(['not desired route', 'not desired route', 'not desired route', 'not desired route', api_deb])
		elif response_peak.status_code == 200 and response_ff.status_code == 200:
			api_data.append([data[0]['DISTANCE'], round(data[0]['ESTIMATED_TRAVEL_TIME']*60.0,0), data2[0]['DISTANCE'], round(data2[0]['ESTIMATED_TRAVEL_TIME']*60.0,0), api_deb])  # appending distance, estimated travel time, benchmark travel time
		else:
			api_data.append(['cornercase', 'cornercase', 'cornercase', 'cornercase', api_deb])
	except requests.exceptions.Timeout:
		api_data.append(['timeout', 'timeout', 'timeout', 'timeout', api_deb])
	#except:
	#	api_data.append(['error', 'error', 'error', 'error', api_deb])

	return api_data


def write_to_csv(write_data): 
    lock = threading.Lock()
    lock.acquire() # thread blocks at this line until it can obtain lock
    with open('OUTPUT_EXCEPTION.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(write_data)
    lock.release()


def combine_lists(l_responses):
	print 'COMBINING YOUR LISTS MASTER'
	dev_list = [x for x in l_responses if 'DEV' == x[1]]
	goog_list = [x for x in l_responses if 'GOOG' == x[1]]
	sb_list = [x for x in l_responses if 'SB' == x[1]]
	d_dev = {d[0]: d[2:] for d in dev_list}
	d_goog = {d[0]: d[18:] for d in goog_list}
	d_sb = {d[0]: d[18:] for d in sb_list}
	dd = defaultdict(list)
	for d in (d_dev, d_sb, d_goog): # you can list as many input dicts as you want here
	    for key, value in d.iteritems():
	        dd[key].append(value)
	combined_list = []
	for key, value in dd.iteritems():
		sub_list = [item for sublist in value for item in sublist]
		combined_list.append(sub_list)
	title_list = ['City', 'StartLat', 'StartLon', 'EndLat', 'EndLon', 'RushHour', 'FF_Hour', 'MandelID', 'From_Link', 'To_Link', 'Usecase_ID', 'Usecase_Name', 'mandel_peak_value', 'mandel_ff_value', 'trace_peak_value', 'trace_ff_value', 'parade15_peak_distance', 'parade15_peak_estimated', 'parade15_ff_distance', 'parade15_ff_estimated', 'dev1_api_debugger', 'sandbox_peak_distance', 'sandbox_peak_estimated', 'sandbox_ff_distance', 'sandbox_ff_estimate', 'sandbox_api_debugger', 'google_distance', 'google_traffic', 'google_ffs']
	combined_list.insert( 0, title_list)

	return combined_list	


def write_to_db(combined_data):
    # ********Connect and write to DB
    db = MySQLdb.connect(host="192.168.1.95", user="mario", passwd="mario1234", db="ops", port=3300)   
    cur = db.cursor()
    sql = """INSERT INTO mandel_bb (City, StartLatitude, StartLongitude, EndLatitude, EndLongitude, RushHour, FF_hour, Mandel_ID, From_Link, To_Link, Usecase_ID, Usecase_name, mandel_peak_value, mandel_ff_value, trace_peak_value, trace_ff_value, ParadeNew_Peak_Distance, ParadeNew_Peak_Estimate, ParadeNew_FF_Distance, ParadeNew_FF_Estimate, paradenew_APIdebugger, ParadeOld_Peak_Distance, ParadeOld_Peak_Estimate, ParadeOld_FF_Distance, ParadeOld_FF_Estimate, Parade_Old_APIdebugger, Google_Distance, Google_Traffic, Google_FFS, testdate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
    iter_data = iter(combined_data) 
    next(iter_data)
    print 'Inserting OUTPUT Data into DB Now'
    date = time.strftime('%Y%m%d')
    for row in iter_data:
    	row.append(date)
        if len(row) == 30: 
            cur.execute(sql, row)
    db.commit()
    db.close
    print "Done and Done"

# TODOS update outputfilename, update wkt file

#**********Input Variables
date = time.strftime('%Y%m%d') 
#city = 'tucson' #only elpaso, tucson, austin allowed for now
#case_count = 2 #This controls the number of cases per avaliable mandel usecase
#concurrent = 100 #number of concurrent api calls to each api
try:
	city = sys.argv[1]
	case_count = sys.argv[2]
	concurrent = sys.argv[3]
except ValueError:
	print('Invalid input. Please enter somthing like: tucson 10 50')
case_count = int(case_count)
concurrent = int(concurrent)
#***********************************
# Input DATA for creating route query file
use_cases_file = 'Mandel_Use_Cases.csv'
#mandel_id_file = 'turn_link_pairs_' + city + '.csv'
wkt_file = 'links_wkt_' + city + '.csv'
mandel_input_file_name = 'Mandel_BB_Input_' + city + '.csv'
# Get ALL Data needed for and before querying routes
use_case_data = get_input_data(use_cases_file)  # getting the input data from the input csv file. contains startlon, startlat, endlon, endlat and departure time
wkt_data = get_input_data(wkt_file)
mandel_id_data = get_mandel_id_data()
final_use_case_data = [['City', 'StartLat', 'StartLon', 'EndLat', 'EndLon', 'RushHour', 'FF_Hour', 'MandelID', 'From_Link', 'To_Link', 'Usecase_ID', 'Usecase_Name']] + get_unique_usecases(use_case_data)
mandel_data = [['City', 'StartLat', 'StartLon', 'EndLat', 'EndLon', 'RushHour', 'FF_Hour', 'MandelID', 'From_Link', 'To_Link', 'Usecase_ID', 'Usecase_Name', 'mandel_peak_value', 'mandel_ff_value']] + get_mandel_delay(final_use_case_data, city, date)
trace_data = [['City', 'StartLat', 'StartLon', 'EndLat', 'EndLon', 'RushHour', 'FF_Hour', 'MandelID', 'From_Link', 'To_Link', 'Usecase_ID', 'Usecase_Name', 'mandel_peak_value', 'mandel_ff_value', 'trace_peak_value', 'trace_ff_value']] + get_trace_data(final_use_case_data, city, date)
#write_output_data(mandel_input_file_name, trace_data)  # writing all of the data to the output csv file

#the below commented piece was used to test individual responses for when multithreading 
'''
print "CREATE OUTPUT FILE"
results = ['City', 'System', 'Testcase', 'Status', 'APIdebugger', 'TestDate']
with open('OUTPUT_EXCEPTION.csv', 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(results)
'''
#************* ROUTE QUERY INPUT PARAMETERS
route_query_input = trace_data 
output_file_name = 'Mandel_Testing_Results_' + city + '.csv'
#************* API PARAMETERS
apis = get_apis(city) #SB, DEV, Google
#************* APIDEBUGGER PARAMETERS
sandbox_api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
dev1_api_debugger = 'http://developer.metropia.com/dev1_v1/static/debug_dev.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
#************CONCURRENT PARAMETERS FOR EACH SERVERS THREAD
q = Queue(concurrent * 2)
l_responses = []
threads = [] #list to count and wait for the threads
# *****Load Input Data
print "GET INPUT DATA READY FOR THREATHING"
SB_list = get_thread_data(route_query_input, apis[0])
DEV_list = get_thread_data(route_query_input, apis[1])
GOOG_list = get_thread_data(route_query_input, apis[2])
# Create new threads
sb_thread = Thread(target=call_thread, args=([SB_list]))
dev_thread = Thread(target=call_thread, args=([DEV_list]))
goog_thread = Thread(target=call_thread, args=([GOOG_list]))
# Start new Threads
sb_data = sb_thread.start()
dev_data = dev_thread.start()
goog_data = goog_thread.start()
# Add threads to thread list
threads.append(sb_thread)
threads.append(dev_thread)
threads.append(goog_thread)
for t in threads:
    t.join()
print "Exiting Main Thread"
# ********* Combine Lists and write Data to a csv file
combined_data = combine_lists(l_responses)
#write_output_data(output_file_name , combined_data) #write responses in csv as a backup
# ******* Load results on Maria DB
write_to_db(combined_data)