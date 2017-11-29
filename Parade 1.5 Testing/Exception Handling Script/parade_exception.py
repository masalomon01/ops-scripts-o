#This Script will ping parade 1.5 and sandbox parade to compare no returns and 400 errors ALL EXCEPTIONS
import urllib2, json, csv, requests, datetime, MySQLdb, time, threading, sys, multiprocessing
from threading import Thread
from Queue import Queue
from multiprocessing import Process

def get_input_data(input_file):
    input_data = []
    with open(input_file, 'rb') as f:  # getting input data
        reader = csv.reader(f)
        input_data = list(reader)
    return input_data

def get_thread_data(input_data, server):
    thread_list = []
    count = 1
    iter_input_data = iter(input_data)
    next(iter_input_data)
    if "/sp" not in server: 
        for i in iter_input_data:
            api_paramaters = 'startlat=%s startlon=%s endlat=%s endlon=%s' % (i[1], i[2], i[3], i[4])  # these are the paramaters that have to change with each request
            api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
            SB_api_deb = sandbox_api_debugger+api_debugger_paramaters
            SB = [i[0], server+api_paramaters, SB_api_deb, count, "SB"]
            count = count + 1
            thread_list.append(SB)
    elif "/sp" in server:
        for i in iter_input_data:
            payload = { "start_lat": i[1], "start_lon": i[2], "end_lat": i[3], "end_lon": i[4], "departure_time": "02:00", "toll": "true" }
            api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
            DEV_api_deb = dev1_api_debugger+api_debugger_paramaters
            DEV = [i[0], server, DEV_api_deb, count, "DEV", payload]
            count = count + 1
            thread_list.append(DEV)
    else:
        print "Excuse me WTF is this input? ", server
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
    global q
    while True:
        data = q.get()
        city = data[0]
        url = data[1]
        api_deb = data[2]
        testcase = data[3]
        system = data[4]
        if system == "SB":
            status = get_status_SB(url)
        elif system == "DEV":
            payload = data[5]
            status = get_status_DEV(url, payload)
        else:
            "Excuse me WTF happened here not SB or DEV? ", data
        if (testcase%100) == 0:
            print testcase, system, city
        if status != 200:
            write_data = [city, system, testcase, status, api_deb, datetime.date.today()]
            write_to_csv(write_data)
        q.task_done()

def get_status_DEV(url, payload):
    try:
        headers = {'content-type': 'application/json'}
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=10)
        status = response.status_code
        if response.status_code != 200:  # if the error is something other than 400 or 200 will just exit because that is unexpected and shouldn't happen.
            return status
        elif not response.json():  # parade will not return anything if it can't find a route, so cannot give more information on why no route is found. Could be possible to when this hapens ping portal to see what the problem was.
            return 'FAIL'
        else:
            return status
    except requests.exceptions.Timeout:
        return "timeout"
    except:
        return "error"

def get_status_SB(url):
    try:
        response = requests.get(url, timeout=10)
        status = response.status_code
        if status != 200:
            return status
        elif not response.json():
            return "FAIL"
        else:
            return status
    except requests.exceptions.Timeout:
        return "timeout"
    except:
        return "error"

def write_to_csv(write_data): 
    lock = threading.Lock()
    lock.acquire() # thread blocks at this line until it can obtain lock
    with open('OUTPUT_EXCEPTION.csv', 'ab') as f:
        writer = csv.writer(f)
        writer.writerow(write_data)
    lock.release()

def write_input_file(atx_count, ep_count, tuc_count):
    insert = [['austin', atx_count, datetime.date.today()], ['elpaso', ep_count, datetime.date.today()], ['tucson', tuc_count, datetime.date.today()]]
    db = MySQLdb.connect(host="192.168.1.95", user="mario", passwd="mario1234", db="ops")   
    cur = db.cursor()
    sql = """INSERT INTO parade_exception_input (City, Test_Count, Test_Date) VALUES (%s, %s, %s) """
    print 'Inserting INPUT Data Now'
    cur.executemany(sql, insert)
    db.commit()
    db.close

def write_to_db(output_file_name):
    # ********Connect and write to DB
    db = MySQLdb.connect(host="192.168.1.95", user="mario", passwd="mario1234", db="ops")   
    cur = db.cursor()
    sql = """INSERT INTO parade_exception (City, testcase, System, Status, APIDEBUGGER, TestDate) VALUES (%s, %s, %s, %s, %s, %s) """
    out_data = csv.reader(open(output_file_name, 'rb'))
    iter_out_data = iter(out_data)
    next(iter_out_data)
    print 'Inserting OUTPUT Data into DB Now'
    for row in iter_out_data:
        if len(row) == 6: 
            cur.execute(sql, row)
    db.commit()
    db.close
    print "Done and Done"

