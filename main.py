from connections.Uart import Uart
import connections.Modbus as Modbus
import struct
from connections.I2C import I2C
from Forno import Forno
import time

uart = Uart()

uart.write(Modbus.request_internal_temp,  7)

data = uart.read()
   
temp = struct.unpack('f', data)[0]
print(temp)

forno = Forno()

while(True):
    uart.write(Modbus.read_user_commands,  7)

    response = uart.read()
    response = struct.unpack('i', response)[0]

    if response == 161:
        message = Modbus.send_sys_on_off + b'\x01'
        uart.write(message,  8)
        data = uart.read()
        if data == b'\x01\x00\x00\x00':
            print("Sistema Ligado")

    elif response == 162:
        message = Modbus.send_sys_on_off + b'\x00'
        uart.write(message,  8)
        data = uart.read()
        if data == 0:
            print("Sistema Desligado")
            
    elif response == 163:
        forno.heat()
    elif response == 164:
        print("FunFoou")
        pass
    elif response == 165:
        pass
    else:
        pass 

    time.sleep(0.5)
        