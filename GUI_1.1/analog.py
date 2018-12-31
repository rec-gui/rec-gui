'''

Analog processing
Eye reading using analog reader
'''
from daqflex import USB_1608G
from constants import EyeCoilChannelId
DAQ_MCC_AD_RANGE = 20
DAQ_MCC_MIN_AD_RANGE = -10

class Usb1608G(USB_1608G):
    id_product = 0x134

class Analog(object):
    def __init__(self):
        self.dev = Usb1608G()
        self.dev.send_message("DIO{0}:DIR=IN")
        for i in range(EyeCoilChannelId.C16 + 1):
            # Set the channel mode to Single ended
            self.dev.send_message("AI{%d}:CHMODE=SE" %i)
            # Set the channel range to BIP10V
            self.dev.send_message("AI{%d}:RANGE=BIP10V" %i)

    def get_channel_analog_value(self, channel):
        '''
        Get the analog channel values
        :param channel:
        :return:
        '''
        resp_value = self.dev.send_message("?AI{%d}:VALUE" %channel)
        value = int(resp_value.split('=')[1])

        voltage = (float(value) / (pow(2, 16) - 1)) * DAQ_MCC_AD_RANGE
        analog_value = voltage + float(DAQ_MCC_MIN_AD_RANGE)
        return analog_value

    def read_digital_bit(self):
        '''
        Read the digital bit
        :return:
        '''
        resp = self.dev.send_message("?DIO{0}:VALUE")
        return resp
