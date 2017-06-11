from web3 import Web3, KeepAliveRPCProvider
import fct
import fct_relay
import time


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
energyDelta = param['node']['delta']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# > Sellers nodes to which the user IS CONNECTED through the relay (may differ from vendors to whom the user purchased
# energy on the blockchain)
# > sellers have to be defined in parameter file (not automatically detected)
# > for now only 2 nodes are used => 1 consumer and 1 seller (producer)
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
# The user consumes his own energy (i.e. from his own solar panel or his "provider" (!= sellers)
#   => relay channel contact = NC (normally closed)
# Sellers channels contacts = NO (normally open)
# Energy form one seller at a time
listChannels = relaySellersChannels
listChannels.append(nodeChannel)
listChannels = str(listChannels).strip('[]')
listStates = fct_relay.readData(listChannels)

nodeChannelState = listStates[nodeChannel]
if nodeChannelState:
    myEnergy = False
else:
    myEnergy = True  # default : state 0 and NC
print("myEnergy = " + str(myEnergy))

print("Defining current seller")
currentSeller = ""
if not myEnergy:
    for channel in relaySellersChannels:
        if listStates[channel]:  # if channel state = 1, energy is provided
            currentSeller = listConnectedSellers[relaySellersChannels.index(channel)]

            # control that user can still consume energy
            # if not, switch to the user provider
            allowance = daisee.call().allowance(currentSeller, nodeAddress)

            if allowance <= 0:

                data = "{" + str(nodeChannel) + ": False, " + str(channel) + ": False}"
                fct_relay.switchChannels(data)
                currentSeller = ""
        break  # one of sellers is connected
print("> currentSeller = " + currentSeller)

time0 = fct.getDateTime(nodeURL, dataTime, headersTime) # TODO : better save and use the latest time processed


while 1:

    print("==========================")
    # delay to define
    time.sleep(16)

    # getting energy produced or consumed
    time1 = fct.getDateTime(nodeURL, dataTime, headersTime)
    sumWatt = fct.getEnergySum(nodeURL, sensorId, dataTime, headersTime, time0, time1)

    print(' > time : ' + time.strftime("%D %H:%M:%S", time.localtime(int(time1))) + ', sumWatt = ' + str(sumWatt))

    time0 = time1

    if sumWatt != 0:

        # Consumer
        if param['node']['typ'] == 'C':

            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, nodeAccountPswd)
            # TODO : error handling
            print(' > unlockOK = ' + str(unlockOK))

            if currentSeller != "":
                # check allowance (may have changer since the last call)
                allowance = daisee.call().allowance(currentSeller, nodeAddress)
                print(" > allowance = " + str(allowance) + " - sumwatt = " + str(sumWatt))

                if allowance < sumWatt:
                    print("BuyEnergy")
                    try:
                        result = daisee.transact({'from': nodeAddress}).buyEnergy(tokenContract,
                                                                                  currentSeller,
                                                                                  sumWatt + energyDelta)
                    except Exception as e:
                        print('> ERROR - function buyEnergy : ' + str(e))
                        channel = relaySellersChannels[listConnectedSellers.index(currentSeller)]
                        data = "{" + str(nodeChannel) + ": False, " + str(channel) + ": False}"
                        fct_relay.switchChannels(data)
                        currentSeller = ""

                    else:
                        print(' > result = buyEnergy ' + str(result))

                # updating Energy Consumption
                print('ConsumeEnergy')
                try:
                    result = daisee.transact({'from': nodeAddress}).consumeEnergy(currentSeller, sumWatt)
                except Exception as e:
                    print(' > ERROR - function consumeEnergy : ' + str(e))
                else:
                    print(' > result (transaction hash) = ' + str(result))

            else:
                # updating Energy Consumption
                print('ConsumeEnergy')
                result = daisee.transact({'from': nodeAddress}).consumeEnergy(nodeAddress, sumWatt)
                print(' > result (transaction hash) = ' + str(result))


        # Producer
        else:
            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, nodeAccountPswd)
            print(' > unlockOK = ' + str(unlockOK))

            # to update Energy balance (producer)
            print('SetProduction')
            result = daisee.transact({'from': nodeAddress}).setProduction(sumWatt)
            print(' > result (transaction hash) = ' + str(result))
