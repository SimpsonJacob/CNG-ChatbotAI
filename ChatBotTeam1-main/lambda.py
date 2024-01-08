import json
import boto3
import re

s3 = boto3.client('s3')
bucket_name = '123u09124u9014u0912bucket'
file_name = 'file.json'
file_name2 = 'airports.json'
file_name3 = 'crew.json'
file_name4 = 'airport.json'
file_name5 = 'plane.json'

def update_start_time_in_s3_crew(event, fname, lname, new_start_time):
    response = s3.get_object(Bucket=bucket_name, Key=file_name3)
    content = response['Body'].read().decode('utf-8')
    crew_segments = json.loads(content)

    found_match = False

    for crew_member in crew_segments["crewSegment"]:
        if crew_member["fname"] == fname and crew_member["lname"] == lname:
            crew_member["actualStartTime"] = new_start_time
            found_match = True

    if found_match:
        updated_content = json.dumps(crew_segments, indent=4)
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name3,
            Body=updated_content.encode('utf-8')
        )

    return found_match

def update_start_time_in_s3_aircraft(event, tailnumber, new_start_time):
    response = s3.get_object(Bucket=bucket_name, Key=file_name)
    content = response['Body'].read().decode('utf-8')
    air_segments = json.loads(content)

    found_match = False

    for segment in air_segments["airSegment"]:
        if segment["tailNumber"] == tailnumber:
            segment["actualArrival"] = new_start_time
            found_match = True

    if found_match:
        updated_content = json.dumps(air_segments, indent=4)
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=updated_content.encode('utf-8')
        )

    return found_match

# Define valid options for flight booking
flight_destinations = ['New York', 'Los Angeles', 'Chicago'] #add whatever destinations you would li

def validate_flight_booking(slots):
    # Validate FlightDestination
    if not slots['Destination']:
        return {
            'isValid': False,
            'invalidSlot': 'Destination',
            'message': 'Please select a flight destination from {}.'.format(", ".join(flight_destinations))
        }
    
    if slots['Destination']['value']['originalValue'] not in flight_destinations:
        return {
            'isValid': False,
            'invalidSlot': 'Destination',
            'message': 'Invalid flight destination. Please select from {}.'.format(", ".join(flight_destinations))
        }

    # Valid flight booking
    return {'isValid': True}


#---------------------------------- intent functions ---------------------------------------------
def email(event, context):
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    # Create an SNS client
    client = boto3.client("sns")

    # Message to be sent
    fname = slots['firstName']['value']['originalValue'].lower()
    lname = slots['lastName']['value']['originalValue'].lower()
    message = slots['emailMessage']['value']['originalValue'].lower()

    # Topic ARN to send the message to
    topic_arn = 'arn:aws:sns:us-east-1:586717510457:new-sns'  # Replace with your SNS topic ARN

    # Publish the message
    response = client.publish(
        TopicArn=topic_arn,
        Message= fname + " " + lname + " sent you this message: " + message
    )

    response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent,
                    "slots": slots,
                    "state": "Fulfilled"
                },
                "message": [
                    {
                        "contentType": "PlainText",
                        "content": "Your email has been sent."
                    }
                ]
            }
        }

    return response

def message(event, context):
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    # Create an SNS client
    client = boto3.client("sns")

    # Message to be sent
    fname = slots['FirstName']['value']['originalValue'].lower()
    lname = slots['LastName']['value']['originalValue'].lower()
    message = slots['mMessage']['value']['originalValue'].lower()

    # Topic ARN to send the message to
    topic_arn = 'arn:aws:sns:us-east-1:586717510457:new-message'  # Replace with your SNS topic ARN

    # Publish the message
    response = client.publish(
        TopicArn=topic_arn,
        Message=fname + " " + lname + " sent you this message: " + message
    )

    response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent,
                    "slots": slots,
                    "state": "Fulfilled"
                },
                "message": [
                    {
                        "contentType": "PlainText",
                        "content": "Your message has been sent."
                    }
                ]
            }
        }

    return response
    
