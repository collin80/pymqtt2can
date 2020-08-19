# PyMQTT2CAN
(c) 2020 Collin Kidder

Released under MIT license

Python and MQTT based tunnel that allows a machine with a python-can compatible connection to share that CAN interface to one or more other machines on the internet at large. Those machines are then able to also send CAN traffic back to be placed onto the CAN interface. This has so far only been tested with SocketCAN devices. Technically support for being a client of this script is already in the CI builds of SavvyCAN so you can use this script to create a tunnel at the location of physical CAN access then use SavvyCAN to connect to that from anywhere in the world. If it breaks, you own all the pieces. You're welcome.

## Great, so how do I use it?

You'll need python 3 (yeah, not a python 2 purist), python-can and paho-mqtt

You will also need some MQTT broker/server to use for the traffic distribution. 

By default this code uses my MQTT broker at api.savvycan.com 

I'm willing to allow other people to use it too but you'll have to contact me and get a user name and password to use. The host has quite a high transfer cap but I reserve the right to yank access if you're a hog or do shady things.

The script has several possible parameters you can pass on the commandline to set things up. You will need at least some of them.

-b sets the interface type. Defaults to socketcan. See python-can docs to find what else you could pass here. Nothing but socketcan is tested but it ought to work anyway.

-i sets the channel name to connect to. For socketcan this will be something like can0 or vcan0. For other interface types you will need to consult the documentation for that interface

-s sets the CAN speed. For socketcan this is probably not super useful. For other interfaces it might be essential.

-u sets the MQTT user name

-p sets the MQTT password for that user name

-t Sets the topic name for MQTT. MQTT requires some sort of topic name, this defaults to "can" if you don't set it. Explicitly setting this parameter could be useful if you want to have multiple different CAN buses with one username/password combo.

-H sets the hostname to connect to for MQTT. Defaults to api.savvycan.com which runs on my server. This machine has a very reliable connection to the internet in a cohosting facility. So, reliability should be very good and transfer speeds very snappy. But, you're not paying me so you get what you pay for.

-P sets the TCP/IP port to use. Defaults to 8883 which is a secure connection. 1883 would be sans encryption. api.savvycan.com requires encryption so you don't have a choice if you're using my server. If you run your own server you can go ahead and do whatever you want.

-S sets server mode. This is important. The machine with the connection to the CAN bus must pass -S. Everyone else must not. The general idea here is that the server listens on a slightly different topic than the clients. This way the server can listen
for clients to signal that they'd like to send a message and the clients can listen for traffic that the server has captured. 

## Overview of connections

Every device is doing the same thing - connecting a CAN interface to MQTT. The server does this with a theoretically "real" CAN interface. But, you can use virtual sockets too on linux. The "client" devices then also connect a CAN interface to MQTT but they are almost certainly connecting a virtual interface to MQTT. This way a client can then use any program that could have used that virtual connection as if they were really connected to the physical hardware that the "server" side is connected to. 

As an example, suppose you have "can0" which is a CAN device on a linux machine. Suppose can0 is connected to the OBDII port on a car. On that machine you could then run:

python3 PyMQTT2CAN.py -u somebody -p realsecurepassword -i can0 -S

This will start sending any traffic on can0 to mqtt on the topic "can"

Now, suppose you have a second machine 3000 miles away (or km if you prefer). This machine is also running linux. On this machine you'd want to create a vcan interface then tunnel the traffic to it:

sudo modprobe vcan

sudo ip link add dev vcan0 type vcan

sudo ip link set up vcan0

python3 PyMQTT2CAN.py -u somebody -p realsecurepassword -i vcan0

Now, if you run socketcan commands with vcan0 as the target you will see traffic from the first machine and be able to also send traffic from the second machine to the first to be forwarded along the CAN bus

"candump vcan0" will show traffic flowing on the OBDII port of the car on the second machine

"cansend vcan0 7E0#013EAAAAAAAAAAAA" will send a tester present command to the OBDII port on the car



