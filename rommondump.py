#!/usr/bin/env python3
import argparse
import logging
import serial
import io

class CiscoSerial:
    def __init__(self, uart, baud=115200):
        self.uart = uart
        self.ser = serial.Serial(uart, baud, timeout=1, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, rtscts=0)
        self.sio = io.TextIOWrapper(io.BufferedRWPair(self.ser, self.ser), newline=None)
        logging.debug('Opened serial port successfully!')

    def flash_read(self, offset, length):
        self.sio.write('\r\n')
        self.sio.flush()

        while self.sio.readline():
            continue

        command_raw = 'dump -b 0x{:x} 0x{:x}\r\n'.format(offset, length)
        logging.debug('Sending command: {}'.format(command_raw))
        self.sio.write(command_raw)
        self.sio.flush()
        result = []

        while True:
            r = self.sio.readline().strip()
            if not r or 'dump' in r:
                continue

            logging.debug('Read: "{}"'.format(r))
            if 'rommon' in r:
                break

            result.append('{}\n'.format(r))

        return result

def _set_verbose(very):
    if very:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description='Read Cisco Router Flash')
    parser.add_argument('-u', '--uart', required=True, dest='uart',
            help='UART to open for communicating with rommon')
    parser.add_argument('-v', '--verbose', help='verbose output', action='store_true')
    parser.add_argument('-b', '--base', help='base address in EEPROM to read',
            type=lambda x: int(x, 0), required=False, default=0)
    parser.add_argument('-l', '--length', help='length to dump, in bytes',
            type=lambda x: int(x, 0), required=True)
    parser.add_argument('-o', '--output', help='output file for dump',
            required=True)
    args = parser.parse_args()

    _set_verbose(args.verbose)

    logging.info('Using serial port {}'.format(args.uart))

    ser = CiscoSerial(args.uart)

    logging.info('Dumping Flash from {} for {} bytes'.format(args.base, args.length))
    logging.info('Writing to file {}'.format(args.output))

    f = open(args.output, 'wt')

    max_block = 64 * 1024

    for i in range(args.base, args.base + args.length, max_block):
        byte_len = min(max_block, (args.base + args.length) - i)

        logging.debug('Dumping {} bytes from {}'.format(byte_len, i))
        raw_data = ser.flash_read(i, byte_len)
        f.writelines(raw_data)
        f.flush()

    f.close()


if __name__ == '__main__':
    main()

