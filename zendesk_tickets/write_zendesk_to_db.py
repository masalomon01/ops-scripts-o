'''
write_zendesk_to_db.py
Author: Daniel Tranfaglia

Purpose: This script pulls ticket data from Zendesk and writes it into the
ticket_responses database everyday in the early morning hours.
'''





import pyodbc
import requests
import string

from datetime import datetime





def get_ticket_data (username, password, ticket_id):
    '''
    Purpose: Uses Metropia's Zendesk credentials to pull ticket data from the Zendesk API.

    Parameters:
        username -- Username to log in for data access.
        password -- Password to log in for data access.
        ticket_id -- ID of the ticket to get ticket data.

    Returns: Dictionary of ticket data for the given ticket in Zendesk.
    '''

    ticket_url = 'https://metropia.zendesk.com/api/v2/tickets/' + str(ticket_id)
    ticket_response = requests.get(ticket_url, auth=(username, password))
    ticket_data = ticket_response.json()

    return ticket_data





def get_metrics_data (username, password, ticket_id):
    '''
    Purpose: Uses the given credentials to pull and return metrics data.

    Parameters:
        username -- Username to log in for data access.
        password -- Password to log in for data access.
        ticket_id -- ID of the ticket to get metrics for.

    Returns: Dictionary of metrics data for the given page in Zendesk.
    '''

    metrics_url = 'https://metropia.zendesk.com/api/v2/tickets/' + str(ticket_id) + '/metrics.json'
    metrics_response = requests.get(metrics_url, auth=(username, password))
    metrics_data = metrics_response.json()
    
    return metrics_data





def get_comments_data (username, password, ticket_id):
    '''
    Purpose: Uses the given credentials to pull and return comments data.

    Parameters:
        username -- Username to log in for data access.
        password -- Password to log in for data access.
        ticket_id -- ID of the ticket to get comments data.

    Returns: Dictionary of comments data for the given ticket in Zendesk.
    '''

    comments_url = 'https://metropia.zendesk.com/api/v2/tickets/' + str(ticket_id) + '/comments.json'
    comments_response =  requests.get(comments_url, auth=(username, password))
    comments_data = comments_response.json()

    return comments_data





def parse_comments (comments_data):
    '''
    Purpose: Takes comments data for a ticket and searches the contents of
        each comment by line. If a line starts with a key phrase, the data
        is returned after all comments have been searched and parsed.
        
        Data returned includes: City, App Version, Mobile Provider, and Type of Phone.
        
    Parameters:
        comments_data -- Comments data from a ticket in Zendesk.

    Returns: Dictionary of user data parsed from the comments on a ticket.
    '''

    # Build from an empty dictionary
    parsed_data = {'email': '', 'city': '', 'app_version': '', 'OS': '', 'mobile_provider': '', 'type_of_phone': ''}

    for comment in comments_data:
        lines = comment['body'].split('\n')     # Split comment by lines

        # Search the beginning of each line for key phrases, and store
        # the associated data in the dictionary
        for line in lines:
            if line.startswith('Account Email') and len(line.split(': ')) == 2:
                parsed_data['email'] = (line.split(': ')[1])[:50]
            elif line.startswith('App Version') and len(line.split(': ')) == 2:
                parsed_data['app_version'] = (line.split(': ')[1])[:50]
            elif line.startswith('City') and len(line.split(': ')) == 2:
                parsed_data['city'] = (line.split(': ')[1])[:50]
            elif line.startswith('Mobile Provider') and len(line.split(': ')) == 2:
                parsed_data['mobile_provider'] = (line.split(': ')[1])[:50]
            elif line.startswith('OS') and len(line.split(': ')) == 2:
                parsed_data['OS'] = (line.split(': ')[1])[:50]
            elif line.startswith('Type of Phone') and len(line.split(': ')) == 2:
                parsed_data['type_of_phone'] = (line.split(': ')[1])[:50]

    return parsed_data





def read_starting_ticket ():
    '''
    Purpose: Opens a file named 'starting_ticket.txt' and returns the number that
        appears on the first line as an integer. This number is the ticket ID of
        the first ticket that this script will write to the database.

    Parameters: N/A.

    Returns: Starting ticket ID as an integer.
    '''

    filename = 'starting_ticket.txt'        # Name of the file to read ID

    file = open(filename, 'r')                    # Prepare to read the file
    starting_ticket = int(file.readline())      # Read the file and parse the ticket ID

    return starting_ticket      # Return the starting ticket to write





