import os
import io
import re
import csv
from xlwt import Workbook

path = '/Users/Mario/Documents/GitHub/ops-scripts/Parade Exception finder/'


files = [i for i in os.listdir(path) if os.path.isfile(os.path.join(path,i)) and \
         'log.' in i]

result = ""
list1 = ['Error Message']
list2 = ['Origin']
list3 = ['Destination']
data = []
if __name__=="__main__":
	# for all log files
	for index in range(len(files)):
		files[index]

		file = open(path+files[index], "r")
		cfile = files[index]
		
		city = re.findall(r'log.(.*?).production',cfile)
		city = "".join(city)
		city = city.title()

		start = -1
		end = -1

		lines = file.readlines()
		for line in lines:
			start += 1
			if line.startswith('java.lang'):
				#print lines[start]
				result += lines[start]
				#list1.append(lines[start])
				end = start
				flag = 0
				while not lines[end].startswith('INFO:') and flag is 0:
					end += 1
					if lines[end].startswith('java.lang'):
						flag = 1
				if lines[end].startswith('INFO:') and flag is 0:
					lat_lon_pattern = re.compile("startlat=.*depart")
					search_OD = lat_lon_pattern.search(lines[end])
					if search_OD:
						OD = search_OD.group() + "\n"
						index = 0
						iteration = 0
						startLat = ""
						startLon = ""
						endLat = ""
						endLon = ""

						while index < len(OD):
							if OD[index] == '=' and iteration == 0:
								index += 1
								while(OD[index] !=  '%'):
									startLat = startLat + OD[index]
									index += 1
									iteration = 1
							if OD[index] == '=' and iteration == 1:
								index += 1
								while(OD[index] != '%'):
									startLon = startLon + OD[index]
									index += 1
									iteration = 2
							if OD[index] == '=' and iteration == 2:
								index += 1
								while(OD[index] !=  '%'):
									endLat = endLat + OD[index]
									index += 1
									iteration = 3
							if OD[index] == '=' and iteration == 3:
								index += 1
								while(OD[index] != '%'):
									endLon = endLon + OD[index]
									index += 1
							index += 1
						#print startLat + ", " + startLon
						result += startLat + ", " + startLon + "\n"
						#list2.append(startLat + ", " + startLon)
						#print endLat + ", " + endLon
						result += endLat + ", " + endLon + "\n"
						#list3.append(endLat + ", " + endLon)
						#print "\n"
						query_route = [city, startLat, startLon, endLat, endLon]
						data.append(query_route)
						#print query_route
	#print result
						#example = []
	flag = 0
	exception = ""
	for line in result.splitlines():

		if (line[0:12] == 'java.lang.Nu' or line[0:12] == 'java.lang.In') and flag == 0:
			exception += line
			flag = 1
		elif (line[0:12] == 'java.lang.Nu' or line[0:12] == 'java.lang.In') and flag == 1:
			exception += " & " + line
		elif line[0] != 'j' and flag == 1:
			list1.append(exception)
			exception = ""
			list2.append(line)
			flag = 0
		elif line[0] != 'j' and flag == 0:
			list3.append(line)

	#print list1
	#print list2
	#print list3

	book = Workbook()
	sheet1 = book.add_sheet('Sheet 1')

	n = 0
	for row in list1:
		sheet1.write(n, 0, row)
		n += 1
	n = 0
	for row in list2:
		sheet1.write(n, 1, row)
		n += 1
	n = 0
	for row in list3:
		sheet1.write(n, 2, row)
		n += 1

	
	book.save(path + "outputny.xls")

with open('for_compare_routes.csv', 'wb') as f:
	writer = csv.writer(f)
	header = ['City', 'StartLatitude', 'StartLongitude', 'EndLatitude', 'EndLongitude']
	writer.writerow(header)
	for i in data:
		writer.writerow(i)