def shop(event, context):
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']

    flight_booking_result = validate_flight_booking(slots)

    if event['invocationSource'] == 'DialogCodeHook':
        if not flight_booking_result['isValid']:
            response = {
                "sessionState": {
                    "dialogAction": {
                        "slotToElicit": flight_booking_result['invalidSlot'],
                        "type": "ElicitSlot"
                    },
                    "intent": {
                        "name": intent,
                        "slots": slots
                    },
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": flight_booking_result['message']
                    }
                ]
            }
        else:
            response = {
                "sessionState": {
                    "dialogAction": {
                        "type": "Delegate"
                    },
                    "intent": {
                        'name': intent,
                        'slots': slots
                    }
                }
            }
    elif event['invocationSource'] == 'FulfillmentCodeHook':
        response = {
            "sessionState": {
                "dialogAction": {
                    "type": "Close"
                },
                "intent": {
                    "name": intent,
                    "slots": slots,
                    "state": "Fulfilled"
                },
                "message": [
                    {
                        "contentType": "PlainText",
                        "content": "Your flight has been booked."
                    }
                ]
            }
        }

    return response
    
def aircraft_segment(event, context):
    
    S3_BUCKET_NAME = '123u09124u9014u0912bucket'
    S3_FILE_NAME = 'file.json'
    
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']

    tailnumber = slots['Tailnumber']['value']['originalValue']
    og_start_date = slots['OriginalStartDate']['value']['originalValue']
    og_start_time = slots['OriginalStartTime']['value']['originalValue']
    new_start_date = slots['NewStartDate']['value']['originalValue']
    new_start_time = slots['NewStartTime']['value']['originalValue']

    expected_time_value = og_start_date + "T" + og_start_time + "-05:00[America/Chicago]"
    new_time_value = new_start_date + "T" + new_start_time + "-05:00[America/Chicago]"

    print(tailnumber)
    print(og_start_date)
    print(og_start_time)
    print(new_start_date)
    print(new_start_time)
    print(expected_time_value)
    print(new_time_value)

    found_match = update_start_time_in_s3_aircraft(event, tailnumber, new_time_value)
    

    if found_match:
        response_message = f"Start time updated for {tailnumber}."
    else:
        response_message = "No match found for the provided tailnumber."

    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "MoveAircraftSegment",
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",  # Use "Close" if you want to end the conversation
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "MoveAircraftSegment",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message
            }
        ]
    }
    
def navigate(event, context):
    print(event)
    
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    hook = slots['hooktype']['value']['originalValue']

    print(slots)
    print(bot)
    print(intent)
    print(hook)
        
    if hook == 'home':
        response_message = 'https://charterandgo.com/home'
    elif hook == 'login':
        response_message = 'https://www.cag-ai.com/login'

    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "Navigate", 
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,     
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",  # Use "Close" if you want to end the conversation
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "Navigate",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message
            }
        ]
    }
    
def search_airport(event, context):
    print(event)
    
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    country = slots['Country']['value']['originalValue']
    state = slots['State']['value']['originalValue']
    city = slots['City']['value']['originalValue']
    zipCode = slots['ZipCode']['value']['originalValue']

    print(slots)
    print(bot)
    print(intent)
    print(country)
    print(state)
    print(city)
    print(zipCode)
    
    response = s3.get_object(Bucket=bucket_name, Key=file_name2)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    
    airport_data = json_data["airports"]
    matching_airports = []
    
    for airport in airport_data:
        similarity_threshold = 4
        similarity_score = 0
        
        if airport["country"] == country:
            similarity_score += 1
        if airport["state"] == state:
            similarity_score += 1
        if airport["city"] == city:
            similarity_score += 1
        if airport["zip"] == zipCode:
            similarity_score += 1
        
        if similarity_score >= similarity_threshold:
            matching_airports.append(airport)
    
    response_message = "\n"
    for airport in matching_airports:
        response_message += f"Name: {airport['name']}, {airport['city']}, {airport['state']}, {airport['zip']}, {airport['country']}\n"
    print(response_message)
    
    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "SearchAirport", 
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,     
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",  # Use "Close" if you want to end the conversation
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "SearchAirport",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message  # Use the response_message generated from the relevant airports
            }
        ]
    }
    
