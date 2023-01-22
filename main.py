from connections.Uart import Uart
import connections.Modbus as Modbus
from Utils.Pid import PID
import struct
from connections.I2C import I2C
from Forno import Forno
import time
from threading import Event, Thread
from Utils.Csv import Csv
import datetime

LIGAR_FORNO = 161
DESLIGAR_FORNO = 162
LIGAR_SISTEMA = 163
DESLIGAR_SISTEMA = 164
ALTERAR_MODO = 165

class Main():
    uart = Uart()
    pid = PID()
    forno = Forno()
    i2c = I2C()
    csv = Csv()
    ref_temp = 0
    internal_temp = 0
    response = 0
    room_temp = 0

    def __init__(self):
        thread_csv = Thread(target=self.register_log, args=())
        thread_csv.start()

        self.menu()

    def menu(self):
        while(True):

            if self.response == LIGAR_FORNO:
                message = Modbus.send_sys_on_off + b'\x01'
                self.uart.write(message,  8)
                data = self.uart.read()
                if data == b'\x01\x00\x00\x00':
                    print("Liga o Forno")

            elif self.response == DESLIGAR_FORNO:
                message = Modbus.send_sys_on_off + b'\x00'
                self.uart.write(message,  8)
                data = self.uart.read()
        
                if data == b'\x00\x00\x00\x00':
                    print("Desliga o Forno")
                    
            elif self.response == LIGAR_SISTEMA:
                self.turn_on_system()

                while self.response != DESLIGAR_SISTEMA:
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

                    time.sleep(1)
                self.turn_off_system()
            
            elif self.response == DESLIGAR_SISTEMA:
                self.turn_off_system()
                
            elif self.response == ALTERAR_MODO:
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
        self.read_internal_temp()
        self.read_room_temp()

    
    def read_ref_temp(self):
        message = Modbus.request_ref_temp

        self.uart.write(message,  7)
        data = self.uart.read()
        self.ref_temp = struct.unpack('f', data)[0]

        print("Temp ref:" ,self.ref_temp)

    
    def read_internal_temp(self):
        message = Modbus.request_internal_temp

        self.uart.write(message,  7)
        data = self.uart.read()
        self.internal_temp = struct.unpack('f', data)[0]

        print("Temp interna: ",self.internal_temp)
    
    def read_room_temp(self):
        self.room_temp = self.i2c.return_room_temp()
    
    def read_user_comands(self):
            print("Esperando comando...")
            self.uart.write(Modbus.read_user_commands,  7)

            response = self.uart.read()
            self.response = struct.unpack('i', response)[0]
            print("Comando do usuário: ", self.response)

    def turn_off_system(self):
        message = Modbus.send_sys_state + b'\x00'
        self.uart.write(message,  8)
        data = self.uart.read()
        self.set_ref_temp_room_temp(data)
        
    
    def set_ref_temp_room_temp(self, data):
        if data == b'\x00\x00\x00\x00':
            print("Sistema interrompido")
            if  self.internal_temp > self.room_temp:
                pid_atual = self.pid.pid_controle(self.room_temp, self.internal_temp)
                if(pid_atual < 0):
                        pid_atual *= -1
                        if(pid_atual < 40):
                            pid_atual = 40
                self.forno.cool_down(pid_atual)

            elif self.internal_temp < self.room_temp:
                self.forno.heat(self.pid.pid_controle(self.room_temp, self.internal_temp))
    
    def turn_on_system(self):
        message = Modbus.send_sys_state + b'\x01'
        self.uart.write(message,  8)
        data = self.uart.read()
        
        if data == b'\x01\x00\x00\x00':
            print("Sistema em funcionamento")
    
    def send_control_signal(self, signal):
        value = (round(signal)).to_bytes(4, 'little', signed=True)
        message = Modbus.send_control_signal + value
        self.uart.write(message, 11)
        self.uart.read()

    def debug_algorithm(self):
        i = 0
        pilha_tempo = [0, 60, 120, 240, 260, 300, 360, 420,480, 600]
        pilha_ref = [25, 38, 46, 54, 57, 61, 63 ,54, 33, 25]
        aux = 0
        while len(pilha_tempo) > 0 and self.response != ALTERAR_MODO:
            if(pilha_tempo[0] == i):
                pilha_tempo.pop(0)
                aux = pilha_ref.pop(0)
        
            pid_atual = self.pid.pid_controle(aux , self.internal_temp)

            self.send_control_signal(pid_atual)

            if(pid_atual < 0):
                pid_atual *= -1
                if(pid_atual < 40):
                    pid_atual = 40
                print("Esfriando")
                self.forno.cool_down(pid_atual)
            else: 
                print("Esquentando")   
                self.forno.heat(pid_atual)

            time.sleep(1)
            i = i + 1
        
    def register_log(self):
        header = ['Data/Hora', 'Temp Interna', 'Temp Ambiente', 'Temp Ref', 'Valor Acionamento' ]
        self.csv.write(header)

        while True:
            data = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            self.read_user_comands()
            self.read_temperatures()
            line = [data, self.internal_temp, self.room_temp , self.ref_temp, self.pid.sinal_de_controle]
            self.csv.write(line)
            time.sleep(1)


if __name__ == '__main__':
    Main()