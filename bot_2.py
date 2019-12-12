import time
import requests
import json
requests.packages.urllib3.disable_warnings()

loop = True
#counter = 1
#wait_time = 10 #Send notifications on every 10 seconds 

totalPendingGuest = []

#Webex Bot Token to access their API - Guest Access Bot
webex_token = ''  

#ISE IP Address
ISE_IP_Address = ''

#Sponsor API Base64 Username:Password
sponsor_base64 = ''

#Headers - Get ALl Guest
url_allGuest = "https://" + ISE_IP_Address + ":9060/ers/config/guestuser"
headers_allGuest = {
    'Content-Type': "application/json",
    'Accept': "application/json",
    'Authorization': "Basic " + sponsor_base64
   }


#Headers - Get Specific Guest
url_specificGuest = "https://" + ISE_IP_Address + ":9060/ers/config/guestuser/"
headers_specificGuest = {
    'Content-Type': "application/json",
    'Accept': "application/json",
    'Authorization': "Basic " + sponsor_base64
    }


def sendWebexMessage(recipient, message):
	url = "https://api.ciscospark.com/v1/messages"

	payload = "{\n  \"toPersonEmail\": \"" + recipient + "\",\n  \"text\": \"" + message + "\"\n}"
	headers = {
	    'Authorization': "Bearer " + webex_token,
	    'Content-Type': "application/json",
	    'Accept': "*/*"
	 }

	response = requests.request("POST", url, data=payload, headers=headers)


while loop:
	
	response_allGuest = requests.request("GET", url_allGuest, headers=headers_allGuest, verify=False)
	allGuest_json = json.loads(response_allGuest.text)
	
	AllGuest_info = allGuest_json["SearchResult"]["resources"]

	try:
		for guest in AllGuest_info:
			guestID =  guest["id"]
			url_specificGuest_X = ""
			url_specificGuest_X = url_specificGuest + guestID

			response_specificGuest = requests.request("GET", url_specificGuest_X, headers=headers_specificGuest, verify=False)
			specificGuest_json = json.loads(response_specificGuest.text)
			
			specificGuest_id = specificGuest_json["GuestUser"]["id"]
			specificGuest_name = specificGuest_json["GuestUser"]["guestInfo"]["userName"]
			specificGuest_status = specificGuest_json["GuestUser"]["status"]
			specificGuest_sponsor = specificGuest_json["GuestUser"]["personBeingVisited"]


			if specificGuest_status == "PENDING_APPROVAL":

				pending_guest = [specificGuest_id, specificGuest_name, specificGuest_status, specificGuest_sponsor]

				#Check if retrieved guest is inside current pending list - matching ID
				check = False


				for c in totalPendingGuest:
					if c[0] == specificGuest_id:
						check = True

				#Add the retrieved guest into the list if it is a new guest (not in the list)
				if check == False:
					
					totalPendingGuest.append(pending_guest)
					print("calling message api")
					sendWebexMessage(pending_guest[3], "You have a guest (" + specificGuest_name + ") awaiting your approval for Wi-Fi access. Please type the username (" + specificGuest_name + ") to approve Wi-Fi access")


		time.sleep(1)
	except:
		print ("Error")




  