def update_start_time_in_s3(event, fname, lname, new_start_time):
    response = s3.get_object(Bucket=S3_BUCKET_NAME, Key=S3_FILE_NAME)
    content = response['Body'].read().decode('utf-8')
    crew_segments = json.loads(content)

    found_match = False

    for crew_member in crew_segments["crewSegment"]:
        if crew_member["fname"] == fname and crew_member["lname"] == lname:
            crew_member["actualStartTime"] = new_start_time
            found_match = True

    if found_match:
        updated_content = json.dumps(crew_segments, indent=4)
        s3.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=S3_FILE_NAME,
            Body=updated_content.encode('utf-8')
        )

    return found_match

def crew_segment(event, context):
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']

    first_name = slots['FirstName']['value']['originalValue']
    last_name = slots['LastName']['value']['originalValue']
    og_start_date = slots['OriginalStartDate']['value']['originalValue']
    new_start_date = slots['NewStartDate']['value']['originalValue']
    og_start_time = slots['OriginalStartTime']['value']['originalValue']
    new_start_time = slots['NewStartTime']['value']['originalValue']
    segment_type = slots['SegmentType']['value']['originalValue']

    expected_time_value = og_start_date + "T" + og_start_time + "-04:00"
    new_time_value = new_start_date + "T" + new_start_time + "-04:00"

    found_match = update_start_time_in_s3_crew(event, first_name, last_name, new_time_value)

    if found_match:
        response_message = f"{first_name} {last_name}'s start time has been updated to {new_time_value}"
    else:
        response_message = "No match found for the provided first name and last name."

    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "MoveCrewSegment",
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "MoveCrewSegment",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message
            }
        ]
    }
    
def airport_location(event, context):
    # TODO implement
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    FAA_code = slots['FAACode']['value']['originalValue']

    print(slots)
    print(bot)
    print(intent)
    print(FAA_code)
    
    response = s3.get_object(Bucket=bucket_name, Key=file_name4)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    
    print(json_data)
    
    for airport in json_data ['airport']:
        if airport ['faa_code'] == FAA_code:
            response_message = f"Airport Name: {airport['name']}\nCity: {airport['city']}\nState: {airport['state']}\nCountry: {airport['country']}" 
            break
    print (airport)
    
    
    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "AirportLocation", 
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,     
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",  # Use "Close" if you want to end the conversation
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "AirportLocation",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message
            }
        ]
    }

def find_plane(event, context):
    print(event)
    
    bot = event['bot']['name']
    slots = event['sessionState']['intent']['slots']
    intent = event['sessionState']['intent']['name']
    
    hook = slots['Tailnumber']['value']['originalValue']

    print(slots)
    print(bot)
    print(intent)
    print(hook)
    
    response = s3.get_object(Bucket=bucket_name, Key=file_name5)
    content = response['Body'].read().decode('utf-8')
    json_data = json.loads(content)
    
    print(json_data)
    
    arrival_timestamp = json_data["arrival"]
    departure_timestamp = json_data["departure"]
    tailnumber = json_data["tailNumber"]
    origin = json_data["origin"]
    destination = json_data["destination"]
    
    print("Arrival Timestamp:", arrival_timestamp)
    print("Departure Timestamp:", departure_timestamp)
    print(tailnumber)
    
    if tailnumber == hook:
        response_message = f"The flight arrived from {origin} Airport at {arrival_timestamp} and departed for {destination} Airport at {departure_timestamp}."
    else:
        response_message = "No matching flight found for the provided tail number."


    return {
        "sessionState": {
            "activeContexts": [
                {
                    "name": "FindPlane", 
                    "contextAttributes": {
                        "key": "value"
                    },
                    "timeToLive": {
                        "timeToLiveInSeconds": 20,     
                        "turnsToLive": 20
                    }
                }
            ],
            "dialogAction": {
                "slotElicitationStyle": "Default",
                "slotToElicit": "string",
                "type": "Close",  # Use "Close" if you want to end the conversation
            },
            "intent": {
                "confirmationState": "Confirmed",
                "name": "FindPlane",
                "state": "Fulfilled"
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": response_message
            }
        ]
    }

