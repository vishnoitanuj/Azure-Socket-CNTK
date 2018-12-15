import time 
from time import sleep 
from sinchsms import SinchSMS 

number = '918826022510'
app_key = 'e31dabc6-aa8d-46bb-aab8-bfb91b58d13c'
app_secret = 'J7js1xm+m0665hYgrzW6+w=='

# enter the message to be sent 
message = 'Alert Triggered'

client = SinchSMS(app_key, app_secret) 
print("Sending '%s' to %s" % (message, number)) 

response = client.send_message(number, message) 
message_id = response['messageId'] 
response = client.check_status(message_id) 

# keep trying unless the status retured is Successful 
while response['status'] != 'Successful': 
    print(response['status']) 
    time.sleep(1) 
    response = client.check_status(message_id) 

print(response['status'])