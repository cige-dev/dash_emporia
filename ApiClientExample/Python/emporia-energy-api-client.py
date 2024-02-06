import math
import time
import sys
import grpc
import partner_api2_pb2_grpc as api
from partner_api2_pb2 import *

# Set an EV Charger to the provided settings 
def changeEVChargerToSettings(stub, auth_token, evCharger):
    updateRequest = UpdateEVChargersRequest()
    updateRequest.auth_token = auth_token    
    updateRequest.settings.append(evCharger.settings)    
    updateResponse = stub.UpdateEVChargers(updateRequest)   # will return us the device if it was changed to the new setting    
    if (len(updateResponse.evchargers) == 1):
        updatedEVSE = updateResponse.evchargers[0]
        print(f'Changed {updatedEVSE.settings.manufacturer_device_id}\'s to {updatedEVSE.settings}')       
    else:
        print(f'ERROR: failed to update: {updateResponse}')
    time.sleep(1) # Python's sleep is in seconds.

# Set a battery to the provided settings
def changeBatteryToSettings(stub, auth_token, battery):
    updateRequest = UpdateBatteriesRequest()
    updateRequest.auth_token = auth_token    
    updateRequest.settings.append(battery.settings)    
    updateResponse = stub.UpdateBatteries(updateRequest)   # will return us the device if it was changed to the new setting    
    if (len(updateResponse.batteries) == 1):
        updatedBattery = updateResponse.batteries[0]
        print(f'Changed {updatedBattery.settings.manufacturer_device_id}\'s to {updatedBattery.settings}')       
    else:
        print(f'ERROR: failed to update: {updateResponse}')
    time.sleep(1) # Python's sleep is in seconds.


if len(sys.argv) != 3:
    print('usage: ' + sys.argv[0] + ' partnerEmail (the email you use to login to the portal at http://partner.emporiaenergy.com) password (that you use for the portal)')
    sys.exit(1)

partnerApiEndpoint = 'partner.emporiaenergy.com:50052'  # this is the V2 of the Partner API

creds = grpc.ssl_channel_credentials()
channel = grpc.secure_channel(partnerApiEndpoint, creds)

# client stub (blocking)
stub = api.PartnerApiStub(channel)

request = AuthenticationRequest()
request.partner_email = sys.argv[1]
request.password = sys.argv[2]
auth_response = stub.Authenticate(request=request)

auth_token = auth_response.auth_token

# get list of devices managed by partner
inventoryRequest = DeviceInventoryRequest()
inventoryRequest.auth_token = auth_token
inventoryResponse = stub.GetDevices(inventoryRequest)

# display device information
print(f'Your partner account has {len(inventoryResponse.devices)} devices associated to it')

devices = inventoryResponse.devices

vue2_list = [dev for dev in devices if dev.model == DeviceInventoryResponse.Device.DeviceModel.Vue2]

