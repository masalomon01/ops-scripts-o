# The purpose of this script is to use the Zendesk API to categorize and take note of all Zendesk Tickets. Right now it just gets all the tickets
# and puts them in an excel file, but will eventually add the functionality to specify two dates, and only get tickets from inbetween those dates.
import requests
import xlsxwriter
import datetime
import pyodbc
import string

# This method takes in a string which is the description of a redemption. It will parse through the description until it finds the '@' character. It then 
# gets the word that is the email address and returns it
def get_email_from_redemption(string):
    words = string.split()  # words is a list that contains all of the words in the descrption

    for word in words: # goes through every word until the first word with '@', and then makes that the word it returns
        if '@' in word:
            if word.endswith('.'): # addresses issue that a lot of email addresses are ending with a period so it isn't matching any SQL searches
                return word[:-1]
            else:
                return word
        
    return ''  # if doesn't find an email just returns an empty string


# This method takes in a pyodbc connection and returns a dictionary that contains the users email, DevideID, MetropiaVersion, Market, and UserLevelTypeID.
# This is for the purpose of making all the connections to the database at the beggining of the script, and then just using this dictionary to get all user
# data because it contains all the information of a user we will need
def get_user_emails(cnxn):

    page_num = 0 # JSON data is in pages so start with page zero
    user = 'info@metropia.com'  # Zendesk credentials
    pwd = 'metropi@power99'
    user_emails_id = {}  # empty dictionary soon to be filled with user information
    cursor = cnxn.cursor()  # establishing a cursor with the connection passed to the method


    while 1:  # loop that iterates through all user pages in order to get all email addresses
        url = 'https://metropia.zendesk.com/api/v2/users.json?page=' + str(page_num)
        response = requests.get(url, auth=(user, pwd))
        data = response.json()  # getting data from the correct Zendesk ticket page
        
        for i in range(0, len(data['users'])):  # iterating through all of the users in the data variable returned by API
            sql = '''select DeviceID, MetropiaVersion, Market, UserLevelTypeID
            from metropian where email = '%s\'''' % data['users'][i]['email']  # sql statement used to get user data

            cursor.execute(sql)  # executing the sql statement
            info = cursor.fetchone()  # fetching the first row returned
            try:
                user_emails_id[data['users'][i]['id']] = [data['users'][i]['email'], info[0], info[1], info[2], info[3]] # creating dictionary
            except TypeError:
                user_emails_id[data['users'][i]['id']] = [data['users'][i]['email'], None, None, None, None]  # if nothing was returned so info has no elements, will fill it with null
        if not data['next_page']: # when there isn't a next page will break out
            break
        
        page_num = page_num + 1  # so it will go through the next page
    return user_emails_id # returns dictionary with email address as key and zendesk id as value


# This function takes in the category and description of the ticket and returns the category. This function doesn't do well because
# with the current feedback page we don't control the language (with categories and subcategories) of how a user communicates feedback to us. This problem
# should be fixed with the deployment of HelpDesk.
def get_category(category, description):
    if 'redemption' in category:  # all redemptions have the word 'redemption' in them, so it will return that first
        return 'Redemption'
    simple_description = makeSimple(str(description))  # making all words lowercase and getting rid of all punctuation and returning in a string
    if 'point' in category or 'point' in simple_description:  # goes through seeing if it is a part of any made category that we have
        return 'Point'
    elif 'bad_route' in category or 'route' in simple_description:
        return 'Routing'
    elif 'api' in category or 'bug' in simple_description:
        return 'Bug'
    elif 'duo' in category or 'duo' in simple_description:
        return 'DUO'
    elif ('Amazon.com' in category) or ('Item(s)' in category) or ('eGift' in category) or ('Termination' in category) or ('shipment' in category) or ('Target' in category): # this is if there is a ticket that we aren't going to put on spreadsheet
        return 'skip'
    else:
        return ''


# This method gets passed the description of a ticket and returns a list of all the words in the ticket without punctuation and lowercase.
# This is in order to not have punctutation or capitalization mess up the categorization in the get_category method.
def makeSimple(text):
    beg = 0
    end = 0
    words = []  # a list that is going to contain all of the simplified words that are sent in
    for character in text:  # splits the string into the seperate words
        if character == ' ':
            new_word = str(text[beg:end]).translate(string.maketrans("",""), string.punctuation).lower()
            words.append(new_word)  # getting rid of all puncutation and making all words lowercase
            beg = end + 1
        end = end + 1
    if not beg: # if there is only one word
        new_word = str(text).translate(string.maketrans("",""), string.punctuation).lower()
        words.append(new_word)  # getting rid of all puncutation and making all words lowercase
    else:
        new_word = str(text[beg:]).translate(string.maketrans("",""), string.punctuation).lower()  # getting the last word
        words.append(new_word)  # getting rid of all puncutation and making all words lowercase

    return words  # returning the list of simple words


# This function gets all of the headers and prints them on the first row of the excel file. return void.
def print_headers_to_worksheet(headers):
    col = 0
    for title in headers:
        worksheet.write(0, col, title)
        col += 1
    col = 1


