'''
Analog processing
Eye reading using analog reader
'''
from daqflex import USB_1608G

class Usb1608G(USB_1608G):
    id_product = 0x134

class DIO(object):
    def __init__(self):
        #self.dev = USB_1608G()
        self.dev = Usb1608G()


    def write_digital_bit(self, outbit):
        self.dev.send_message("DIO{0/0}:DIR=OUT")
        self.dev.send_message("DIO{0/0}:VALUE="+str(outbit))
        return

    def reward_on(self):
        self.dev.send_message("DIO{0}:DIR=OUT")
        self.dev.send_message("DIO{0}:VALUE=255")
        return

    def reward_off(self):
        self.dev.send_message("DIO{0}:DIR=OUT")
        self.dev.send_message("DIO{0}:VALUE=0")
        return

    def read_digital_bit(self):
        '''
        Read the digital bit
        :return:
        '''
        self.dev.send_message("?DIO{0}:DIR=IN")
        resp = self.dev.send_message("?DIO{0}:VALUE")
        return resp
