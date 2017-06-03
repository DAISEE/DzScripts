from web3 import Web3, KeepAliveRPCProvider
import fct
import socket
import time
import yaml

param = fct.loadparam()

# Connection to Ethereum
web3 = Web3(KeepAliveRPCProvider(host=param['contract']['node'], port='8545'))

# Parameters
# > Blockchain info
nodeAddress = param['node']['address']
nodeAccountPswd = param['node']['accountpswd']
tokenContract = param['contract']['token']

# > Energy monitoring app
nodeURL = param['node']['url']
nodeLogin = param['node']['login']
nodePswd = param['node']['password']
sensorId = param['node']['sensorId']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# > Sellers nodes to which the user IS CONNECTED through the relay (may differ from vendors to whom the user purchased
# energy on the blockchain)
# > sellers have to be defined in parameter file (not automatically detected)
# > for now only 2 nodes are used => 1 seller
nodeChannel = param['node']['channel']
connectedSellers = param['sellers']

relaySellersChannels = []
listConnectedSellers = []

for seller in connectedSellers.items():
    listConnectedSellers.append(seller[1]['account'])
    relaySellersChannels.append(seller[1]['channel'])

# > Relay info
relayHost = param['relay']['host']
relayPort = param['relay']['port']


# Init
# > Contract definition
daiseeAddress = param['contract']['address']
daiseeAbi = fct.loadabi('daisee.sol.json')
daisee = web3.eth.contract(abi=daiseeAbi, address=daiseeAddress)

# > Getting the state of relay
# Default : relay state = False
# The user consumes his own energy (i.e. from his own solar panel or his "provider" (<> sellers) => relay channel = NC
# Sellers channels : NO
# Energy form one seller at a time
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((relayHost, relayPort))
print("Socket relay - Connection on {}".format(relayPort))

socket.send(b"ReadDATA|0,1")
resp = socket.recv(255)
print(resp.decode())

print("Socket relay - Close")
socket.close()

listStates = yaml.load(resp)
print(type(listStates))

nodeChannelState = listStates[nodeChannel]
if nodeChannel:
    myEnergy = False
else:
    myEnergy = True  # default : state 0 and NC


if not myEnergy: # one of sellers is connected
    for channel in relaySellersChannels:
        if listStates[channel]:  # if channel state = 1, energy is provided

            currentSeller = listConnectedSellers[relaySellersChannels.index(channel)]

            # control that user can still consume energy
            # if not, switch to the user provider
            allowance = daisee.call().allowance(currentSeller, nodeAddress)
            print("allowance = " + str(allowance))

            if allowance <= 0:

                socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                socket.connect((relayHost, relayPort))
                print("Socket relay - Connection on {}".format(relayPort))

                data = "{" + str(nodeChannel) + ": False, " + str(channel) + ": False}"
                socket.send(data.encode())
                resp = socket.recv(255)
                print(resp.decode())

                print("Close")
                socket.close()

                currentSeller = ""


time0 = fct.getDateTime(nodeURL, dataTime, headersTime)   # TODO : better save and use the latest time processed


while 1:
    # delay to define
    time.sleep(16)

    # getting energy produced or consumed
    time1 = fct.getDateTime(nodeURL, dataTime, headersTime)
    sumWatt = fct.getEnergySum(nodeURL, sensorId, dataTime, headersTime, time0, time1)

    print('time : ' + time.strftime("%D %H:%M:%S", time.localtime(int(time1))) + ', sumWatt = ' + str(sumWatt))

    time0 = time1

    if sumWatt != 0:

        # Consumer
        if param['node']['typ'] == 'C':

            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, nodeAccountPswd)
            print(' > unlockOK = ' + str(unlockOK))

            # updating Energy balance (consumer)
            print('ConsumeEnergy')
            result = daisee.transact({'from': nodeAddress}).consumeEnergy(sumWatt)
            print(' > result = ' + str(result))

            # if not myEnergy:
            #    bEnergy = bEnergy + sumWatt
            #    if bEnergy > 200:
            #        myEnergy = True

            # getting the energy balance
            print('Get Energy Balance')
            EnergyBalance = daisee.call({'from': param[node]['address']}).getEnergyBalance()
            print(' > EnergyBalance = ' + str(EnergyBalance))

            # if energy balance is too low, a energy transaction is triggered
            if EnergyBalance < param[node]['limit']:

                myEnergy = False

                # unlock account
                print('Unlock Account')
                unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
                print(' > unlockOK = ' + str(unlockOK))

                print('Buy Energy')
                # beware of tokens allowed (see function approve() in token smart contract)
                # watt : to adjust
                watt = 200
                # for DEBUG/TESTING, node2 is selected by default
                seller = param['node2']['address']
                try:
                    ret = daisee.transact({'from': nodeAddress}).buyEnergy(tokenContract, seller, watt)
                except Exception as e:
                    print('ERROR - function buyEnergy : ' + str(e))
                else:
                    print(' > result = ' + str(result))
                    #switchEnergy(False)

        # Producer
        else:
            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
            print(' > unlockOK = ' + str(unlockOK))

            # to update Energy balance (producer)
            print('SetProduction')
            result = daisee.transact({'from': nodeAddress}).setProduction(sumWatt)
            print(' > result = ' + str(result))
