import usb.core
import usb.util
from ctypes import *
import sys

class command_block_wrapper(LittleEndianStructure):
    _pack_ = 1
    _fields_ = [('dCBWSignature', c_uint32),
                ('dCBWTag', c_uint32),
                ('dCBWDataTransferLength', c_uint32),
                ('bCWDFlags', c_uint8),
                ('bCBWLUN', c_uint8),
                ('bCBWCBLength', c_uint8),
                ('CBWCB', c_uint8 * 16),
    ]

    def encode(self):
        return string_at(addressof(self), sizeof(self))

    def decode(self, data):
        memmove(addressof(self), data, sizeof(self))
        return len(data)

VENDOR_ID = 0x10c4
PRODUCT_ID = 0x85ed
TAG = 0x00000000

dev = usb.core.find(custom_match = lambda d: d.idProduct==PRODUCT_ID and d.idVendor==VENDOR_ID)

if dev.is_kernel_driver_active(0):
  reattach = True
  dev.detach_kernel_driver(0)
dev.set_configuration()

epaddr_in  = dev[0].interfaces()[0].endpoints()[0].bEndpointAddress
epaddr_out = dev[0].interfaces()[0].endpoints()[1].bEndpointAddress

#print(dev)
#print('Endpoint addr IN: ', epaddr_in)
#print('Endpoint addr OUT:', epaddr_out)

# Etape 1 Inquiry. On demande le VendorId, et le ProductId
cbw = command_block_wrapper()
cbw.dCBWSignature = 0x43425355
cbw.dCBWTag=TAG
cbw.dCBWDataTransferLength=0x00000024
cbw.bCWDFlags=0x80
cbw.bCBWLun=0x00
cbw.bCBWCBLength=0x06
cbw.CBWCB = 0x12, 0, 0, 0, 0x24, 0

mycmd =  cbw.encode()
num = dev.write(epaddr_out,mycmd, 32)

buff = dev.read(epaddr_in, 36)
#print('resultat VendorId ProductId: ', buff)
#print('conversion:', "-".join(hex(x) for x in buff))
#print('conversion:', "".join(chr(x) for x in buff[8:]))
buff = dev.read(epaddr_in, 13)
#print('resultat VendorId ProductId: ', buff)
#print('conversion:', "-".join(hex(x) for x in buff))

# Etape 1 Inquiry. On demande le Serial Number
TAG = TAG + 1
cbw = command_block_wrapper()
cbw.dCBWSignature = 0x43425355
cbw.dCBWTag=TAG
cbw.dCBWDataTransferLength=0x000000ff
cbw.bCWDFlags=0x80
cbw.bCBWLun=0x00
cbw.bCBWCBLength=0x06
cbw.CBWCB = 0x12, 1, 0x80, 0, 0xff, 0

mycmd =  cbw.encode()
num = dev.write(epaddr_out,mycmd, 32)

buff = dev.read(epaddr_in, 36)
#print('resultat Serial Number: ', buff)
#print('conversion:', "-".join(hex(x) for x in buff))
#print('conversion:', "".join(chr(x) for x in buff))
buff = dev.read(epaddr_in, 13)
#print('resultat Serial Number: ', buff)
#print('conversion:', "-".join(hex(x) for x in buff))

# Etape 3 Read (6). On demande les données
iter=0
exit_loop = False
while True:
  TAG = TAG + 1
  cbw = command_block_wrapper()
  cbw.dCBWSignature = 0x43425355
  cbw.dCBWTag=TAG
  cbw.dCBWDataTransferLength=0x00000100
  cbw.bCWDFlags=0x80
  cbw.bCBWLun=0x00
  cbw.bCBWCBLength=0x10
  cbw.CBWCB = 0x08, 0, iter, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  iter = iter + 1
  
  mycmd =  cbw.encode()
  num = dev.write(epaddr_out,mycmd, 32)
  
  buff = dev.read(epaddr_in, 256)
  #print('resultat DATA: ', buff)
  #print('conversion:', "-".join(hex(x) for x in buff))
  arr = [buff[i:i + 8] for i in range(0, len(buff), 8)]
  #print(arr)
  for i in range(32):
    if arr[i][0] == 255:
      exit_loop = True
      break
    print("20{:2x}-{:02x}-{:02x} {:02x}:{:02x} {:x}{:02x}"\
      .format(arr[i][2], arr[i][3], arr[i][4], arr[i][5], arr[i][6], arr[i][0], arr[i][1]), end='')
    context = ""
    if arr[i][7] == 0x3:
        context = 0x2
    if arr[i][7] == 0x2:
        context = 0x1
    if arr[i][7] == 0x4:
        context = 0x0
    if context != '':
      print(" {:x}".format(context))
    else:
      print("")
  buff = dev.read(epaddr_in, 13)
  if exit_loop:
    break
  #print('resultat DATA: ', buff)
  #print('conversion:', "-".join(hex(x) for x in buff))
