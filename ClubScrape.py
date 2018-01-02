import cookielib
import time
import urllib
import urllib2
import re
import units
import ast
import csv
import os

from BeautifulSoup import BeautifulSoup

from stravalib.client import Client

global TIME_BT_REQUESTS
TIME_BT_REQUESTS = 2

# Uses the strava API to find all activities by members of a club on strava,
# records all gps data from those activities and plots them ontop of road data
# from Open Street Maps

# Access the web address of activities
def fetch_url(opener, url):
  try:
    print 'fetching %s' % url
    response = opener.open(url)
    time.sleep(TIME_BT_REQUESTS)
  except Exception, e:
    print '%s - %s' % (e, url)
    time.sleep(TIME_BT_REQUESTS)
    return None

  if response.getcode() != 200:
    raise Exception('%s: %s - %s' % \
        (url, response.getcode(), response.msg))

  response = response.read()
  return response

# authentication code by: https://github.com/loisaidasam/stravalib
def log_in():
  print "Logging in..."
  cj = cookielib.CookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

  f = opener.open('https://www.strava.com/login')
  soup = BeautifulSoup(f.read())

  time.sleep(TIME_BT_REQUESTS)

  utf8 = soup.findAll('input', {'name': 'utf8'})[0].get('value').encode('utf-8')
  token = soup.findAll('input', {'name': 'authenticity_token'})[0].get('value')

  values = {
    'utf8': utf8,
    'authenticity_token': token,
    'email': 'andrew.cullen@monash.edu',
    'password': 'm0nstermad',
  }

  data = urllib.urlencode(values)
  url = 'https://www.strava.com/session'
  response = opener.open(url, data)
  soup = BeautifulSoup(response.read())

  time.sleep(TIME_BT_REQUESTS)
  return opener

# Takes html, parses and strips everything except GPS track data
def parse_and_write(activity_id):
  url = 'https://www.strava.com/activities/%s/streams' % activity_id
  response = fetch_url(opener, url)
  response_strp = response.strip()
  results_dict = dict((k.strip('\"').strip('{').strip('\"'), ast.literal_eval(v.strip().strip('}').replace('false','0').replace('true','1'))) for k,v in (item.split(':') for item in response_strp.split(',\"')))

  with open('filetest.csv', 'ab') as f:
    writer = csv.writer(f)
    writer.writerows(results_dict['latlng'])

  return results_dict

# Takes html, parses and strips everything except GPS track data
def parse_and_write_club(activity_id, club):
  url = 'https://www.strava.com/activities/%s/streams' % activity_id
  response = fetch_url(opener, url)
  response_strp = response.strip()
  results_dict = dict((k.strip('\"').strip('{').strip('\"'), ast.literal_eval(v.strip().strip('}').replace('false','0').replace('true','1').replace('null','0'))) for k,v in (item.split(':') for item in response_strp.split(',\"')))

  #with open('filetest.csv', 'ab') as f:
  with open(club + '.csv', 'ab') as f:
    writer = csv.writer(f)
    writer.writerows(results_dict['latlng'])

  return results_dict

# Returns the last 200 activities from club members
def club_scraper(club_number):
    club_activities = client.get_club_activities(club_number)
    activities_list = []
    for activity in club_activities:
        counter = 0
        # Opens CSV to store gps track data
        with open(club_number + '_activities.csv', 'rt') as f:
            reader = csv.reader(f, delimiter=',')
            for row in reader:
                try:
                    if abs(int(row[0]) - activity.id) < 1:
                        counter = 1
                except:
                    counter = 0
                #for field in row:
                    #if field == str(activity.id):
                        #counter = 1
        if counter == 0:
            try:
                bob = parse_and_write_club(activity.id, club_number)
                activities_list.append([activity.id, str(activity.type).strip('\'')])
            except:
                print 'bob'        
            print club_number, activity.id


    print club_number, ' length of activities list is ', len(activities_list)

    if len(activities_list) > 0:
        #os.system("heatmap.py --csv=filetest.csv -e '-38.5,144.2,-37.7,145.8' -o mcat_new.png --height 1200 --osm")
        
        #with open('files_activities.csv', 'ab') as f:
        with open(club_number + '_activities.csv', 'ab') as f:
            writer = csv.writer(f)
            writer.writerows(activities_list)
        # Writes the gps track data ontop of open streetmaps data
        os.system("heatmap.py --csv=" + club_number + ".csv --ignore_csv_header -e '-38.5,144.2,-37.5,145.8' -o " + club_number + ".png --height 1200 --osm")
    return activities_list
  
  
  


if __name__ == "__main__":
    # Temporary activity test to force log in
    activity_id = '832303006'
    url = 'https://www.strava.com/activities/%s/streams' % activity_id
    opener = log_in()
    LOGIN = file("access_token").read().strip()
    client = Client()
    client.access_token = LOGIN

    club_list = ['32462', '236463']

    for club in club_list:
        club_scraper(club) 

