from __future__ import print_function # Needed if you want to have console output using Flask
import requests
import sys
import json
import os
import time
from flask import Flask, request

#Disable the warnings caused by unverified SSL certificates
requests.packages.urllib3.disable_warnings()

#Webex Bot Token to access their API - Guest Access Bot
webex_token = ''  

#ISE IP Address
ISE_IP_Address = ''

#Sponsor API Base64 Username:Password
sponsor_base64 = ''

#MessageBird Access Key to access their API
messageBirdKey = ''

#MessageBird SMS originating number
smsOrigin = ''

#MessageBird SMS Country Code
country_code = "+"




def getWebexMessage_fromID(messageId):
    print("getWebexMessage_fromID(" + messageId + ")")
    url = "https://api.ciscospark.com/v1/messages/" + messageId

    print(url)
    headers = {
        'Authorization': "Bearer " + webex_token,
        'Content-Type': "application/json",
        'Accept': "*/*"
        }

    response = requests.request("GET", url, headers=headers)
    response_text = response.text
    response_json = json.loads(response_text)
    
    message = response_json["text"]

    return message


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
    print("sendWebexMessage(" + recipient + ", " + message + ")")
    url = "https://api.ciscospark.com/v1/messages"

    payload = "{\n  \"toPersonEmail\": \"" + recipient + "\",\n  \"text\": \"" + message + "\"\n}"
    headers = {
        'Authorization': "Bearer " + webex_token,
        'Content-Type': "application/json",
        'Accept': "*/*"
        }

    response = requests.request("POST", url, data=payload, headers=headers)


def verifyPendingUser(username):
    print("verifyPendingUser(" + username + ")")

    returnGuestId = ""

    response_allGuest = requests.request("GET", url_allGuest, headers=headers_allGuest, verify=False)
    allGuest_json = json.loads(response_allGuest.text)
    
    AllGuest_info = allGuest_json["SearchResult"]["resources"]

    print(username)

    for guest in AllGuest_info:
        guestID =  guest["id"]
        url_specificGuest_X = ""
        url_specificGuest_X = url_specificGuest + guestID

        response_specificGuest = requests.request("GET", url_specificGuest_X, headers=headers_specificGuest, verify=False)
        specificGuest_json = json.loads(response_specificGuest.text)
        
        specificGuest_id = specificGuest_json["GuestUser"]["id"]
        specificGuest_username = specificGuest_json["GuestUser"]["guestInfo"]["userName"]
        specificGuest_status = specificGuest_json["GuestUser"]["status"]
        print(specificGuest_username + " - " + username + " " + specificGuest_status)

        if specificGuest_status == "PENDING_APPROVAL" or specificGuest_status == "SUSPENDED":
            if specificGuest_username.casefold() == username.casefold():
                returnGuestId = specificGuest_id
                break;

    return returnGuestId


def authorizeGuest(guestId):
    print("authorizeGuest(" + guestId + ")")

    url_specificGuest_X = ""
    url_specificGuest_X = url_specificGuest + guestId

    response_specificGuest = requests.request("GET", url_specificGuest_X, headers=headers_specificGuest, verify=False)
    specificGuest_json = json.loads(response_specificGuest.text)
    
    specificGuest_password = specificGuest_json["GuestUser"]["guestInfo"]["password"]
    specificGuest_username = specificGuest_json["GuestUser"]["guestInfo"]["userName"]
    specificGuest_phone = specificGuest_json["GuestUser"]["guestInfo"]["phoneNumber"]
    specificGuest_sponsor = specificGuest_json["GuestUser"]["personBeingVisited"]
    specificGuest_country = specificGuest_json["GuestUser"]["customFields"]["ui_country_code_text_label"]

    url = "https://" + ISE_IP_Address + ":9060/ers/config/guestuser/reinstate/" + guestId

    payload = ""
    headers = {
        'Content-Type': "application/json",
        'Accept': "application/json",
        'Authorization': "Basic " + sponsor_base64
        }

    try:
        print("Sending: " + url)
        requests.put(url, data=payload, headers=headers, verify=False, timeout=1)
    except:
        print("Sent!")

    sendWebexMessage(specificGuest_sponsor, "Wi-Fi access for (" + specificGuest_username + ") is now granted")


    print("notifyGuest(" + guestId + ")")

    print("Sending SMS to " + specificGuest_username + " at " + specificGuest_phone)

    headers_sms = {
        'Authorization': 'AccessKey ' + messageBirdKey
    }

    #Singapore only
    specificGuest_phone = country_code + specificGuest_country + specificGuest_phone

    data_sms = '{"recipients":"' + specificGuest_phone + '", "originator":"' + smsOrigin + '", "body":"Sponsored Guest Access Password = ' + specificGuest_password + '"}'

    print("Sending: " + data_sms)

    response_sms = requests.post('https://rest.messagebird.com/messages', headers=headers_sms, data=data_sms)
    print("MessageBird Gateway Response Code: " + response_sms.text)
    

app = Flask(__name__)

@app.route("/",methods=['POST'])    # all request for localhost:5000/  will reach this method
def webhook():
    guestId = ""

    # Get the json data
    json = request.json

    webexMessageID = json["data"]["id"]
   
    #Retrieve guest's username from Webex Teams based on messageID - Sponsor should only type the guest's username into the chat
    username = getWebexMessage_fromID(webexMessageID)

    #Retrieve guest's ID from ISE Portal - Must be either in "PENDING_APPROVAL" or "SUSPENDED" state
    guestId = verifyPendingUser(username)

    if guestId != "":
        #Authorize Guest Access using ISE API
        #Inform Guest via SMS on the wifi apssword
        
        authorizeGuest(guestId)
    

    return ("Success")


   

if __name__ == '__main__':
    app.run(host='localhost', use_reloader=True, debug=True)
