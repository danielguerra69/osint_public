import argparse
import re
import sqlite3
import requests
import time
import csv

full_contact_api_key = "YOURKEY"

ap = argparse.ArgumentParser()
ap.add_argument("-d","--database",    required=True,help="Path to the SQLite database you wish to analyze.")
args = vars(ap.parse_args())

match_list  = []
regex_match = re.compile('[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')

# connect to the database
db     = sqlite3.connect(args['database'])
cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

tables = cursor.fetchall()

for table in tables:
    
    print "[*] Scanning table...%s" % table
    
    # now do a broad select for all records
    cursor.execute("SELECT * FROM %s" % table[0])

    rows = cursor.fetchall()
    
    for row in rows:
        
        for column in row:
            
            try:
                matches = regex_match.findall(column)
            except:
                continue
            
            for match in matches:
                
                if match not in match_list:
                    
                    match_list.append(match)
cursor.close()
db.close()
            
print "[*] Discovered %d matches." % len(match_list)

# setup for csv writing
fd         = open("%s-social-media.csv" % args['database'],"wb")
fieldnames = ["Email Address","Network","User ID","Username","Profile URL"]
writer     = csv.DictWriter(fd,fieldnames=fieldnames)
writer.writeheader()

while match_list:
    
    # build the request up for Full Contact
    headers = {}
    headers['X-FullContact-APIKey'] = full_contact_api_key
    
    match   = match_list.pop()
    
    print "[*] Trying %s" % match
    url = "https://api.fullcontact.com/v2/person.json?email=%s" % match
    
    response = requests.get(url,headers=headers)
    
    time.sleep(2)
    
    if response.status_code == 200:
        
        contact_object = response.json()       
        
        if contact_object.has_key('socialProfiles'):
            
            for profile in contact_object['socialProfiles']:
                
                record = {}
                record['Email Address'] = match
                record['Network']       = profile.get("type","N/A")
                record['User ID']       = profile.get("id","N/A")
                record['Username']      = profile.get("username","N/A")
                record['Profile URL']   = profile.get("url","N/A")
                
                writer.writerow(record)
                
                # print some output to the screen
                print "Network: %s"  % profile.get("type","N/A")
                print "Username: %s" % profile.get("username","N/A")
                print "URL: %s"      % profile.get("url","N/A")
                print "ID: %s"       % profile.get("id","N/A")
                print 
                
    
    elif response.status_code == 202:
        
        print "[*] Sleeping for a bit."
    
        # push this item back onto the list and sleep
        match_list.append(match)
        time.sleep(30)        

fd.close()