# This is a method which takes in a dictionary which contains user information with the key as a users email address, and then gets the
# ticket information and the user information from the user that reported the ticket. Then returns void
def get_tickets(email_id_list): # gets the ID of the agent and the dictionary of emails and ids and then prints them into excel sheet
    print 'in get tickets function'
    row = 1
    user = 'info@metropia.com'
    pwd = 'metropi@power99'
    start_time = 1459814400 # April 5th 2016
    all_words = []

    while 1:

        url = 'https://metropia.zendesk.com/api/v2/incremental/tickets.json?start_time=' + str(start_time)  # accessing Zendesk API that contains archived tickets
        response = requests.get(url, auth=(user, pwd)) # makes sure it connects to URL successfully
        
        if response.status_code != 200: # TODO: make this so if the error code is too many requests (429), wait until that amount of time is up and start again
            print('Status:', response.status_code)
            print url
            break

        data = response.json()
        ticket_list = data['tickets']  # getting the list of all the tickets in that page
        start_time = data['end_time']  # getting the start time for the next iteration through
        
        for ticket in ticket_list:  # loop that will go through each ticket in the entire page sent back by the API
            email = 'None'  # initializing all variables to None
            OS = 'None'
            MetropiaVersion = 'None'
            Location = 'None'
            internal = None

            category = get_category(ticket['raw_subject'], str(ticket['description'].encode('utf-8'))) # calling function to get the category that will go in spreadsheet
            
            if category == 'Redemption':  # TODO: Make this a function that just returns a list of user data
                email = get_email_from_redemption(ticket['description'])  # gets the email from the subject of the redemption
                for id_dict, info in email_id_list.iteritems():  # iterating over the dictionary to get the information of the user who made the ticket
                    if info[0] == email:  # if it gets the correct email
                        if info[1] != None:
                            if 'APA' == info[1][:3]:  # if it is android (can tell if first three characters of device id are APA)
                                OS = 'Android'
                            else:
                                OS = 'iOS'
                        MetropiaVersion = info[2]  # getting all user information
                        Location = info[3]
                        internal = info[4]
                        break
            else:  # if not a redemption, so the submitter_id is the user (versus when it is a redemption and the submitter is always info@metropia.com)
                try:
                    email = email_id_list[ticket['submitter_id']][0]
                    if email_id_list[ticket['submitter_id']][1] != None:
                        if 'APA' == email_id_list[ticket['submitter_id']][1][:3]:
                            OS = 'Android'
                        else:
                            OS = 'iOS'
                    MetropiaVersion = str(email_id_list[ticket['submitter_id']][2])
                    Location = str(email_id_list[ticket['submitter_id']][3])
                    internal = email_id_list[ticket['submitter_id']][4]
                except KeyError, detail:
                    print detail

            if category != 'skip' and email != '' and internal == None: # if already in spreadsheet or ticket we don't care about it will not get printed to spreadsheet
                print email
    
                if ticket['status'] == 'solved' or ticket['status'] == 'closed': # will mark the ticket as resolved if the status is either closed or solved
                    issue_resolved = 1
                else:
                    issue_resolved = 0

                print_data_to_worksheet(ticket, email, OS, MetropiaVersion, Location, category, issue_resolved, row)  # printing all the data to the spreadsheet
                row += 1

        if not start_time:  # if there is no other page after iterating through all of the tickets, it will break out and end function
            break


# This method takes in all of the data needed to be printed to a worksheet, and then writes all of the data in the corresponding row. returns void.
def print_data_to_worksheet(ticket, email, OS, MetropiaVersion, Location, category, issue_resolved, row):
    worksheet.write(row, 0, ticket['created_at'][:10]) # writing full date
    worksheet.write(row, 1, ticket['created_at'][11:19]) # writing time
    worksheet.write(row, 2, int(ticket['created_at'][0:4])) # writing year
    worksheet.write(row, 3, int(ticket['created_at'][5:7])) # writing month
    worksheet.write(row, 4, email) #writes email address
    worksheet.write(row, 5, OS) # writes OS 
    worksheet.write(row, 6, MetropiaVersion) # writes MetropiaVersion
    worksheet.write(row, 7, Location) # writes Location
    worksheet.write(row, 8, category) # writing category
    worksheet.write(row, 9, issue_resolved) # writes if the issue is resolved or not
    worksheet.write(row, 10, ticket['id']) # printing the ticket # which could be added to the current spreadsheet
    worksheet.write(row, 11, ticket['description'])  # printing the description

print 'starting the zayne train'
cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.95;DATABASE=Complete;UID=mario;PWD=mario1234;')  # connecting to db, need to change if not using windows machine
print 'connected to db'
user_emails_id = get_user_emails(cnxn) # getting email and id dictionary to send to function
cnxn.close()  # closing connection
print 'got user information and closed connection with db'
workbook = xlsxwriter.Workbook('Zendesk Total Data Test.xlsx', {'strings_to_urls': False}) # opening excel file and doesn't turn strings into urls
worksheet = workbook.add_worksheet('General Data') # creates a workseet
headers = ['Full Date', 'Time', 'Year', 'Month', 'Email', 'OS', 'MetropiaVersion','City', 'Category', 'Resolved', 'Ticket #', 'Description']
print_headers_to_worksheet(headers)  # printing the headers to the spreadsheet
print 'created work book'
get_tickets(user_emails_id)  # getting the zendesk tickets
try:
    workbook.close()
except detail:
    print "Couldn't create file because detail:" + str(detail)
    exit(1)