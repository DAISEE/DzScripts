from web3 import Web3, KeepAliveRPCProvider
import fct
import time
import RPi.GPIO as GPIO


def switchEnergy(myEnergy):

    print('myEnergy = ' + str(myEnergy))
    # own energy (channel 0 NC, channel 1 NO)
    if myEnergy:
        GPIO.output(Relay_channel[0], GPIO.LOW)
        GPIO.output(Relay_channel[1], GPIO.LOW)
    else:
        # node uses seller energy
        GPIO.output(Relay_channel[0], GPIO.HIGH)
        GPIO.output(Relay_channel[1], GPIO.HIGH)

param = fct.loadparam()

# Connection to Ethereum
web3 = Web3(KeepAliveRPCProvider(host=param['contract']['node'], port='8545'))

# connection to the relay
# RPI.GPIO
Relay_channel = [17, 18]
GPIO.setmode(GPIO.BCM)
GPIO.setup(Relay_channel, GPIO.OUT, initial=GPIO.LOW)

# Node parameters
node = param['usedNode']['id']
nodeAddress = param[node]['address']
nodeURL = param[node]['url']
nodeLogin = param[node]['login']
nodePswd = param[node]['password']
tokenContract = param['contract']['token']
sensorId = param[node]['sensorId']
headersTime = {'Content-Type': 'application/json', }
dataTime = 'login=' + nodeLogin + '&password=' + nodePswd

# Contract definition
daiseeAbi = fct.loadabi('daisee.sol.json')
daisee = web3.eth.contract(abi=daiseeAbi, address=param['contract']['address'])

# LED init
# getting energy balance
print('Get Energy Balance')
EnergyBalance = daisee.call({'from': param[node]['address']}).getEnergyBalance()
print(EnergyBalance)

if EnergyBalance >= param['node2']['limit'] :
    # LED on
    myEnergy = True
    switchEnergy(myEnergy)
else:
    # LED off
    myEnergy = False
    switchEnergy(myEnergy)

time0 = fct.getDateTime(nodeURL, dataTime, headersTime)
bEnergy = 0

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
        if param[node]['typ'] == 'C':

            # unlock account
            print('Unlock Account')
            unlockOK = web3.personal.unlockAccount(nodeAddress, param[node]['accountpswd'])
            print(' > unlockOK = ' + str(unlockOK))

            # updating Energy balance (consumer)
            print('ConsumeEnergy')
            result = daisee.transact({'from': nodeAddress}).consumeEnergy(sumWatt)
            print(' > result = ' + str(result))

            if not myEnergy:
                bEnergy = bEnergy + sumWatt
                if bEnergy > 200:
                    myEnergy = True

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
                    switchEnergy(False)

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
