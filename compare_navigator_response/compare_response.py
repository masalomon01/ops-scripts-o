import requests
import os
from os import listdir
from os.path import isfile, join
import json
import csv
import re

def get_nav_response(url):
    route_data = requests.get(url).json()
    navigator_url = route_data['data']['navigation_url']
    return requests.get(navigator_url).json()

def compare_instructions(old_instructions, new_instructions, old_status):
    if old_instructions == new_instructions:
        outfile = ('instructions are exactly the same\n')
        if old_status == 'pass':
                new_status = old_status
        elif old_status == 'fail':
            new_status = old_status
        else:
                new_status = "weird old_status please check"
        return outfile, new_status

    link_sequence1 = [x['link_id'] for x in old_instructions]
    link_sequence2 = [x['link_id'] for x in new_instructions]
    if link_sequence1 != link_sequence2:
        outfile = ('link sequences are different\n')
        new_status = 'invalid different routes'
        return outfile, new_status
        
    voice_sequence1 = [x['voice'] for x in old_instructions]
    voice_sequence2 = [x['voice'] for x in new_instructions]
    for v1, v2 in zip(voice_sequence1,voice_sequence2):
        if v1 != v2:
            change = '%s became %s' % (v1, v2)
            outfile = (change)
            if old_status == 'pass':
                new_status = 'fail'
            elif old_status == 'fail':
                new_status = 'check'
            else:
                new_status = "weird old_status please check"

            return outfile, new_status
           



def read_nav_response(response):
    links = response['data']
    iterator = iter(links)
    all_links = []  # list of dictionaries that contain relevant attributes
    for item in iterator:
        link_attributes = {'link_id': item['link']}
        try:
            link_attributes['voice'] = item['voice']
        except KeyError:
            link_attributes['voice'] = None
        all_links.append(link_attributes)
    return all_links

if __name__ == '__main__':
    # get all the input files; must be named routeX.json
    in_folder = os.getcwd()
    files = [f for f in listdir(in_folder) if isfile(join(in_folder, f)) and f[-5:]=='.json' and f[:5] == 'route']
    files = listdir
    #for f in files:
    #    info = json.load(open(in_folder+f,'r'))
    #    route_url = info['route_url']
    #    old_data = info['data']

    routes = json.load(open('routes.json','r'))
    with open('route_comparison.csv', 'wb') as w:
        writer = csv.writer(w)
        writer.writerow(["Test Results", "Old Status", "New Status", "City", "Case", "Intructions Change", "Route URL"])
        for route in routes:
            r_test = []
            route_url = route['route_url']
            rep = {"business": "static", "route": "debug", "json": "html", "startlat": "origin", "&startlon=": "%2C+", "endlat": "destination", "&endlon=": "%2C+"}
            rep = dict((re.escape(k), v) for k, v in rep.iteritems())
            pattern = re.compile("|".join(rep.keys()))
            url, sep , tail = pattern.sub(lambda m: rep[re.escape(m.group(0))], route_url).partition('&_=')
            t0 = url.split(':')[0]
            t1 = url.split(':')[1]
            t2 = url.split(':')[2]
            t2 = t2.replace(t2[:2], "%3A00")
            url = t0 + ':' + t1 + t2
            old_data = route['data']
            old_status = route['status']
            city = route['city']
            case = route['case']

            new_navigator_response = get_nav_response(route_url)
            new_data = read_nav_response(new_navigator_response)
            #compare_instructions(old_data, new_data, out_changelog)
            out_change = compare_instructions(old_data, new_data, old_status)
            new_status = out_change[1]
            ins_change = out_change[0]

            if new_status == old_status:
                test = 'same'
            elif new_status != old_status:
                if new_status == 'fail' and old_status == 'pass':
                    test = 'regressed'
                elif new_status == 'check' and old_status == 'fail':
                    test = 'check nav response'
                elif new_status == 'invalid different routes':
                    test = 'invalid route'
                else:
                    test = 'weird old_status'

            r_test = [test, old_status, new_status, city, case, ins_change, url]
            writer.writerow(r_test)
