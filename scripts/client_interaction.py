from web3 import Web3, KeepAliveRPCProvider
import fct
import fct_relay
import sys
import time


param = fct.loadparam()

filename = "/tmp/sensor.log"
try:
    with open(filename):
        pass
except FileNotFoundError:
    sys.exit("Unable to open file " + filename + ".")


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
hasFuelGauge = param['node']['fuelgauge']
threshold = param['node']['limit']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# PROTO V0.2 HYPOTHESES
# =====================
# > Sellers nodes to which the user IS CONNECTED through the relay may differ from vendors to whom the user purchased
# energy on the blockchain
# > Each node (consumer or producer) is connected to 2 channels :
# - first channel is connected to energy source (= "energy" channel)
# - second channel is connected to the components consuming energy
# > Sellers have to be defined in parameter file (not automatically detected). All connected sellers can sell energy
# (no verification of production capacity for the moment)
# > For now only 2 nodes are used => 1 consumer (channels 2 and 3) and 1 seller (producer, channels 0 and 1)
nodeChannel = param['node']['channel']
connectedSellers = param['sellers']
currentSeller = ""

hasSellers = False
# Address of the sellers' nodes and the "energy" channel to which they are connected (see file parameter)
if connectedSellers != "":
    hasSellers = True

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


# > Getting the state of charge of the battery
# data from CitizenWatt App running on the same node (from fuel gauge sensor for a Consumer Node - acs712-soc branch)
soc = 100
if hasFuelGauge:
    soc = fct.getSoC(filename)
    print("Battery state of charge = " + str(soc))

# > Getting the state of relay
# Default : Relay state = False
# The user consumes his own energy (i.e. from his own solar panel or his "provider" (!= sellers))
#   => relay channel contact = NC (normally closed)
# Sellers channels contacts = NO (normally open)
# Energy form one seller at a time (= only one seller "energy" channel can be closed)
if hasSellers:
    listChannels = relaySellersChannels
    listChannels.append(nodeChannel)
    listChannels = str(listChannels).strip('[]')
    listStates = fct_relay.readData(listChannels)

    nodeChannelState = listStates[nodeChannel]
    # reminder : Consumer node
    # - False = closed (it consumes its "own" energy)
    # - True = open
    if nodeChannelState:
        myEnergy = False
    else:
        if hasFuelGauge and soc < threshold:
            myEnergy = False
        else:
            myEnergy = True  # default : state False and NC
    print("myEnergy = " + str(myEnergy))


    print("Defining current seller")
    if not myEnergy:
        for channel in relaySellersChannels:
            if listStates[channel]:  # if channel state = 1, energy is provided
                currentSeller = listConnectedSellers[relaySellersChannels.index(channel)]

                # control that user can still consume energy
                # if not, switch to the user provider
                allowance = daisee.call().allowance(currentSeller, nodeAddress)

                if allowance == 0:
                    data = "{" + str(nodeChannel) + ": False, " + str(nodeChannel + 1) + ": False, " + \
                                 str(channel) + ": False, " + str(channel + 1) + ": False}"
                    fct_relay.switchChannels(data)  # switch to user energy (even the Soc is under the threshold)
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
                        data = "{" + str(nodeChannel) + ": False, " + str(nodeChannel + 1) + ": False, " + \
                                     str(channel) + ": False, " + str(channel + 1) + ": False}"
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
                # currentSeller == ""
                # => the Node consumes its "own" energy
                # => All channels' states are False

                # updating Energy Consumption
                print('ConsumeEnergy')
                result = daisee.transact({'from': nodeAddress}).consumeEnergy(nodeAddress, sumWatt)
                print(' > result (transaction hash) = ' + str(result))

                # check the State of charge
                soc = fct.getSoC(filename)
                print("State of charge (soc) = " + str(soc))
                if soc < threshold:

                    print(" > soc < threshold")
                    for seller in listConnectedSellers:

                        print(" > seller = " + str(seller))
                        allowance = daisee.call().allowance(seller, nodeAddress)
                        print(" > allowance = " + str(allowance))

                        if allowance > 0:

                            channel = relaySellersChannels[listConnectedSellers.index(seller)]
                            print(" > channel = " + str(channel))

                            # channel = 0  # TODO : use a function to define the channel
                            data = "{" + str(nodeChannel) + ": True, " + str(nodeChannel + 1) + ": True, " + \
                                         str(channel) + ": True, " + str(channel + 1) + ": True}"
                            print(" > data = " + str(data))
                            fct_relay.switchChannels(data)
                            # currentSeller = listConnectedSellers[relaySellersChannels.index(channel)]
                            currentSeller = seller
                            print(" > update current seller : " + str(currentSeller))
                            break

                    # if all sellers allowances are equal to zero, the current node buys energy form the first seller
                    # connected
                    if currentSeller == "":

                        seller = listConnectedSellers[0]
                        channel = relaySellersChannels[0]
                        print("BuyEnergy from seller : " + seller + ", channel : " + str(channel))

                        try:
                            result = daisee.transact({'from': nodeAddress}).buyEnergy(tokenContract,
                                                                                      seller,
                                                                                      sumWatt + energyDelta)

                        except Exception as e:
                            print('> ERROR - function buyEnergy : ' + str(e))

                            data = "{" + str(nodeChannel) + ": False, " + str(nodeChannel + 1) + ": False, " + \
                                   str(channel) + ": False, " + str(channel + 1) + ": False}"
                            print(" > data = " + str(data))
                            fct_relay.switchChannels(data)

                            currentSeller = ""
                            print(" > update current seller : " + str(currentSeller))

                        else:
                            print(' > result = buyEnergy ' + str(result))

                            data = "{" + str(nodeChannel) + ": True, " + str(nodeChannel + 1) + ": True, " + \
                                   str(channel) + ": True, " + str(channel + 1) + ": True}"
                            print(" > data = " + str(data))
                            fct_relay.switchChannels(data)

                            currentSeller = seller
                            print(" > update current seller : " + str(currentSeller))


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
