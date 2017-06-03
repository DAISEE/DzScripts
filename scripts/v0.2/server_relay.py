import RPi.GPIO as GPIO
import socket
import yaml


def read_data(relay):
    # relay
    # format: list
    # example: [0, 1]

    relayState = {}
    for channel in relay:
        print(channel)
        if GPIO.input(Relay_channel[channel]) == 0:
            relayState[channel] = False
        else:
            relayState[channel] = True
    print(relayState)
    return str(relayState)


def switch_energy(relay):

    # format: dict
    # example: {0: False, 1: True}
    try:
        for channel, state in relay.items():
            print(channel, state)
            GPIO.output(Relay_channel[channel], state)
        success = True
    except Exception as e:
        print('ERROR switchEnergy() : ' + str(e))
        success = False
    return success

# connection to the relay
Relay_channel = [17, 18]
GPIO.setmode(GPIO.BCM)
GPIO.setup(Relay_channel, GPIO.OUT, initial=GPIO.LOW)

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind(('', 15555))


while True:

    socket.listen(5)
    client, address = socket.accept()
    print("{} connected".format(address))

    try:
        response = client.recv(255)
        if response != "":
            print('=====================')
            data = response.decode()
            data = data.split("|")
            print(data)
            if data[0] == "ReadDATA":
                print("=> read_data()")
                listChannels = data[1]
                listChannels = listChannels.split(",")
                listChannels = list(map(int, listChannels))
                print(listChannels)
                #listChannels = [0, 1]
                state = read_data(listChannels)
                client.send(str.encode(state))
            else:
                print("=> switch_energy()")
                state = yaml.load(data[0])
                success = switch_energy(state)
                client.send(str.encode(str(success)))
            print('+++++++++++++++++++++')

    except Exception as e:
        print("Close - " + str(e))
        client.close()
        socket.close()