print(f'\n***Your partner account has {len(vue2_list)} Vue2s associated to it')
if len(vue2_list) > 0:
    vue2 = vue2_list[0]
    model = vue2.model
    print("Here are the details of the first one")
    print(f'Manufacturer Device Id: {vue2.manufacturer_device_id}')
    print(f'                 Model: {DeviceInventoryResponse.Device.DeviceModel.Name(model)}')
    print(f'                  Name: {vue2.device_name}')
    print(f'      Device Connected: {vue2.device_connected}')

    print(f'Here are the circuit_infos describing the circuits available on this device:' )
    for circuitInfo in vue2.circuit_infos:
        # this print converts to the correct enum value and then concatenates all 5 of these strings onto a single line
        print( f'{circuitInfo.channel_number:2}'
               f'{DeviceInventoryResponse.Device.CircuitInfo.CircuitType.Name(circuitInfo.type):20}' 
               f'{DeviceInventoryResponse.Device.CircuitInfo.EnergyDirection.Name(circuitInfo.energy_direction):20}'
               f'{circuitInfo.sub_type:20}'
               f'{circuitInfo.name:20}' )

    deviceUsageRequest = DeviceUsageRequest()
    deviceUsageRequest.auth_token = auth_token

    now = math.ceil(time.time()) # seconds as integer
    deviceUsageRequest.start_epoch_seconds = now - 3600 # one hour of seconds
    deviceUsageRequest.end_epoch_seconds = now
    deviceUsageRequest.scale = DataResolution.FifteenMinutes
    deviceUsageRequest.channels = DeviceUsageRequest.UsageChannel.MAINS
    deviceUsageRequest.manufacturer_device_ids.append(vue2.manufacturer_device_id)

    usageResponse = stub.GetUsageData(deviceUsageRequest)

    for usage in usageResponse.device_usages:
        print("Energy (kWhs) & Power (kWatts) on the 3 mains channels over recent 15 minute buckets:")
        cnt = len(usage.bucket_epoch_seconds)
        for i in range(cnt):
            print(f'{usage.bucket_epoch_seconds[i]}: kWhs / kWatts')
            for j in range(len(usage.channel_usages)):
                kWhs = usage.channel_usages[j].usages[ i ]
                # multiply by 4 to get to power since this is 15min energy using 2 kWhs of energy in 15 minutes is consuming at a 8 kWatts rate
                kWatts = kWhs * 4
                channel  = usage.channel_usages[j].channel
                print( f'  ({channel}) {kWhs:.2f}/{kWatts:.2f}')

outlet_list = [dev for dev in devices if dev.model == DeviceInventoryResponse.Device.DeviceModel.Outlet]
print(f'\n***Your partner account has {len(outlet_list)} Outlets associated to it')
if len(outlet_list) > 0:
    outlet = outlet_list[0]
    listDevicesRequest = ListDevicesRequest()
    listDevicesRequest.auth_token = auth_token
    listDevicesRequest.manufacturer_device_ids.append(outlet.manufacturer_device_id)

    listDevicesResponse = stub.ListOutlets(listDevicesRequest)
    first_outlet = listDevicesResponse.outlets[0]

    model = outlet.model

    print("Here are the details of the first outlet")
    print(f' Manufacturer Device Id: {outlet.manufacturer_device_id}')
    print(f'                  Model: {DeviceInventoryResponse.Device.DeviceModel.Name(model)}')
    print(f'                   Name: {outlet.device_name}')
    print(f'       Device Connected: {outlet.device_connected}')
    print(f'              Outlet On: {first_outlet.on}')

    # toggle outlet state
    if outlet.device_connected :
        print( f'toggling the On/Off for outlet {outlet.manufacturer_device_id}')
        first_outlet.on = not first_outlet.on
        updateOutletRequest = UpdateOutletsRequest()
        updateOutletRequest.auth_token = auth_token
        updateOutletRequest.outlets.append(first_outlet)
        updateOutletResponse = stub.UpdateOutlets(updateOutletRequest)
        print( f'updateOutletsResponse indicates the on/off flag is {updateOutletResponse.outlets[0].on}')
    else :
        print( f'Outlet {outlet.manufacturer_device_id} is not connected so we cannot turn it on/off')        


