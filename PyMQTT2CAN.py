import argparse
import time
import uuid
import can
import paho.mqtt.client as mqtt
import ssl
import datetime

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    if arg_results.serverMode: 
        client.subscribe(topic + "/s/+", qos=0)
    else: 
        client.subscribe(topic + "/+", qos=0)
	
# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
#    print("Msg:" + msg.topic + " " + str(msg.payload))

    if arg_results.serverMode:
        arbID = int(msg.topic.split('/')[2])
    else:
        arbID = int(msg.topic.split('/')[1])
    flags = int.from_bytes(msg.payload[8:9], byteorder='little')
    isExt = False
    if ((flags & 1) == 1) : isExt = True

    msg = can.Message(arbitration_id = arbID, data = msg.payload[9:], is_extended_id = isExt)

    try:
        bus.send(msg)
#        print("Message sent on {}".format(bus.channel_info))
    except can.CanError:
        print("Message NOT sent - Something broke")

def on_disconnect(mqttc, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection. Reconnecting...")
        client.reconnect()
    else :
        print("Disconnected successfully")
	
client_id = str(uuid.uuid4())
print ("Start up!")
parser = argparse.ArgumentParser(description='SocketCAN To MQTT Conduit')
parser.add_argument('-u', action='store', dest='username', help='Specify MQTT Username')
parser.add_argument('-p', action='store', dest='password', help='Specify MQTT Password')
parser.add_argument('-b', action='store', dest='bustype', default='socketcan', help='Set usage of a different bus type (defaults to socketcan)')
parser.add_argument('-i', action='store', dest='channel', default='can0', help='Specify which socketcan interface to use')
parser.add_argument('-s', action='store', dest='speed', default=500000, type=int, help='Set speed of socketcan interface')
parser.add_argument('-t', action='store', dest='topic', default="can", help='Set MQTT topic to use')
parser.add_argument('-H', action='store', dest='mqtthost', default="api.savvycan.com", help='Set hostname of MQTT Broker')
parser.add_argument('-P', action='store', dest='mqttport', default=8883, type=int, help='Set port to connect to on MQTT Broker')
parser.add_argument('-S', action='store_const', const=True, dest='serverMode', default=False, help='Run as a server device (connected to physical bus)')

arg_results = parser.parse_args()

topic = arg_results.topic

bus = can.interface.Bus(channel=arg_results.channel, bustype=arg_results.bustype, bitrate=arg_results.speed)
	
client = mqtt.Client(client_id=client_id, clean_session=True)
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect

if arg_results.mqttport == 8883:
    client.tls_set(ca_certs=None, certfile=None, keyfile=None, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLS, ciphers=None)
if len(arg_results.username) > 0:
    client.username_pw_set(arg_results.username, arg_results.password)

client.connect(arg_results.mqtthost, arg_results.mqttport, 60)

print("Initialized. Tunneling traffic now.")
client.loop_start()

run = True
while run:
    for msg in bus:
        print(msg.arbitration_id)
        #msg.arbitration_id, msg.timestamp, and msg.data
        flags = 0
        if (msg.is_extended_id): flags += 1
        if (msg.is_remote_frame): flags += 2
        if (msg.is_fd): flags += 4
        if (msg.error_state_indicator): flags += 8
        microsStamp = int(msg.timestamp * 1000000).to_bytes(8, 'little')
        fullTopic = topic + "/" + str(msg.arbitration_id)
        client.publish(fullTopic, microsStamp + int(flags).to_bytes(1, 'little') + msg.data, qos=0)

