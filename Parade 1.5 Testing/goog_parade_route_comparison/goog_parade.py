import requests, datetime, json, httplib2, os, calendar, MySQLdb, time
from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, timedelta
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import sys
from address import AddressParser, Address
from pytz import timezone


def get_credentials():
    """Gets valid user credentials from storage.
    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.
    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'sheets.googleapis.com-python-quickstart.json')
    
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        try:
            import argparse
            flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
        except ImportError:
            flags = None
        SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
        CLIENT_SECRET_FILE = 'client_secret.json'
        APPLICATION_NAME = 'Google Sheets API Python Quickstart'
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def get_spreadsheet_data():

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?''version=v4')
    service = discovery.build('sheets', 'v4', http=http, discoveryServiceUrl=discoveryUrl)
    spreadsheetId = '1oeJrla9HW8T_758BmANqnM703NFvk_1q2DzXthppaKU'
    rangeName = 'Sheet1!A2:G'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheetId, range=rangeName).execute()
    values = result.get('values', [])

    return values

def get_google_apis(input_data, departure_time):
    print 'preparing apis for GOOGLE'
    goog_apis = []
    #departure_time = '02:00'
    google_url = 'https://maps.googleapis.com/maps/api/directions/json?'
    #goog_api_key = 'AIzaSyDsIC6DL9dgyAp2hjZlDdaB-f70IvO94u4' #This is the real key for this script m.salomon@metropia the one below was used only as a support for temporary testing
    goog_api_key = 'AIzaSyCqec7uPDVAh4toTqsVnbkh2IQL2PsmJRk'

    for i in input_data:
        route_id = i[0]
        city = i[1]
        actual_tt = i[6]

        if city == 'Austin':
            zone = 'US/Central'
            now_time = datetime.now(timezone(zone))
            dt = now_time.replace(year=now_time.year, month=now_time.month, day=now_time.day, hour=int(departure_time[:2]), minute=int(departure_time[-2:])) + timedelta(days=1)
            goog_departure_time = calendar.timegm(dt.utctimetuple())
        elif city == 'ElPaso':
            zone = 'US/Mountain'
            now_time = datetime.now(timezone(zone))
            dt = now_time.replace(year=now_time.year, month=now_time.month, day=now_time.day, hour=int(departure_time[:2]), minute=int(departure_time[-2:])) + timedelta(days=1)
            goog_departure_time = calendar.timegm(dt.utctimetuple())
        elif city == 'Tucson':
            zone = 'US/Arizona'
            now_time = datetime.now(timezone(zone))
            dt = now_time.replace(year=now_time.year, month=now_time.month, day=now_time.day, hour=int(departure_time[:2]), minute=int(departure_time[-2:])) + timedelta(days=1)
            goog_departure_time = calendar.timegm(dt.utctimetuple())
        else:
            print ('Excuse me wtf city did you chose? you can only pick austin, tucson or elpaso')

        #This chunk is to make google apis
        paramaters = 'origin=%s,%s&destination=%s,%s&departure_time=%s&key=%s' % (i[2], i[3], i[4], i[5], goog_departure_time, goog_api_key)  # these are al of the paramaters that we are to change
        #'origin=1790+E+River+rd+tucson&destination=1717+E+Glenn+st+tucson+az&key=' + goog_api_key' if there is a bug please see this parameters instead!
        g_api = [route_id, google_url+paramaters, city, actual_tt]
        goog_apis.append(g_api)

    return goog_apis

def get_system_apis(input_data, input_system, name, departure_time):
    print  'preparing apis for', name, '   ', input_system
    system_apis = []
    #departure_time = '02:00'

    if input_system == 'PD_GET':
        api_debugger = 'http://production.metropia.com/v1/static/debug.html?'  #PD API
        url_get = 'http://production.metropia.com/v1/business/route.json?' # SB GET
        atx, ep, tuc, nav_atx, nav_ep, nav_tuc = 'na', 'na', 'na', 'na', 'na', 'na' #avoid reference before assignment 

    elif input_system == 'SB_GET':
        api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?'  #SB API
        url_get = 'http://sandbox.metropia.com/sandbox_v1/business/route.json?' # SB GET
        atx, ep, tuc, nav_atx, nav_ep, nav_tuc = 'na', 'na', 'na', 'na', 'na', 'na' #avoid reference before assignment
        
    elif input_system == 'SB_POST':
        api_debugger = 'http://sandbox.metropia.com/sandbox_v1/static/debug.html?'  #SB API
        atx = 'http://54.244.202.51:8102/sp' #SB POST
        ep = 'http://54.244.202.51:8107/sp' #SB POST
        tuc = 'http://54.244.202.51:8103/sp' #SB POST
        nav_atx = 'http://ec2-54-191-155-1.us-west-2.compute.amazonaws.com:8152/navigation?' #'http://54.214.216.113:8152/navigation?' #SB POST Nav
        nav_ep = 'http://ec2-54-191-155-1.us-west-2.compute.amazonaws.com:8156/navigation?' #'http://54.214.216.113:8156/navigation?' #SB POST Nav
        nav_tuc = 'http://ec2-54-191-155-1.us-west-2.compute.amazonaws.com:8153/navigation?' #'http://54.214.216.113:8153/navigation?' #SB POST Nav

    elif input_system == 'DEV_POST':
        api_debugger = 'http://developer.metropia.com/dev1_v1/static/debug.html?' #DEV API
        atx = 'http://54.218.80.167:8102/sp' #DEV POST Parade
        ep = 'http://54.218.80.167:8107/sp'  #DEV POST Parade
        tuc = 'http://54.218.80.167:8103/sp' #DEV POST Parade
        nav_atx = 'http://ec2-54-149-86-192.us-west-2.compute.amazonaws.com:8152/navigation?' #'http://54.149.86.192:8152/navigation?' #DEV POST Nav
        nav_ep = 'http://ec2-54-149-86-192.us-west-2.compute.amazonaws.com:8156/navigation?' #'http://54.149.86.192:8156/navigation?' #DEV POST Nav
        nav_tuc = 'http://ec2-54-149-86-192.us-west-2.compute.amazonaws.com:8153/navigation?' #'http://54.149.86.192:8153/navigation?' #DEV POST Nav

    elif input_system == 'PD_POST':
        api_debugger = 'http://production.metropia.com/v1/static/debug.html?'  #PD API
        atx = 'http://54.213.163.191:8092/sp' #PD POST Parade
        ep = 'http://54.213.155.8:8097/sp' #PD POST Parade
        tuc = 'http://54.218.119.82:8093/sp' #PD POST Parade
        nav_atx = 'http://ec2-54-187-66-36.us-west-2.compute.amazonaws.com:8152/navigation?' #PD POST Nav
        nav_ep = 'http://ec2-54-187-66-36.us-west-2.compute.amazonaws.com:8156/navigation?' #PD POST Nav
        nav_tuc = 'http://ec2-54-187-66-36.us-west-2.compute.amazonaws.com:8153/navigation?' #PD POST Nav

    else:
        print 'You made a mistake picking the system there is a typo here: ', input_system


    for i in input_data:
        route_id = i[0]
        city = i[1]
        actual_tt = i[6]

        if city == 'Austin':
            url_post = atx
            nav_url = nav_atx
        elif city == 'ElPaso':
            url_post = ep
            nav_url = nav_ep
        elif city == 'Tucson':
            url_post = tuc
            nav_url = nav_tuc
        else:
            print ('Excuse me wtf city did you chose? you can only pick austin, tucson or elpaso ', city)
        space = '%2C%20'
        space2 = '%3A'
        hour = departure_time[:2]
        hour = departure_time[1] if departure_time[0] == '0' else departure_time[:2]
        api_debugger_paramaters = 'origin=%s%s%s&destination=%s%s%s&departtime=%s%s%s' % (i[2], space, i[3], i[4], space, i[5], hour, space2, departure_time[-2:])  # these are the parameters that have to be changed for the API debugger
        api_debugger_paramaters = api_debugger_paramaters+'&speed=0&course=112&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true'

        if "GET" in input_system:
        #This chunk is to make GET apis
            api_paramaters = 'startlat=%s&startlon=%s&endlat=%s&endlon=%s&departtime=' % (i[2], i[3], i[4], i[5])  # these are the paramaters that have to change with each request
            api_paramaters = api_paramaters+departure_time
            api_deb = api_debugger+api_debugger_paramaters
            api_list = [route_id, url_get+api_paramaters, api_deb]
            system_apis.append(api_list)

        #This chunk is to make POST apis
        elif "POST" in input_system:
            payload_ff = { "start_lat": i[2], "start_lon": i[3], "end_lat": i[4], "end_lon": i[5], "departure_time": departure_time, "toll": "true" }
            #payload_peak = { "start_lat": i[1], "start_lon": i[2], "end_lat": i[3], "end_lon": i[4], "departure_time": "17:15", "toll": "true" }
            nav_parameters = 'speed=0&course=3&startlat=%s&startlon=%s&endlat=%s&endlon=%s&nodes=' % (i[2], i[3], i[4], i[5])  # these are the paramaters that have to change with each request
            api_deb = api_debugger+api_debugger_paramaters
            api_list = [route_id, url_post, payload_ff, nav_url+nav_parameters, api_deb]
            system_apis.append(api_list)

        else:
            print ('Excuse me wtf city did you chose? you can only pick austin, tucson or elpaso ', city)

    return system_apis


def get_goog_response(google_api):
    print "getting google"
    goog_route_deets, goog_route_main, goog_route_similar = [], [], []
    counta = 1
    for i in google_api:
        route_id = i[0]
        url = i[1]
        city = i[2]
        actual_tt = i[3]
        inter = []
        #print (url)
        try:
            response = requests.get(url, timeout=10)
            status = response.status_code
            data = response.json()
            steps = data['routes'][0]['legs'][0]['steps']
            main_distance = round(data['routes'][0]['legs'][0]['distance']['value']*0.000621371, 2)
            main_eta = data['routes'][0]['legs'][0]['duration']['value']
            avg_d_turns = []
            count = 0
            turn = 0
            for j in steps:
                soup = BeautifulSoup(j['html_instructions'], "html.parser")
                try:
                    street = soup.contents[3].string
                except IndexError:
                    street = " "
                distance = round(j['distance']['value']*0.000621371, 2)
                duration = j['duration']['value']
                sum_of_d_for_turns = sum(avg_d_turns)
                deets = [route_id, 'google', turn, street, distance, duration]
                r_similar = [route_id, street, distance]
                if sum_of_d_for_turns + distance >= .5 and main_distance - sum_of_d_for_turns >= .5: 
                    turn = turn + 1
                    goog_route_deets.append(deets)
                    inter.append(r_similar)
                    avg_d_turns.append(distance)
                else:
                    pass
                
                count = count+1
                
            #print inter
            goog_route_similar.append(inter)
            avg = round(float(sum(avg_d_turns)/max(len(avg_d_turns), 1)), 2)
            main = [route_id, main_distance, main_eta, turn, avg, city, actual_tt]
            goog_route_main.append(main)
            avg_d_turns = []

        except:
            print 'error here', counta, url
            inter = [[route_id, None, None]]
            goog_route_similar.append(inter)
            main = [route_id, 'error', 'error', 'error', 'error', city, actual_tt]
            goog_route_main.append(main)
            counta = counta+1
            continue

        if (counta%50) == 0:
            print counta
        counta = counta+1


    return goog_route_deets, goog_route_main, goog_route_similar


def get_get_response(sandbox_api, system, name):
    print "getting ", name, "  ", system
    sb_route_deets, sb_route_main, sb_route_similar = [], [], []
    counta = 1
    for i in sandbox_api:
        route_id = i[0]
        url = i[1]
        api_d = i[2]

        try:
            route_data = requests.get(url).json()
            route = route_data['data']['route']
            navigator_url = route_data['data']['navigation_url']
            nav_response = requests.get(navigator_url).json()
            main_distance = route_data['data']['distance']
            eta = []
            avg_d_turns = []

            duration_d = defaultdict(int)
            for j in route:
                duration_d[j['link']] = j['time']*60
                eta.append(j['time']*60)

            main_eta = int(round(sum(eta), 0))
            nav_data = nav_response['data']
            d, t = [], []
            sb_response_dict = defaultdict(list)
            sb_response_list = []
            count = 0 
            turn = 0
            turn_t = 0

            for j in nav_data:
                road = j['road']
                distance = j['distance']
                link = j['link']
                time = duration_d[link]

                if road not in sb_response_dict['street'] and road != 'Destination' and road != "":
                    sb_response_dict['street'].append(str(road))
                    if count > 0:
                        d_sum = round(sum(d)*0.000189394, 2)
                        t_sum = round(sum(t), 0)
                        sb_response_dict['distance'].append(d_sum)
                        sb_response_dict['duration'].append(t_sum)
                        response = [route_id, 'sb', turn_t, road_prev, d_sum, t_sum]
                        similar = [route_id, road_prev, d_sum]
                        sum_of_d_for_turns = sum(avg_d_turns)

                        if sum_of_d_for_turns + d_sum >= .5 and main_distance - sum_of_d_for_turns >= .5: 
                            turn_t = turn_t + 1
                            sb_response_list.append(similar)
                            sb_route_deets.append(response)
                            #print 'here', sum_of_d_for_turns, d_sum
                        else:
                            pass

                        avg_d_turns.append(d_sum)
                        turn = turn + 1
                        d = []
                        t = []
                        d.append(distance)
                        t.append(time)
                        count = 0
                    else:
                        d.append(distance)
                        t.append(time)
                elif road in sb_response_dict['street'] and road != 'Destination' and road != "":
                    d.append(distance)
                    t.append(time)
                elif road == 'Destination':
                    d_sum = round(sum(d)*0.000189394, 2)
                    t_sum = round(sum(t), 0)
                    sb_response_dict['distance'].append(d_sum)
                    sb_response_dict['duration'].append(t_sum)
                    response = [route_id, 'sb', turn_t, road_prev, d_sum, t_sum]
                    similar = [route_id, road_prev, d_sum]
                    sum_of_d_for_turns = sum(avg_d_turns)

                    if sum_of_d_for_turns + d_sum >= .5 and main_distance - sum_of_d_for_turns >= .5: 
                        turn_t = turn_t + 1
                        sb_response_list.append(similar)
                        sb_route_deets.append(response)
                        #print 'here', sum_of_d_for_turns, d_sum
                    else:
                        pass
                    avg_d_turns.append(d_sum)
                    turn = turn + 1
                    d = []
                    t = []
                    d.append(distance)
                    t.append(time)
                    count = 0
                else:
                    continue
                count = count + 1
                road_prev = str(j['road'])
                
            #print sb_response_list
            sb_route_similar.append(sb_response_list)
            avg = round(float(sum(avg_d_turns)/max(len(avg_d_turns), 1)), 2)
            main = [route_id, main_distance, main_eta, turn_t, avg, api_d]
            sb_route_main.append(main)
            avg_d_turns = [] 

        except requests.exceptions.Timeout:
            print ('request timeout!', api_d)
        except ValueError:
            print ('something funky with this case', api_d)
        except:
            print 'error here', counta, api_d
            similar = [[route_id, None, None]]
            sb_route_similar.append(similar)
            main = [route_id, 'error', 'error', 'error', 'error', api_d]
            sb_route_main.append(main)
            counta = counta+1
            continue
        #print counta, api_d
        if (counta%50) == 0:
            print counta
        counta = counta + 1

        

    return sb_route_deets, sb_route_main, sb_route_similar


def get_post_response(developer_api, system, name):
    print "getting ", name, "  ", system
    dev_route_deets, dev_route_main, dev_route_similar = [], [], []
    counta = 1
    for i in developer_api:
        route_id = i[0]
        url = i[1]
        payload = i[2]
        nav_url = i[3]
        api_d = i[4]

        try:
            headers = {'content-type': 'application/json'}
            response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=60)
            data = json.loads(response.content)
            route_data = data['data']['route']
            main_distance = round(data['data']['distance'], 2)
            main_eta = int(round(data['data']['estimated_travel_time']*60,0))
            node_list = []
            [node_list.append(k['node']+1) for k in route_data]
            nodes = str(node_list)
            navigator_url = nav_url+nodes
            nav_response = requests.get(navigator_url).json()

            duration_d = defaultdict(int)
            for t in route_data:
                duration_d[t['link']] = t['time']*60

            nav_data = nav_response['data']
            d, t = [], []
            dev_response_dict = defaultdict(list)
            dev_similar_list = []
            count = 0 
            turn = 0
            turn_t = 0
            avg_d_turns = []
            for j in nav_data:
                road = j['road']
                distance = j['distance']
                link = j['link']
                time = duration_d[link]

                if road not in dev_response_dict['street'] and road != 'Destination' and road != "":
                    dev_response_dict['street'].append(str(road))
                    if count > 0:
                        d_sum = round(sum(d)*0.000189394, 2)
                        t_sum = round(sum(t), 0)
                        dev_response_dict['distance'].append(d_sum)
                        dev_response_dict['duration'].append(t_sum)
                        response = [route_id, 'dev', turn_t, road_prev, d_sum, t_sum]
                        similar = [route_id, road_prev, d_sum]
                        
                        sum_of_d_for_turns = sum(avg_d_turns)
                        if sum_of_d_for_turns + d_sum >= .5 and main_distance - sum_of_d_for_turns >= .5: 
                            turn_t = turn_t + 1
                            dev_similar_list.append(similar)
                            dev_route_deets.append(response)
                        else:
                            pass
                        avg_d_turns.append(d_sum)
                        turn = turn + 1
                        d = []
                        t = []
                        d.append(distance)
                        t.append(time)
                        count = 0
                    else:
                        d.append(distance)
                        t.append(time)
                elif road in dev_response_dict['street'] and road != 'Destination' and road != "":
                    d.append(distance)
                    t.append(time)
                elif road == 'Destination':
                    d_sum = round(sum(d)*0.000189394, 2)
                    t_sum = round(sum(t), 0)
                    dev_response_dict['distance'].append(d_sum)
                    dev_response_dict['duration'].append(t_sum)
                    response = [route_id, 'dev', turn_t, road_prev, d_sum, t_sum]
                    similar = [route_id, road_prev, d_sum]
                    sum_of_d_for_turns = sum(avg_d_turns)

                    if sum_of_d_for_turns + d_sum >= .5 and main_distance - sum_of_d_for_turns >= .5: 
                        turn_t = turn_t + 1
                        dev_similar_list.append(similar)
                        dev_route_deets.append(response)
                    else:
                        pass
                    avg_d_turns.append(d_sum)
                    turn = turn + 1
                    d = []
                    t = []
                    d.append(distance)
                    t.append(time)
                    count = 0
                else:
                    continue
                count = count + 1
                road_prev = str(j['road'])
                
            #print dev_response_list
            dev_route_similar.append(dev_similar_list)   # Make sure exception appends something for dev route similar otherwise there will me matching errors later on
            avg = round(float(sum(avg_d_turns)/max(len(avg_d_turns), 1)), 2)
            main = [route_id, main_distance, main_eta, turn, avg, api_d]
            dev_route_main.append(main)
            avg_d_turns = [] 
        
        except requests.exceptions.Timeout:
            print ('request timeout!', i[4])
        except ValueError:
            print ('something funky with this case', i[4])
        except:
            print 'error here', counta, i[4]
            similar = [[route_id, None, None]]
            dev_route_similar.append(similar)
            main = [route_id, 'error', 'error', 'error', 'error', api_d]
            dev_route_main.append(main)
            counta = counta+1
            continue
        #print counta, api_d
        if (counta%50) == 0:
            print counta
        counta = counta+1
    return dev_route_deets, dev_route_main, dev_route_similar


def same_path(similar_1, similar_2, name):
    print 'path similarity for  ', name
    route_a_2_route_b = []
    for i, j in map(None, similar_1, similar_2):
        a_dict, b_dict = defaultdict(int), defaultdict(int)
        ab = []
        ap = AddressParser()

        if i and j:

            if i[0][1] is not None:
                for x in i:
                    if "I 10" in x[1] or "Interstate " in x[1] or "I-" in x[1] or "US-" in x[1] or "TX-" in x[1] or "State Highway" in x[1] or  ' ' in x[1] and x[2] > .7:
                        ad1 = 'I-10'
                        if ad1 in a_dict:
                            a_dict[ad1] += x[2]
                        else:
                            a_dict[ad1] = x[2]
                    else:
                        address = ap.parse_address(x[1])
                        ad1 = address.street
                        if ad1 in a_dict:
                            a_dict[ad1] += x[2]
                        else:
                            a_dict[ad1] = x[2]
            else:
                a_dict['None'] = 0


            if j and j[0][1] is not None:
                for y in j:
                    if "I 10" in y[1] or "Interstate " in y[1] or "I-" in y[1] or "US-" in y[1] or "TX-" in y[1] or "State Highway" in y[1] or ' ' in y[1] and y[2] > .7:
                        ad2 = 'I-10'
                        if ad2 in b_dict:
                            b_dict[ad2] += y[2]
                        else:
                            b_dict[ad2] = y[2]
                    else:
                        address = ap.parse_address(y[1])
                        ad2 = address.street
                        if ad2 in b_dict:
                            b_dict[ad2] += y[2]
                        else:
                            b_dict[ad2] = y[2]
            else:
                b_dict['None'] = 0

            route_id = i[0][0]

            for key, a_d in a_dict.items():
                if key in b_dict:
                    b_d = b_dict[key]
                    same = min(a_d, b_d)
                else:
                    same = 0
                ab.append(same)
            sim = [route_id, round(sum(ab),2)]
            route_a_2_route_b.append(sim)

        else:
            route_id = int(route_id) + 1 
            sim = [str(route_id), 'na']
            route_a_2_route_b.append(sim)

    return route_a_2_route_b

    '''
    for i, j, k in zip(goog_response_deets ,sb_response_deets, dev_response_deets):
        g_dict[i[3]] = i[4]
        sb_dict[j[3]] = j[4]
        dev_dict[k[3]] = k[4]

    print 'dev', dev_dict 
    print 'sb', sb_dict
    print 'g', g_dict

    dev2sb = []
    for key, dev_d in dev_dict.items():
        if key in sb_dict:
            sb_d = sb_dict[key]
            same = min(dev_d, sb_d)
        else:
            same = 0
        dev2sb.append(same)
    print 'dev', sum(dev_dict.values())
    print 'sb', sum(sb_dict.values())
    print 'gog', sum(g_dict.values())
    print dev2sb
    '''

def clean_same(dev2sb, dev2goog, sb2goog):
    same_path = []
    for x, y, z in zip(dev2sb, dev2goog, sb2goog):
        if x[0] == y[0] == z[0]:
            row = [x[0], x[1], y[1], z[1]]
            same_path.append(row)
        else:
            print "wtf happened here sir! this values should always be numbered the same, please checl clean_same function", x[0], y[0], z[0]
    return same_path


def make_main(goog_response_main, sb_response_main, dev_response_main, similar_paths, input_system_wolf, input_system_lion):
    main = []
    temp, temp_2 = [], []
    for x, y, z in zip(goog_response_main, sb_response_main, dev_response_main):
        row = [x[0], time.strftime('%Y-%m-%d %H:%M:%S'), x[5], x[1], x[2], x[3], x[4], y[1], y[2], y[3], y[4], y[5], z[1], z[2], z[3], z[4], z[5], x[6]]
        temp.append(row)
    for v, r in zip(temp, similar_paths):
        if v[0] == r[0]:
            s = v + r[1:]
            temp_2.append(s)
        else:
            "for some reason there is a mismatch between clean_some and response_main please do us a favor and check the function make_main"
    for i in temp_2:
        i.append(input_system_wolf)
        i.append(input_system_lion)
        main.append(i)
    return main


def write_to_db(route_data):
    # ********Connect and write to DB
    db = MySQLdb.connect(host="192.168.1.95", user="mario", passwd="mario1234", db="ops", port=3300)   
    cur = db.cursor()
    cur.execute("SELECT test_run FROM route_compare_main order by main_id DESC Limit 1")
    last_test = str(cur.fetchone()[0]) 
    last_run_id = last_test.split(' ', 1)[0]

    sql_deets = """INSERT INTO route_deets (route_id, system, test_run, test_date, turn_num, street, distance, duration) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) """
    sql_main = """INSERT INTO route_compare_main (route_id, test_run, test_date, city, g_distance, g_eta, g_turns, g_avg_turn_distance, wolf_distance, wolf_eta, wolf_turns, wolf_avg_turn_distance, wolf_api_deb, lion_distance, lion_eta, lion_turns, lion_avg_turn_distance, lion_api_deb, actual_tt, lion2wolf, lion2g, wolf2g, wolf, lion, departure_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) """
    
    date = time.strftime('%Y-%m-%d %H:%M:%S')
    date_short = time.strftime('%Y%m%d')
    run_id = int(last_run_id)+1
    test_id = str(run_id)+' '+date_short
    #print route_data
    if len(route_data[0]) == 6:
        print ('Inserting OUTPUT Data into ROUTE_DEET Table')
        for row in route_data:
            row.insert(2, last_test)
            row.insert(3, date)
            if len(row) == 8:
                cur.execute(sql_deets, row)
            else:
                print ('number of items in row is incorrect'), row

    elif len(route_data[0]) == 23:
        print ('Inserting OUTPUT Data into ROUTE_MAIN Table')
        for row in route_data:
            row.insert(1, test_id)
            row.insert(24, departure_time)
            if len(row) == 25: 
                cur.execute(sql_main, row)
            else:
                print ('number of items in row is incorrect'), row
    else:
        print 'something wrong with the number of items in each row not matching any table', route_data[0]

    db.commit()
    db.close
    print ("Done and Done")

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
        #   print data
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


if __name__ == '__main__':
    reload(sys);
    sys.setdefaultencoding("utf8")
    input_data = get_spreadsheet_data()
    #first and foremost get your inputs from Jenkins
    try:
        departure_time = sys.argv[1]
        input_system_lion = sys.argv[2]
        input_system_wolf = sys.argv[3]
    except ValueError:
        print('Invalid input. Please enter somthing like: 02:00 SB POST DEV POST')
    #sample inputs
    #input_system_lion = 'SB_POST'#DEV Post, SB Get, SB Post, PD Get, PD Post
    #input_system_wolf = 'PD_POST' #DEV Post, SB Get, SB Post, PD Get, PD Post
    #departure_time = '02:00' #Select the desired departure time to cpmpare the routes

    system_lion_api = get_system_apis(input_data, input_system_lion, 'LION', departure_time)
    system_wolf_api = get_system_apis(input_data, input_system_wolf, 'WOLF', departure_time)
    google_api = get_google_apis(input_data, departure_time)

    '''
    #************CONCURRENT PARAMETERS FOR EACH SERVERS THREAD
    q = Queue(concurrent * 2)
    l_responses = []
    threads = [] #list to count and wait for the threads
    # Create new threads
    sb_thread = Thread(target=call_thread, args=([sandbox_api]))
    dev_thread = Thread(target=call_thread, args=([developer_api]))
    goog_thread = Thread(target=call_thread, args=([google_api]))
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
    '''
    
    if 'GET' in input_system_lion: 
        lion_response_deets, lion_response_main, lion_response_similar = get_get_response(system_lion_api, input_system_lion, 'LION')
    elif 'POST' in input_system_lion:
        lion_response_deets, lion_response_main, lion_response_similar = get_post_response(system_lion_api, input_system_lion, 'LION')

    if 'GET' in input_system_wolf: 
        wolf_response_deets, wolf_response_main, wolf_response_similar = get_get_response(system_wolf_api, input_system_wolf, 'WOLF')
    elif 'POST' in input_system_wolf:
        wolf_response_deets, wolf_response_main, wolf_response_similar = get_post_response(system_wolf_api, input_system_wolf, 'WOLF')

    goog_response_deets, goog_response_main, goog_response_similar = get_goog_response(google_api)

    
    
    lion2wolf = same_path(lion_response_similar, wolf_response_similar, 'lion2wolf')
    lion2goog = same_path(lion_response_similar, goog_response_similar, 'lion2goog')
    wolf2goog = same_path(wolf_response_similar, goog_response_similar, 'wolf2goog')

    similar_paths = clean_same(lion2wolf, lion2goog, wolf2goog)

    main_table = make_main(goog_response_main, wolf_response_main, lion_response_main, similar_paths, input_system_wolf, input_system_lion)

    write_to_db(main_table)

    '''
    write_to_db(dev_response_deets)
    write_to_db(goog_response_deets)
    write_to_db(sb_response_deets)
    '''
