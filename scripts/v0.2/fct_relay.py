import fct
import socket
import yaml

param = fct.loadparam()

# > Relay info
relayHost = param['relay']['host']
relayPort = param['relay']['port']


def createConnection():
    s = socket.create_connection((relayHost, relayPort))
    print("Socket relay - Connection on {}".format(relayPort))
    return s


def closeConnection(s):
    print("Socket relay - Close")
    s.close()


def readData(channels):

    s = createConnection()

    data = "ReadDATA|" + str(channels)
    s.send(data.encode())
    resp = s.recv(255)

    closeConnection(s)

    listStates = yaml.load(resp)
    return listStates


def switchChannels(data):

    s = createConnection()

    s.send(data.encode())
    resp = s.recv(255)
    print(resp.decode())

    closeConnection(s)

    return resp.decode()