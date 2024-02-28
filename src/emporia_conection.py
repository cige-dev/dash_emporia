import src.partner_api2_pb2_grpc as api
from src.partner_api2_pb2 import *
import pandas as pd
import numpy as np
import grpc


def data_extract(cliente, start_interval, end_interval):
    # Endpoint // Response // Full conection
    partnerApiEndpoint = 'partner.emporiaenergy.com:50052'
    creds = grpc.ssl_channel_credentials()
    channel = grpc.secure_channel(partnerApiEndpoint, creds)
    stub = api.PartnerApiStub(channel)
    request = AuthenticationRequest()
    request.partner_email = 'hsoto@cigepty.com'
    request.password = 'hsm280466'
    auth_response = stub.Authenticate(request=request)
    auth_token = auth_response.auth_token
    inventoryRequest = DeviceInventoryRequest()
    inventoryRequest.auth_token = auth_token
    inventoryResponse = stub.GetDevices(inventoryRequest)
    deviceUsageRequest = DeviceUsageRequest()
    deviceUsageRequest.auth_token = auth_token
    deviceUsageRequest.start_epoch_seconds = int(start_interval)
    deviceUsageRequest.end_epoch_seconds = int(end_interval)
    deviceUsageRequest.scale = DataResolution.Days
    deviceUsageRequest.channels = DeviceUsageRequest.UsageChannel.ALL
    usageResponse = stub.GetUsageData(deviceUsageRequest)

    # Creating the output data object
    names = {}; data = pd.DataFrame(); device_id=''
    for device in inventoryResponse.devices: 
        if cliente.lower() in device.device_name.lower():
            device_name = device.device_name
            device_id = device.manufacturer_device_id
            for circuit in device.circuit_infos:
                if circuit.name != '':
                    names[circuit.channel_number] = circuit.sub_type+'-'+circuit.name
            break
    device_found =  [i for i in usageResponse.device_usages if i.manufacturer_device_id==device_id]
    if len(device_found)==0:
        return data, device_name
    else:
        device_found = device_found[0]
        data['Time Bucket'] = pd.date_range(start=pd.to_datetime(device_found.bucket_epoch_seconds[0], unit='s'),
                                            end=pd.to_datetime(device_found.bucket_epoch_seconds[-1], unit='s'),
                                            periods=len(device_found.bucket_epoch_seconds)).date
        for circuit in device_found.channel_usages:
            if circuit.channel in names.keys():
                data[f'{circuit.channel}-{names[circuit.channel]}'] = np.array(circuit.usages)/1000
            if circuit.channel == 1: data[f'{circuit.channel}-Mains_A'] = np.array(circuit.usages)/1000
            if circuit.channel == 2: data[f'{circuit.channel}-Mains_B'] = np.array(circuit.usages)/1000
            if circuit.channel == 3: data[f'{circuit.channel}-Mains_C'] = np.array(circuit.usages)/1000
        return data, device_name