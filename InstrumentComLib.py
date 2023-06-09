# from ElectraDAQLib import Device, Instrument
from labjack import ljm
import pandas as pd
from pymodbus.client import ModbusSerialClient

class InstrumentComError(Exception):
    pass

def connect(device):
    if device.type == "LabJackT7":
        return labjackT7_connect(device)
    if device.type == "Modbus":
        return modbus_connect(device)
    else:
        raise InstrumentComError(f"Instrument {device.name} not in InstrumentComLib")

def labjackT7_connect(device):
    params = device.connection_params
    if params['type'] == "usb":
        serial_number = params['serial_number']
        handle = ljm.openS("T7", "USB", f"{serial_number}")
        return handle
    elif params['type'] == "ethernet":
        ip = params['ip']
        handle = ljm.openS("T7", "ETHERNET", f"{ip}")
        return handle
    else:
        raise Exception("Couldn't connect")

def modbus_connect(device):
    params = device.connection_params
    if params['type'] == "rtu":
        client = ModbusSerialClient(method='rtu', port=params['port'], stopbits=params['stopbits'], bytesize=params['bytesize'], parity=params['parity'], baudrate=params['baudrate'], timeout=params['timeout'])
        return client

def read(device):
    if device.type == "LabJackT7":
        return labjackT7_read(device)
    if device.type == "Modbus":
        return modbus_read(device)
    else:
        raise InstrumentComError(f"Instrument {device.name} not in InstrumentComLib")

def labjackT7_read(device):
    #Read 10 points then return average
    handle = device.connection
    instruments = device.instruments
    channels = [inst.channel for inst in instruments]
    read_data = pd.DataFrame({inst.tag:[] for inst in instruments})
    for i in range(10):
        current_read = ljm.eReadNames(handle, len(channels), channels)
        read_data.loc[len(read_data)] = current_read
    return_data = pd.DataFrame({col: [read_data[col].mean()] for col in read_data.columns})
    return return_data

def modbus_read(device):
    client = device.connection
    instruments = device.instruments
    return_data = pd.DataFrame({inst.tag:[] for inst in instruments})
    for inst in instruments:
        res = client.read_holding_registers(address=inst.channel, count=1, slave=inst.slave)
        return_data[inst.tag] = [res.registers[0]]
    return return_data


def write(device):
    if device.type == "LabJackT7":
        labjackT7_read()
    else:
        raise InstrumentComError(f"Instrument {device.name} not in InstrumentComLib")

def labjackT7_write(device):
    pass