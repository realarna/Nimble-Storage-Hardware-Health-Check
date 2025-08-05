#!/usr/bin/env python

# Nimble Storage - NagiosXI Hardware Health API Check Script - v1.0
# Tristan Self
# The script utilises the Nimble Storage API to provide some basic hardware status monitoring. Although the Nimble Storage alerting system via Infosight is very good, we all know the warm fuzzy feeling of seeing a nice green service status in NagiosXI. The script only really needs to be scheduled to run once every 30 minutes or so. The script makes use of the Nimble Storage API, it is recommended to create a read-only account on the Nimble Storage array(s), this can be AD/LDAP or local.

import requests
import sys
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import argparse

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

#############################################################################################
# Argument Collection
#############################################################################################

# Parse the arguments passed from the command line.
parser = argparse.ArgumentParser()
parser.add_argument('-e','--endpointurl',help='Endpoint URL (e.g. https://arrayname.domain.com:5392)',required=True)
parser.add_argument('-u','--username',help='API Username',required=True)
parser.add_argument('-p','--password',help='API Password (in single quotes!)',required=True)
parser.add_argument('-d','--debugmode',help='Enable debug mode',action='store_true')

# Assign each arguments to the relevant variables.
arguments = vars(parser.parse_args())
strEndpointURL = arguments['endpointurl']
strAPIPassword = arguments['password']
strAPIUsername = arguments['username']
intDebugMode = arguments['debugmode']

#############################################################################################
# Initalise and Clean Variables
#############################################################################################

strCheckOutputStatusText = "OK"
strCheckOutputStatus = 0
strCheckOutputText = ""

if intDebugMode:
    pass
    print("DEBUG MODE")
    pass
    print("Endpoint URL:\033[0;32;40m",strEndpointURL,"\033[0m")
    pass
    pass

################################################################################################
# API Authentication
################################################################################################

# Get the authentication token.
try:
    objToken = requests.post(strEndpointURL+'/v1/tokens', data = json.dumps({'data' : {'password':strAPIPassword,'username':strAPIUsername}}),verify=False)
except requests.exceptions.RequestException as e:
    if intDebugMode:
        print(e)
    # Build and print to the screen the check result.
    print("CRITICAL - Failed to connect! Check EndpointURL, username and password.")
    strCheckOutputStatus = 2
    # Return the status to the calling program.
    sys.exit(strCheckOutputStatus)

# Get the JSON from the request response, then extract the session token for actually making a connection.
objTokenJSON = json.dumps(objToken.json(),indent=2)
objTokenDict = json.loads(objTokenJSON)
strAPIToken = objTokenDict['data']['session_token']
strAPITokenDict = {'X-Auth-Token':strAPIToken}

#################################################################################################
# Basic Array Information
#################################################################################################

# Get the Array's basic information
objArrayInfo = requests.get(strEndpointURL+'/v1/arrays/detail', headers = strAPITokenDict, verify=False)
objArrayInfoJSON = json.dumps(objArrayInfo.json(),indent=2)
objArrayInfoDict = json.loads(objArrayInfoJSON)
strArrayFullName = objArrayInfoDict.get('data')[0]['full_name']
strArraySerialNo = objArrayInfoDict['data'][0]['serial']
strArrayVersion = objArrayInfoDict['data'][0]['version']

#################################################################################################
# Controller, Fan, Temperature and PSU Status
#################################################################################################

# Get the listof all the shelves in the Nimble Storage array.
objArrayHardwareInfo = requests.get(strEndpointURL+'/v1/shelves', headers = strAPITokenDict, verify=False)
objArrayHardwareInfoJSON = json.dumps(objArrayHardwareInfo.json(),indent=2)
objArrayHardwareInfoDict = json.loads(objArrayHardwareInfoJSON)

# Get the total number of shelves in the array.
intstartRowShelves = objArrayHardwareInfoDict['startRow']
intendRowShelves = objArrayHardwareInfoDict['endRow'] # This variable lists the number of shelves there are in the array.

