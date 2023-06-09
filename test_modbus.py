from pymodbus.pdu import ModbusRequest
from pymodbus.client import ModbusSerialClient
from pymodbus.transaction import ModbusRtuFramer

client = ModbusSerialClient(method='rtu', port='COM4', stopbits=1, bytesize=8, parity='N', baudrate=9600, timeout=.1)
# client.connect()
res = client.read_holding_registers(address=4096, count=8, slave=1)
print(res.registers)
client.write_register(address=4097, value=10, slave=1)
print(res.registers)
# res = client.read_holding_registers(4096, 0x01, unit=1)

