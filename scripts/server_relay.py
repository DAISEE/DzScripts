import RPi.GPIO as GPIO
import socket
import yaml


def read_data(relay):
    # relay
    # format: list
    # example: [0, 1]

    relayState = {}
    for channel in relay:

        if GPIO.input(Relay_channel[channel]) == 0:
            relayState[channel] = False
        else:
            relayState[channel] = True

    return str(relayState)


def switch_energy(relay):

    # format: dict
    # example: {0: False, 1: True}
    try:
        for channel, state in relay.items():
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

# socket init
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('', 15555))


while True:

    s.listen(5)
    client, address = s.accept()
    print("{} connected".format(address))

    try:
        response = client.recv(255)
        if response != "":
            data = response.decode()
            data = data.split("|")

            if data[0] == "ReadDATA":
                print("=> read_data()")
                listChannels = data[1]
                listChannels = listChannels.split(",")
                listChannels = list(map(int, listChannels))
                state = read_data(listChannels)
                client.send(str.encode(state))
            else:
                print("=> switch_energy()")
                state = yaml.safe_load(data[0])
                success = switch_energy(state)
                client.send(str.encode(str(success)))
            print('+++++++++++++++++++++')

    except Exception as e:
        print("Close - " + str(e))
        client.close()
        s.close()
