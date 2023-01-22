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
    i2c = I2C()
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

                message = Modbus.send_sys_state + b'\x01'
                self.uart.write(message,  8)
                data = self.uart.read()
                
                if data == b'\x01\x00\x00\x00':
                    print("Sistema em funcionamento")

                while self.response != 164:
                    pid_atual = self.pid.pid_controle(self.ref_temp, self.internal_temp)
                    print("pid " + str(pid_atual))
                    
                    if(pid_atual < 0):
                        pid_atual *= -1
                        if(pid_atual < 40):
                            pid_atual = 40
                        print("Esfriando")
                        self.forno.cool_down(pid_atual)
                    else: 
                        print("Esquentando")   
                        self.forno.heat(pid_atual)

                    self.read_temperatures()
                    self.read_user_comands()
                self.turn_off_system()
                
            elif self.response == 165:
                message = Modbus.change_ref_temp_control_mode + b'\x01'
                self.uart.write(message,  8)
                data = self.uart.read()
                self.response = 0

                if data == b'\x01\x00\x00\x00':
                    print("Modo curva ativado") 

                self.debug_algorithm()

                message = Modbus.change_ref_temp_control_mode + b'\x00'
                self.uart.write(message,  8)
                data = self.uart.read()
                if data == b'\x00\x00\x00\x00':
                    print("Modo curva desativado") 
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

    def turn_off_system(self):
        message = Modbus.send_sys_state + b'\x00'
        self.uart.write(message,  8)
        data = self.uart.read()
        time.sleep(0.5)
        if data == b'\x00\x00\x00\x00':
            print("Sistema interrompido")
            room_temp = self.i2c.return_room_temp()
            if  self.internal_temp > room_temp:
                self.forno.cool_down(self.pid.pid_controle(room_temp, self.internal_temp))
            elif self.internal_temp < room_temp:
                self.forno.heat(self.pid.pid_controle(room_temp, self.internal_temp))

    def debug_algorithm(self):
        i = 0
        pilha_tempo = [0, 60, 120, 240, 260, 300, 360, 420,480, 600]
        pilha_ref = [25, 38, 46, 54, 57, 61, 63 ,54, 33, 25]
        aux = 0
        while len(pilha_tempo) > 0 and self.response != 165:
            if(pilha_tempo[0] == i):
                pilha_tempo.pop(0)
                aux = pilha_ref.pop(0)

            self.read_internal_temp()
        
            pid_atual = self.pid.pid_controle(aux , self.internal_temp)

            if(pid_atual < 0):
                pid_atual *= -1
                if(pid_atual < 40):
                    pid_atual = 40
                print("Esfriando")
                self.forno.cool_down(pid_atual)
            else: 
                print("Esquentando")   
                self.forno.heat(pid_atual)
                
            self.read_user_comands()

            time.sleep(1)
            i = i + 1

if __name__ == '__main__':
    Main()