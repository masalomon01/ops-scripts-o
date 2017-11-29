import csv 

def get_input_data(input_file):
    input_data = []
    with open(input_file, 'rb') as f:  # getting input data
        reader = csv.reader(f)
        input_data = list(reader)
    return input_data


def get_total_count(turn_link_pairs, use_cases):
	usecase_count = []
	tagged_data = []
	iterdata = iter(turn_link_pairs)
	next(iterdata)
	for i in iterdata:
		usecase_id = i[4]+'&'+i[5]+'&'+i[3]
		i.append(usecase_id)
		tagged_data.append(i)
	itercase = iter(use_cases)
	next(itercase)
	for i in itercase:
		count = get_count(i[0], tagged_data)
		i.append(count)
		usecase_count.append(i)
	return usecase_count	


def get_count(case, tagged_data):
	iterdata = iter(tagged_data)
	next(iterdata)
	count = 0
	for i in iterdata:
		if i[9] == case:
			count = count +1
		else:
			continue
	return count 


def get_differences(Will, Asif):
	w = []
	a = []
	iterwill = iter(Will)
	iterasif = iter(Asif)
	next(iterwill)
	next(iterasif)
	for i in iterwill:
		usecase_id = i[4]+'&'+i[5]+'&'+i[3]
		new = i[1:6]
		new.append(usecase_id)
		w.append(new)
	for i in iterasif:
		usecase_id = i[4]+'&'+i[5]+'&'+i[3]
		new = i[1:6]
		new.append(usecase_id)
		a.append(new)
	first_set = set(map(tuple, w))
	secnd_set = set(map(tuple, a))
	x = first_set.symmetric_difference(secnd_set) 
	y = first_set.difference(secnd_set) 
	z = secnd_set.difference(first_set) 
	diff = [list(elem) for elem in x]
	Will_not_in_Asif = [list(elem) for elem in y]
	Asif_not_in_Will = [list(elem) for elem in z]
	for i in Will_not_in_Asif:
		i.append('Will')
	for i in Asif_not_in_Will:
		i.append('Asif')

	return diff, Will_not_in_Asif, Asif_not_in_Will


def get_diff_cases(diff, use_cases):
	iterdata = iter(use_cases)
	next(iterdata)
	usecase_count = []
	for i in iterdata:
		count = get_diff_count(i[0], diff)
		i.append(count)
		usecase_count.append(i)
	return usecase_count


def get_diff_count(case, diff):
	count = 0
	for i in diff:
		if i[5] == case:
			count = count + 1
		else:
			continue
	return count 


def get_percentages(count):
	final = []
	final.append(['ID', 'USE_CASE', 'Will_Total', 'Asif_Total', 'Will_not_in_Asif', 'Asif_not_in_Will','tot_difference', 'Percentage_diff_Will', 'Percentage_diff_Asif', 'percentage_combined'])
	for i in count:
		if i[8] > 0:
			p1 = (float(i[10]) / float(i[8]))*100
		elif i[8] == 0:
			p1 = 0
		i.append(p1)
		if i[9] > 0:
			p2 = (float(i[11])/float(i[9]))*100
		elif i[9] == 0:
			p2 = 0
		i.append(p2)
		comb = (p2+p1)/2
		i.append(comb)
		x = [i[0], i[7], i[8], i[9], i[10], i[11], i[12], i[13], i[14], i[15]]
		final.append(x)

	return final


def write_output_data(filename, input_data):
	print 'writing the csv ' 
	with open(filename, 'wb') as f:
		writer = csv.writer(f)
		for i in input_data:
			writer.writerow(i)


def get_api_debugger(differences):
	difference_list = []
	difference_list.append(['from_link', 'to_link', 'turn_type', 'from_ltype', 'to_ltype', 'usecase_id', 'Code_output', 'API_debugger_link'])
	for i in differences:
		x = get_points(i[0], i[1], i)
		difference_list.append(x)
	return difference_list


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

	dev1_api_debugger = 'http://developer.metropia.com/dev1_v1/static/debug_dev.html?departtime=2:00&speed=0&course=&occupancy=1&vehicle_type=&etag=true&hov=true&hot=true&toll=true&'
	api_debugger_paramaters = 'origin=%s,%s&destination=%s,%s' % (startlat, startlon, endlat, endlon)  # these are the parameters that have to be changed for the API debugger
	DEV_api_deb = dev1_api_debugger+api_debugger_paramaters
	case.append(DEV_api_deb) # if you get an error for calling a variable before assigned you are probably using the wrong wkt file

	return case


usecase_diff = 'mandel_diff.csv'
differents = 'differences_list.csv'
use_cases = get_input_data('Mandel_Use_Cases.csv')
Will = get_input_data('turn_link_pairs_Will.csv')
Asif = get_input_data('turn_link_pairs_Asif.csv')
wkt_data = get_input_data('links_wkt_elpaso.csv')

diff, Will_not_in_Asif, Asif_not_in_Will = get_differences(Will, Asif)

count = get_total_count(Will, use_cases)
print 'Will tots done'
count = get_total_count(Asif, use_cases)
print 'Asif tots done'
count = get_diff_cases(Will_not_in_Asif, use_cases)
print 'Will not Asif done'
count = get_diff_cases(Asif_not_in_Will, use_cases)
print 'Asif not Will done'
count = get_diff_cases(diff, use_cases)
print 'tot diff done'
final = get_percentages(count)
print 'final done'
write_output_data(usecase_diff, final)


differences = Will_not_in_Asif + Asif_not_in_Will
print len(differences), len(diff)
difference_list = get_api_debugger(differences)
print difference_list[0:20]
write_output_data(differents, difference_list)


# This is part one, we can already start seeing the differences by use case, next we need a file that has all the use cases
# and api debugger links to be able to quickly determine what the turn should be thru qa/qc and manually start tagging them. 
# once they are starting to get tagged, we can report and confirm systematic changes vs undesired changes. 

'''
pseudo code
iterate over all of the mandel different use_cases
get the start point and end point for every use_case (get this code from mandel estimation)
finally compose the api debugger url and write output
sample output:
from_link, to_link, turn type, ltype, ltype, Will or Asif, API Debug Link
'''
