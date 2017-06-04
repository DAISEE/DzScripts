import fct
import socket
import yaml

param = fct.loadparam()

# > Relay info
relayHost = param['relay']['host']
relayPort = param['relay']['port']
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def readData(channels):

    socket.connect((relayHost, relayPort))
    print("Socket relay - Connection on {}".format(relayPort))

    data = "ReadDATA|" + str(channels)
    socket.send(data.encode())
    resp = socket.recv(255)
    print(resp.decode())

    print("Socket relay - Close")
    socket.close()

    listStates = yaml.load(resp)
    return listStates


def switchChannels(data):

    socket.connect((relayHost, relayPort))
    print("Socket relay - Connection on {}".format(relayPort))

    socket.send(data.encode())
    resp = socket.recv(255)
    print(resp.decode())

    print("Close")
    socket.close()