def help_intent(sentence):
    test_regex = re.compile(r'(?=.*test)([^\s]+)')
    
    logon_regex = re.compile(r'(?=.*logon)|(?=.*login)')
    teams_regex = re.compile(r'(?=.*teams).*')
    fleet_regex = re.compile(r'(?=.*fleet).*')
    flight_deck_regex = re.compile(r'(?=.*flight deck).*')
    specific_flight_deck_regex = re.compile(r'(?=crew scheduling)([^\s]+)|(?=certifications)([^\s]+)|(?=hours)([^\s]+)')
    cost_model_regex = re.compile(r'(?=.*cost model).*')
    accurpricer_regex = re.compile(r'(?=.*accurpricer).*')
    tracker_regex = re.compile(r'(?=.*tracker).*')
    shopping_regex = re.compile(r'(?=.*shopping)([^\s]+)|(?=.*shop)([^\s]+)')
    specific_shopping_regex = re.compile(r'(?=page)([^\s]+)|(?=fleet view)([^\s]+)|(?=client list)([^\s]+)')
    dashboard_regex = re.compile(r'(?=.*dashboard)([^\s]+)')
    airports_regex = re.compile(r'(?=.*airports).*')
    client_list_regex = re.compile(r'(?=.*client list).*')
    security_regex = re.compile(r'(?=.*security).*')
    operation_regex = re.compile(r'(?=.*operations).*')
    sentence = sentence.lower()
    return_message = "default return message"


    if logon_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with logon"
    if teams_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with teams"

    if flight_deck_regex.match(sentence) and return_message == "default return message":
        match = re.search(specific_flight_deck_regex, sentence)
        if match is not None:
            return_message = "Helping with specific flight deck request " + match.group(0)
        else:
            return_message = "Helping with basic flight deck request"

    if cost_model_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with cost model"

    if accurpricer_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with accurpricer"

    if tracker_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with tracker"

    if shopping_regex.match(sentence) and return_message == "default return message":
        match = re.search(specific_shopping_regex, sentence)
        # Compound requests are currently not working
        if match is not None:
            return_message = ("Helping with specific shop request " + match.group(1))
        else:
            return_message = "Helping with basic shop request"

    if dashboard_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with dashboard"

    if airports_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with airports"

    if client_list_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with client list"

    if security_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with security"

    if operation_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with flight tracking operations"

    if fleet_regex.match(sentence) and return_message == "default return message":
        return_message = "Helping with fleet"

    return{
    "sessionState": {
        "dialogAction": {
            "type": "Close"
    },
    "intent": {
      "confirmationState": "Confirmed",
      "name": "Help",
      "state": "Fulfilled",
      
    },
},
    "messages": [
        {
        "contentType": "PlainText",
        "content": return_message,
        }
    ]
}

#---------------------------------- intent functions ---------------------------------------------

def lambda_handler(event, context):
    bot = event['bot']['name']
    intent = event['sessionState']['intent']['name']
    user_message = event['inputTranscript']  # <-- collects what user enter on lex bot

    if intent == 'SendEmail':
        return email(event, context)
    if intent == 'SendMessage':
        return message(event, context)
    if intent == 'Shop':
        return shop(event, context)
    if intent == 'MoveAircraftSegment':
        return aircraft_segment(event, context)
    if intent == 'Navigate':
        return navigate(event, context)
    if intent == 'SearchAirport':
        return search_airport(event, context)
    if intent == 'MoveCrewSegment':
        return crew_segment(event, context)
    if intent == 'AirportLocation':
        return airport_location(event, context)
    if intent == 'FindPlane':
        return find_plane(event,context)
    if intent == 'Help':
        return help_intent(user_message)