def update_starting_ticket (ticket_id):
    '''
    Purpose: Stores the given ticket ID to a file called 'starting_ticket.txt'.
        This file will keep track of where the script will begin pulling data
        everyday.

    Parameters:
        ticket_id -- Ticket ID to write to the file.

    Returns: None.
    '''

    filename = 'starting_ticket.txt'    # Name of the file to store ID

    file = open(filename, 'w')      # Create or overwrite file
    file.write(str(ticket_id))      # Write the given ticket ID

    file.close()    # Close file





def write_to_db ():
    '''
    Purpose: Pulls data from Zendesk to write in the ticket_responses database.
        Data includes ticket id, ticket metrics data, and comments data.

    Parameters: N/A.

    Returns: None.
    '''

    # Connect to DB
    print("Connecting to database...")
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER=192.168.1.95;DATABASE=HelpCenter;UID=daniel;PWD=Hala_Madrid123')
    print('Connection successful!')

    # Begin pulling and writing data into the database
    print('\nWriting to database...')

    cursor = cnxn.cursor()  # Cursor for DB operations
    
    # Zendesk credentials
    username = 'info@metropia.com'    # Username
    password = 'metropi@power99'      # Password

    # Get the first ticket to start pulling data from
    ticket_id = read_starting_ticket()

    # Track the end of tickets: if 100 ticket IDs in a row have no records, database updating is complete
    skipped_tickets = 0

    while 1:
        # Use credentials to access ticket data
        ticket_data = get_ticket_data(username, password, ticket_id)

        # Check if there are records for the current ticket

        # Records DO NOT exist for this ticket, skip it
        if 'ticket' not in ticket_data:
            ticket_id += 1                  # Next ticket
            skipped_tickets += 1            # Ticket has been skipped
            #print('Ticket ' + ticket_id + ' does not exist')
            if skipped_tickets == 20:       # If 20 tickets in a row have been skipped, end program
                break
            continue
        # Records exist for this ticket, write to or update database
        else:
            skipped_tickets = 0
            ticket_data = ticket_data['ticket']

        # Use credentials to access metrics data for the current ticket
        metrics_data = get_metrics_data(username, password, ticket_id)['ticket_metric']

        # Use credentials to access ticket comments information
        comments_data = get_comments_data(username, password, ticket_id)['comments']
    
        # Get user data from the comments on the ticket
        user_data = parse_comments(comments_data)

        # Get the time the insertion into the DB began for the current ticket
        time_inserted = str(datetime.today())[:-7]

        # Insert data into the 'ticket' table
        cursor.execute("""INSERT INTO [HelpCenter].[dbo].[ticket] (ticket_id, user_email, ticket_status, reply_amount, time_created, time_solved, time_updated, latest_reply_date, response_minutes_calendar, response_minutes_business, satisfaction_rating, time_inserted) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                       (ticket_id, user_data['email'], ticket_data['status'], metrics_data['replies'], metrics_data['created_at'], metrics_data['solved_at'], metrics_data['updated_at'], metrics_data['latest_comment_added_at'], metrics_data['reply_time_in_minutes']['calendar'], metrics_data['reply_time_in_minutes']['business'], ticket_data['satisfaction_rating']['score'], time_inserted))

        # Insert data into the 'user' table
        cursor.execute("""INSERT INTO [HelpCenter].[dbo].[user] (ticket_id, user_email, app_version, OS, mobile_provider, type_of_phone, city, time_inserted) VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
                       (ticket_id, user_data['email'], user_data['app_version'], user_data['OS'], user_data['mobile_provider'], user_data['type_of_phone'], user_data['city'], time_inserted))

        # Keep track of comment number on the current ticket
        comment_number = 1

        for comment in comments_data:
            # Insert data into the 'response' table
            cursor.execute("""INSERT INTO [HelpCenter].[dbo].[response] (response_id, zendesk_id, ticket_id, response_number, is_public, body, time_inserted) VALUES (?, ?, ?, ?, ?, ?, ?);""",
                           (str(ticket_id)+'_'+str(comment_number), comment['id'], ticket_id, comment_number, comment['public'], comment['body'], time_inserted))

            comment_number += 1     # Next comment

        ticket_id += 1      # Next ticket
        update_starting_ticket(ticket_id)   # Update the latest completed ticket in 'starting_ticket.txt'
        cnxn.commit()                       # Commit DB updates

        # Current ticket has been added to the DB
        print('Ticket ' + str(ticket_id) + ' complete')
        
    cnxn.close()    # Close connection
    #update_starting_ticket(ticket_id-1000)      # Next run of the script will start 1000 tickets back to check for updates
    print ("Database updated.")
    

    


#======================================================================================================================
# Run script

write_to_db()
