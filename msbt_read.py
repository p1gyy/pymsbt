import struct
from classes import *

LITTLE_ENDIAN = 0xFFFE
BIG_ENDIAN = 0xFEFF

class MSBTFile:
    def __init__(self, filepath):
        self.filepath = filepath

        # load file
        with open(filepath, 'rb') as f:
            self.data = f.read()

        # initialize class attributes
        self.header = MSBTHeader(self.data)
        self.sections = []

        self.LBL1 = None
        self.ATR1 = None
        self.TXT2 = None
        
        self.attributes = []

        # start the process by parsing sections
        self.parse_sections()

    def parse_sections(self):
        offset = 0x20 # start after msbt header

        for _ in range(self.header.section_count):
            # section header contains signature and table size
            section = MSBTSection(self.data, offset)
            self.sections.append(section)

            # Labels
            if section.signature == "LBL1":
                print("Parsing Labels section...")
                self.LBL1 = LBL1Section(self.data, offset, section.table_size)

            # Attributes
            elif section.signature == "ATR1":
                print("Parsing Attributes section...")
                self.parse_attributes_section(offset, section.table_size)

            # Text
            elif section.signature == "TXT2":
                print("Parsing Text section...")
                self.TXT2 = TXT2Section(self.data, offset, section.table_size)

            else:
                raise KeyError(f"Unknown section: {section.signature}")
            
            # move to next section (aligned to 16 bytes)
            offset += (section.table_size + 16 + (16 - (section.table_size % 16)) % 16) 
    
    def parse_attributes_section(self, section_offset, table_size):
        offset = section_offset + 16 # skip ATR1 section header

        attr_header_data = struct.unpack_from("<II", self.data, offset)
        attr_count, attr_data_size = attr_header_data
    
        offset += 8
        
        for i in range(attr_count):
            # read each attribute entry (4b offset from beginning)
            attr_offset, = struct.unpack_from("<I", self.data, offset)
            print(attr_offset)
            self.attributes.append(attr_offset)
            offset += 4