from connections.Uart import Uart
import connections.Modbus as Modbus
from Utils.Pid import PID
import struct
from connections.I2C import I2C
from Forno import Forno
import time
from threading import Event, Thread 

class Main():
    uart = Uart()
    pid = PID()
    forno = Forno()
    ref_temp = 0
    internal_temp = 0
    response = 0

    def __init__(self):
        self.menu()

    def menu(self):
        while(True):

            self.read_user_comands()

            print(self.response)

            if self.response == 161:
                message = Modbus.send_sys_on_off + b'\x01'
                self.uart.write(message,  8)
                data = self.uart.read()
                if data == b'\x01\x00\x00\x00':
                    print("Liga o Forno")

            elif self.response == 162:
                message = Modbus.send_sys_on_off + b'\x00'
                self.uart.write(message,  8)
                data = self.uart.read()
        
                if data == b'\x00\x00\x00\x00':
                    print("Desliga o Forno")
                    
            elif self.response == 163:
                self.read_temperatures()

                while self.internal_temp != self.ref_temp:
                    pid_atual = self.pid.pid_controle(self.ref_temp, self.internal_temp)
                    print("pid " + str(pid_atual))
                    
                    if(pid_atual < 0):
                        pid_atual *= -1
                        if(pid_atual < 40):
                            pid_atual = 40
                        self.forno.cool_down(pid_atual)
                    else:    
                        self.forno.heat(pid_atual)

                    self.read_temperatures()
                    self.read_user_comands()
                    
            elif self.response == 164:
                pass
            elif self.response == 165:
                pass
            else:
                pass 


    def read_temperatures(self):
        self.read_ref_temp()
        time.sleep(0.5)
        self.read_internal_temp()
        time.sleep(0.5)

    
    def read_ref_temp(self):
        message = Modbus.request_ref_temp

        self.uart.write(message,  7)
        data = self.uart.read()
        self.ref_temp = struct.unpack('f', data)[0]

        print(self.ref_temp)

    
    def read_internal_temp(self):
        message = Modbus.request_internal_temp

        self.uart.write(message,  7)
        data = self.uart.read()
        self.internal_temp = struct.unpack('f', data)[0]

        print(self.internal_temp)
    
    def read_user_comands(self):
            print("Esperando comando...")
            self.uart.write(Modbus.read_user_commands,  7)

            response = self.uart.read()
            self.response = struct.unpack('i', response)[0]
            time.sleep(0.5)


if __name__ == '__main__':
    Main()