charger_list = [dev for dev in devices if dev.model == DeviceInventoryResponse.Device.DeviceModel.EVCharger]
print(f'\n***Your partner account has {len(charger_list)} EV Chargers associated to it')
if len(charger_list) > 0:
    charger = charger_list[0]
    listDevicesRequest = ListDevicesRequest()
    listDevicesRequest.auth_token = auth_token
    listDevicesRequest.manufacturer_device_ids.append(charger.manufacturer_device_id)

    listDevicesResponse = stub.ListEVChargers(listDevicesRequest)
    first_charger = listDevicesResponse.evchargers[0]

    model = charger.model

    print("Here are the details of the first EV Charger")
    print(f' Manufacturer Device Id: {charger.manufacturer_device_id}')
    print(f'                  Model: {DeviceInventoryResponse.Device.DeviceModel.Name(model)}')
    print(f'                   Name: {charger.device_name}')
    print(f'       Device Connected: {charger.device_connected}')
    print(f'          Car Connected: {first_charger.car_connected}')
    print(f'           Car Charging: {first_charger.car_charging}')
    print(f'   Max Charge Rate Amps: {first_charger.max_charge_rate_amps}')
    print(f'             Charger On: {first_charger.settings.on.value}')
    print(f'       Charge Rate Amps: {first_charger.settings.charge_rate_amps.value}')

    # now we change the charger to a different setting and then put it back
    originalSettings = EVChargerSettings()
    originalSettings.CopyFrom(first_charger.settings)

    print( "Changing charger to off at a rate of 10 amps" )
    first_charger.settings.on.value = False
    first_charger.settings.charge_rate_amps.value = 10
    changeEVChargerToSettings(stub=stub, auth_token=auth_token, evCharger=first_charger)

    print( "cause an error by trying to set the charger rate impossibly high." )
    try:
        first_charger.settings.charge_rate_amps.value = 100
        changeEVChargerToSettings(stub=stub, auth_token=auth_token, evCharger=first_charger)
    except Exception as e:
        print( f'Caught the expected exception: {e}')
    
    # now change it back to the original settings
    print( "\n*** Setting the EVCharger back to the original settings" )
    first_charger.settings.CopyFrom(originalSettings)
    changeEVChargerToSettings(stub=stub, auth_token=auth_token, evCharger=first_charger)


battery_list = [dev for dev in devices if dev.model == DeviceInventoryResponse.Device.DeviceModel.Battery]
print(f'\n***Your partner account has {len(battery_list)} Batteries associated to it')
if len(battery_list) > 0:
    battery = battery_list[0]
    listDevicesRequest = ListDevicesRequest()
    listDevicesRequest.auth_token = auth_token
    listDevicesRequest.manufacturer_device_ids.append(battery.manufacturer_device_id)
    model = battery.model

    listDevicesResponse = stub.ListBatteries(listDevicesRequest)
    first_battery = listDevicesResponse.batteries[0]

    print("Here are the details of the first Battery")
    print(f' Manufacturer Device Id: {battery.manufacturer_device_id}')
    print(f'                  Model: {DeviceInventoryResponse.Device.DeviceModel.Name(model)}')
    print(f'                   Name: {battery.device_name}')
    print(f'       Device Connected: {battery.device_connected}')
    print(f'           Capacity kWh: {first_battery.capacity_kwhs}')
    print(f'  Inverter Max Power kW: {first_battery.inverter_max_power_kwatts}')
    print(f'            Reserve SOC: {first_battery.settings.reserve_soc_percentage.value}')
    print(f'        State of Charge: {first_battery.soc_percentage.value}')
    print(f'          Dispatch Mode: {first_battery.settings.WhichOneof("dispatch_mode")}')

    # now we change the battery to several different settings and then put it back 
    originalSettings = BatterySettings()
    originalSettings.CopyFrom(first_battery.settings)
    
    print( "Changing battery to a lower Reserve State of Charge" )
    first_battery.settings.reserve_soc_percentage.value = first_battery.settings.reserve_soc_percentage.value - 1
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery)
    
    print( "Set battery to Load Following at 2 kWatts" ) 
    first_battery.settings.load_following.power_kwatts.value = 2    
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery)

    print( "Set battery to charge from Excess Solar" )
    first_battery.settings.charge_with_excess_solar.charge_power_kwatts.value = 5
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery)

    print( "Set battery to charge to 90 percent" )
    first_battery.settings.charge_to_state_of_charge.soc_percentage.value = 90.0
    first_battery.settings.charge_to_state_of_charge.charge_power_kwatts.value = 3
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery)
    
    print( "Set battery to discharge to 30 percent" )
    first_battery.settings.discharge_to_state_of_charge.soc_percentage.value = 30.0
    first_battery.settings.discharge_to_state_of_charge.discharge_power_kwatts.value = 3
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery)

    # now change it back to the original settings
    print( "\n*** Setting the battery back to the original settings" )
    first_battery.settings.CopyFrom(originalSettings)
    changeBatteryToSettings(stub=stub, auth_token=auth_token, battery=first_battery) 