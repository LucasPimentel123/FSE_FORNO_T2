import serial
import time

from Utils.Crc import calcula_CRC

class Uart:
    isConected = False 

    def __init__(self):
        self.conect()

    def conect(self):
        self.serial = serial.Serial("/dev/serial0", 9600)

        if(self.serial.is_open()):
            self.isConected = True
            print('Conexão UART estabelecida...')


    def envia(self):
        if (self.isConected):
            m1 = b'\x01' + b'\x23' + b'\xC1' + bytes([6, 6, 6, 3])
            m2 = calcula_CRC(m1, 8).to_bytes(2, 'little')
            msg = m1 + m2
            self.serial.write(msg)
            # print('Mensagem enviada: {}'.format(msg))
        else:
            self.conect()