if __name__ == '__main__':
    #************* INPUT PARAMETERS
    input_atx_name = 'exception_austin.csv' #'sample_atx.csv' 
    input_ep_name = 'sample_ep.csv' #'sample_ep.csv' 
    input_tuc_name = 'sample_tuc.csv' #'sample_tuc.csv' 
    output_file_name = 'OUTPUT_EXCEPTION.csv'
    #************* SERVER PARAMETERS
    hardcoded_parade_parameters = '/getroutes/departtime=02:00 speed=0 course=208 occupancy=1 vehicle_type= etag=true toll=true hot=true hov=true '  # these parameters are for all parade urls
    SB_Parade_austin = 'http://54.187.235.23:8102' + hardcoded_parade_parameters
    SB_Parade_elpaso = 'http://54.187.235.23:8107' + hardcoded_parade_parameters
    SB_Parade_tucson = 'http://54.187.235.23:8103' + hardcoded_parade_parameters
    DEV_atx = 'http://54.218.80.167:8102/sp'
    DEV_ep = 'http://54.218.80.167:8107/sp'
    DEV_tuc = 'http://54.218.80.167:8103/sp'
    #************* APIDEBUGGER PARAMETERS
    sandbox_api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
    dev1_api_debugger = 'http://developer.metropia.com/dev1_v1/static/debug_dev.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
    # *****Load Input Data
    print "READING INPUT DATA"
    atx_input = get_input_data(input_atx_name)
    ep_input = get_input_data(input_ep_name)
    tuc_input = get_input_data(input_tuc_name)
    #*************Get Input Ready for THREADING
    print "GET INPUT DATA READY FOR THREATHING"
    ep_SB_list = get_thread_data(ep_input, SB_Parade_elpaso)
    ep_DEV_list = get_thread_data(ep_input, DEV_ep)
    tuc_SB_list = get_thread_data(tuc_input, SB_Parade_tucson)
    tuc_DEV_list = get_thread_data(tuc_input, DEV_tuc)
    #*************CREATE AND PREPARAE OUTPUT FILE
    print "CREATE OUTPUT FILE"
    results = ['City', 'System', 'Testcase', 'Status', 'APIdebugger', 'TestDate']
    with open(output_file_name, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(results)
    #************CONCURRENT PARAMETERS FOR EACH SERVERS THREAD
    concurrent = 200
    q = Queue(concurrent * 2)
    threads = [] #list to count and wait for the threads

    # Create new threads
    sb_ep_thread = Thread(target=call_thread, args=([ep_SB_list]))
    dev_ep_thread = Thread(target=call_thread, args=([ep_DEV_list]))
    sb_tuc_thread = Thread(target=call_thread, args=([tuc_SB_list]))
    dev_tuc_thread = Thread(target=call_thread, args=([tuc_DEV_list]))
    # Start new Threads
    sb_ep_data = sb_ep_thread.start()
    dev_ep_data = dev_ep_thread.start()
    sb_tuc_data = sb_tuc_thread.start()
    dev_tuc_data = dev_tuc_thread.start()
    # Add threads to thread list
    threads.append(sb_ep_thread)
    threads.append(dev_ep_thread)
    threads.append(sb_tuc_thread)
    threads.append(dev_tuc_thread)
    for t in threads:
        t.join()
    print "Exiting Main Thread"


#*************INSERT TEST INPUT DATA ON DB
write_input_file(len(atx_input), len(ep_input), len(tuc_input))
#*************INSERT RESULTS DATA ON DB
write_to_db(output_file_name)




'''
def write_output_data(file_path, input_data):
    print 'writing output data'
    with open(file_path, 'wb') as f:
        writer = csv.writer(f)
        for i in input_data:
            writer.writerow(i)

def write_to_db(api_data, city , system):
    # ********Connect and write to DB
    #print "writing to db", api_data
    db = MySQLdb.connect(host="192.168.1.95",    # your host, usually localhost
                         user="mario",         # your username
                         passwd="mario1234",  # your password
                         db="ops")   
    cur = db.cursor()
    sql = """INSERT INTO parade_exception (City, testcase, System, Status, APIDEBUGGER, TestDate) VALUES (%s, %s, %s, %s, %s, %s) """
    print 'Inserting Data Now', system, city
    cur.executemany(sql, api_data)
    db.commit()
    #for i in api_data:
    #    cur.execute(sql, i)
    #    db.commit
    db.close


def get_oldparade_data(oldparade_url, sandbox_api_debugger, input_data, city, api_data):
    print '********getting data from old parade sandbox for ' + city
    iterdata = iter(input_data)
    next(iterdata)  # to get past the headers
    count = 1  # this is equal to the row of the csv, just to keep track of where the code is
    iter_count = 1
    loop_time = time.time()
    #api_data = []  # a list that will contain all of the api data
    for i in iterdata:  # iterating through all the data without the headers
        url = oldparade_url 
        api_paramaters = 'startlat=%s startlon=%s endlat=%s endlon=%s' % (i[1], i[2], i[3], i[4])  # these are the paramaters that have to change with each request
        api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4])  # these are the parameters that have to be changed for the API debugger
        response = requests.get(url+api_paramaters)  # concatenating the parade url and port number with the parameters
        if response.status_code != 200:  # if the error is something other than 400 or 200 will just exit because that is unexpected and shouldn't happen.
            print('Status:', response.status_code)  # printing out useful debugging information
            print url+api_paramaters
            exit(1)
        elif not response.json():  # parade will not return anything if it can't find a route, so cannot give more information on why no route is found. Could be possible to when this hapens ping portal to see what the problem was.
            #print 'Parade returned nothing with the following url: %s. Will skip this and continue.' % (url+api_paramaters)
            api_data.append([i[0], str(count), 'SB_PARADE', 'FAIL', sandbox_api_debugger+api_debugger_paramaters, datetime.date.today()])
            #print str(count) + " SB " + city, 'FAIL'
            count = count + 1  # just to be consistent with count
        else:
            api_data.append([i[0], str(count), 'SB_PARADE', 'PASS', sandbox_api_debugger+api_debugger_paramaters, datetime.date.today()])  # appending distance, estimated travel time, benchmark travel time
            #print str(count) + " SB " + city # for logging purposes, count is the row of the csv file. Also printing out the url in case there is an error the person running the command can test it out in their browser
            count = count + 1
        #data = response.json()
        iter_count = iter_count + 1
        if iter_count == 100:
            print str(count) + " SB " + city + " API_time " + str(time.time() - loop_time)
            iter_count = 1
            write_to_db(api_data, city, "SB")
            api_data = []
            loop_time = time.time()
            continue
    #return api_data


def get_parade15_data(parade15_url, dev1_api_debugger, input_data, city, api_data, start_time):
    print '********getting parade15 data' + city 
    iterdata = iter(input_data)
    next(iterdata)  # to get past the headers
    count = 1  # this is equal to the row of the csv, just to keep track of where the code is
    iter_count = 1
    loop_time = time.time()

    #api_data = []  # a list that will contain all of the api data
    for i in iterdata:  # iterating through all the data without the headers
        payload = { "start_lat": i[1], "start_lon": i[2], "end_lat": i[3], "end_lon": i[4], "departure_time": '02:00', "toll": "true" }
        api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (i[1], i[2], i[3], i[4]) 
        headers = {'content-type': 'application/json'}
        response = requests.post(parade15_url, data=json.dumps(payload), headers=headers)
        if response.status_code != 200:  # if the error is something other than 400 or 200 will just exit because that is unexpected and shouldn't happen.
            status = 'STATUS ' + str(response.status_code)
            api_data.append([i[0], str(count), 'DEV_PARADE', status, dev1_api_debugger+api_debugger_paramaters, datetime.date.today()])
            #print str(count) + " DEV " + city, ('Status:', response.status_code)
            count = count + 1
            #continue
        elif not response.json():  # parade will not return anything if it can't find a route, so cannot give more information on why no route is found. Could be possible to when this hapens ping portal to see what the problem was.
            print 'Parade returned nothing with the following url: %s. Will skip this and continue.' % (payload)
            api_data.append([i[0], str(count), 'DEV_PARADE', 'FAIL', dev1_api_debugger+api_debugger_paramaters, datetime.date.today()])
            #print str(count) + " DEV " + city, 'FAIL'
            count = count + 1  # just to be consistent with count
            #continue
        else:
            api_data.append([i[0], str(count), 'DEV_PARADE', 'PASS', dev1_api_debugger+api_debugger_paramaters, datetime.date.today()])
            #print str(count) + " DEV " + city # for logging purposes, count is the row of the csv file. Also printing out the url in case there is an error the person running the command can test it out in their browser
            count = count + 1
            #continue
        #data = json.loads(response.content)
        iter_count = iter_count + 1
        if iter_count == 50:
            print str(count) + " DEV " + city + " API_time " + str(time.time() - loop_time)
            #print q.get()
            iter_count = 1
            with threading.Lock():
                write_to_db(api_data, city, "DEV")
            api_data = []
            continue
    #return api_data

start_time = time.time()
print start_time
#************* INPUT PARAMETERS
input_atx_name = 'exception_austin.csv' #'sample_atx.csv' 
input_ep_name = 'exception_elpaso.csv' #'sample_ep.csv' 
input_tuc_name = 'exception_tucson.csv' #'sample_tuc.csv' 
output_file_name = 'OUTPUT_EXCEPTION.csv'
#************* SERVER PARAMETERS
hardcoded_parade_parameters = '/getroutes/departtime=02:00 speed=0 course=208 occupancy=1 vehicle_type= etag=true toll=true hot=true hov=true '  # these parameters are for all parade urls
SB_Parade_austin = 'http://54.187.235.23:8102' + hardcoded_parade_parameters
SB_Parade_elpaso = 'http://54.187.235.23:8107' + hardcoded_parade_parameters
SB_Parade_tucson = 'http://54.187.235.23:8103' + hardcoded_parade_parameters
DEV_atx = 'http://54.218.80.167:8102/sp'
DEV_ep = 'http://54.218.80.167:8107/sp'
DEV_tuc = 'http://54.218.80.167:8103/sp'
#************* APIDEBUGGER PARAMETERS
sandbox_api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
dev1_api_debugger = 'http://developer.metropia.com/dev1_v1/static/debug_dev.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
# *****Load Input Data
input_atx_data = get_input_data(input_atx_name)[0]  # getting the input data from the input csv file. contains startlon, startlat, endlon, endlat and departure time
input_ep_data = get_input_data(input_ep_name)[0]  # getting the input data from the input csv file. contains startlon, startlat, endlon, endlat and departure time
input_tuc_data = get_input_data(input_tuc_name)[0]  # getting the input data from the input csv file. contains startlon, startlat, endlon, endlat and departure time
#************** MULTITHREADING BEGINS
threads = [] #list to count and wait for the threads
api_data = []  # a list that will contain all of the api data
# Create new threads
sb_atx_thread = Thread(target=get_oldparade_data, args=(SB_Parade_austin, sandbox_api_debugger, input_atx_data, 'atx', api_data))
sb_ep_thread = Thread(target=get_oldparade_data, args=(SB_Parade_elpaso, sandbox_api_debugger, input_ep_data, 'ep', api_data))
sb_tuc_thread = Thread(target=get_oldparade_data, args=(SB_Parade_tucson, sandbox_api_debugger, input_tuc_data, 'tuc', api_data))
dev_atx_thread = Thread(target=get_parade15_data, args=(DEV_atx, dev1_api_debugger, input_atx_data, 'atx', api_data, start_time))
dev_ep_thread = Thread(target=get_parade15_data, args=(DEV_ep, dev1_api_debugger, input_ep_data, 'ep', api_data, start_time))
dev_tuc_thread = Thread(target=get_parade15_data, args=(DEV_tuc, dev1_api_debugger, input_tuc_data, 'tuc', api_data, start_time))
# Start new Threads
sb_atx_data = sb_atx_thread.start()
#sb_ep_data = sb_ep_thread.start()
#sb_tuc_data = sb_tuc_thread.start()
dev_atx_data = dev_atx_thread.start()
dev_ep_data = dev_ep_thread.start()
dev_tuc_data = dev_tuc_thread.start()
# Add threads to thread list
threads.append(sb_atx_thread)
threads.append(sb_ep_thread)
threads.append(sb_tuc_thread)
threads.append(dev_atx_thread)
threads.append(dev_ep_thread)
threads.append(dev_tuc_thread)
# Wait for all threads to complete
for t in threads:
    t.join()
print "Exiting Main Thread"

#Write to CSV FILE
results = [['City', 'System', 'TestDate', 'Status', 'APIdebugger', 'TestDate']] + api_data
write_output_data(output_file_name, results)  # writing all of the data to the output csv file

'''