# Get the ID of each shelf in the array and then get the relevant metrics from the array or shelf.
for i in range(intstartRowShelves,intendRowShelves,1):
    if intDebugMode == 1:
        print("Shelf ID:\033[0;33;40m", objArrayHardwareInfoDict['data'][i]['id'],"\033[0m")

    # Build a object with the JSON response in it.
    objArrayHardwareDetailInfo = requests.get(strEndpointURL+'/v1/shelves/detail', headers = strAPITokenDict, verify=False)
    objArrayHardwareDetailInfoJSON = json.dumps(objArrayHardwareDetailInfo.json(),indent=2)
    objArrayHardwareDetailInfoDict = json.loads(objArrayHardwareDetailInfoJSON)

    if intDebugMode == 1:
        print("Model:\033[0;33;40m", objArrayHardwareDetailInfoDict['data'][i]['model_ext'],"\033[0m")
        print("Shelf Type:\033[0;33;40m", objArrayHardwareDetailInfoDict['data'][i]['ctrlrs'][0]['ctrlr_attrset_list'][0]['sw_type'],"\033[0m")
        print("PSU Status:\033[0;33;40m", objArrayHardwareDetailInfoDict['data'][i]['psu_overall_status'],"\033[0m")
        print("Fan Status:\033[0;33;40m", objArrayHardwareDetailInfoDict['data'][i]['fan_overall_status'],"\033[0m")
        print("Temperature Status:\033[0;33;40m", objArrayHardwareDetailInfoDict['data'][i]['temp_overall_status'],"\033[0m")
        print("Controller A Status:\033[0;33;40m",objArrayHardwareDetailInfoDict['data'][i]['ctrlrs'][0]['ctrlr_attrset_list'][0]['hw_state'],"\033[0m")
        print("Controller B Status:\033[0;33;40m",objArrayHardwareDetailInfoDict['data'][i]['ctrlrs'][1]['ctrlr_attrset_list'][0]['hw_state'],"\033[0m")
    pass

    # Check each of the various hardware component status, if it is in error state add this to the Output Status.
    if objArrayHardwareDetailInfoDict['data'][i]['psu_overall_status'] != "OK":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "PSU or Supply Fault!" + " "

    if objArrayHardwareDetailInfoDict['data'][i]['fan_overall_status'] != "OK":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "Fan Fault!" + " "

    if objArrayHardwareDetailInfoDict['data'][i]['temp_overall_status'] != "OK":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "Temperature Fault!" + " "

    if objArrayHardwareDetailInfoDict['data'][i]['ctrlrs'][0]['ctrlr_attrset_list'][0]['hw_state'] != "ready":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "Controller A Fault!" + " "

    if objArrayHardwareDetailInfoDict['data'][i]['ctrlrs'][1]['ctrlr_attrset_list'][0]['hw_state'] != "ready":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "Controller B Fault!" + " "



###################################################################################################
# Disk Status
###################################################################################################

# Get the list of all the shelves in the Nimble Storage array.
objArrayDiskDetailInfo = requests.get(strEndpointURL+'/v1/disks/detail', headers = strAPITokenDict, verify=False)
objArrayDiskDetailInfoJSON = json.dumps(objArrayDiskDetailInfo.json(),indent=2)
objArrayDiskDetailInfoDict = json.loads(objArrayDiskDetailInfoJSON)

# Get the total number of disks in all the array shelves, as one big list.
intstartRowDisks = objArrayDiskDetailInfoDict['startRow']
intendRowDisks = objArrayDiskDetailInfoDict['endRow'] # This variable lists the number of disks there are in the array.

for i in range(intstartRowDisks,intendRowDisks,1):
    if intDebugMode == 1:
        print("Disk ID:\033[0;33;40m", objArrayDiskDetailInfoDict['data'][i]['id'],"\033[0m")
        print("Disk Type:\033[0;33;40m",objArrayDiskDetailInfoDict['data'][i]['type'],"\033[0m")
        print("Disk State:\033[0;33;40m",objArrayDiskDetailInfoDict['data'][i]['state'],"\033[0m")
        print("Disk RAID State:\033[0;33;40m",objArrayDiskDetailInfoDict['data'][i]['raid_state'],"\033[0m")
    pass

    if objArrayDiskDetailInfoDict['data'][i]['state'] != "in use":
        strCheckOutputStatusText = "CRITICAL"
        strCheckOutputStatus = 2
        strCheckOutputText = strCheckOutputText + "Disk Fault!" + " "

####################################################################################################
# Result
####################################################################################################

if strCheckOutputStatus == 0:
    strCheckOutputText = "No Hardware Issues Present"

# Build and print to the screen the check result.
print("{} - {} ({} {} with {} shelves and {} disks)".format(strCheckOutputStatusText,strCheckOutputText,strArrayFullName,strArraySerialNo,intendRowShelves,intendRowDisks))

if intDebugMode == 1:
    print("Return Code: ",strCheckOutputStatus)

# Return the status to the calling program.
sys.exit(strCheckOutputStatus)
