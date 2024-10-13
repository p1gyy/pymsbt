import struct
from .classes import *

LITTLE_ENDIAN = 0xFFFE
BIG_ENDIAN = 0xFEFF

class MSBTFile:
    """
    A representation of a MSBT file.

        header: A MSBTHeader class that contains information about the file
        sections: A list of MSBTSections in the in the file

        LBL1: The LBL1Section if it exists in the file
        TXT2: The TXT2Section if it exists in the file
        ATR1: The ATR1Section if it exists in the file

        text_labels: A map between labels and texts that are found in the file.
    """
    def __init__(self, filepath):
        self.filepath = filepath

        # load file
        with open(filepath, 'rb') as f:
            self.data = f.read()

        # initialize class attributes
        self.header = MSBTHeader(self.data)
        self.sections = []

        self.LBL1 = None
        self.TXT2 = None
        self.ATR1 = None
        
        self.text_labels = {}

        #self.attributes = []

        # start the process by parsing sections
        self._parse_sections()

        # create label and text map
        for label in self.LBL1.labels:
            self.text_labels[label.data] = self.TXT2.texts[label.string_index]

    def _parse_sections(self):
        """Parses the MSBT file's sections such as LBL1 and TXT2. Ran automatically upon creation of a MSBTFile class"""
        offset = 0x20 # start after msbt header

        for _ in range(self.header.section_count):
            # section header contains signature and table size
            section = MSBTSection(self.data, offset)
            next_offset = offset + (section.table_size + 16 + (16 - (section.table_size % 16)) % 16) # store next section offset for later use

            # Labels
            if section.signature == "LBL1":
                print("Parsing Labels section...")
                self.LBL1 = LBL1Section(self.data, offset, section.table_size)

            # Attributes
            #elif section.signature == "ATR1":
            #    print("Parsing Attributes section...")
            #    self.parse_attributes_section(offset, section.table_size)

            # Text
            elif section.signature == "TXT2":
                print("Parsing Text section...")
                self.TXT2 = TXT2Section(self.data, offset, section.table_size)

            else:
                print(f"Unknown section: {section.signature}")
                section.storeBytes(self.data, offset, next_offset)

            self.sections.append(section)
            
            # move to next section (aligned to 16 bytes)
            offset = next_offset
    
    #def parse_attributes_section(self, section_offset, table_size):
    #    offset = section_offset + 16 # skip ATR1 section header
    #
    #    attr_header_data = struct.unpack_from("<II", self.data, offset)
    #    attr_count, attr_data_size = attr_header_data
    # 
    #    offset += 8
    #    
    #    for i in range(attr_count):
    #        # read each attribute entry (4b offset from beginning)
    #        attr_offset, = struct.unpack_from("<I", self.data, offset)
    #        print(attr_offset)
    #        self.attributes.append(attr_offset)
    #        offset += 4

    def get_text_index(self, lbl):
        """Returns a index in TXT2.texts that corresponds to the label"""
        label_obj = None
        for label in self.LBL1.labels:
            if label.data == lbl:
                label_obj = label
                break
        
        return label_obj.string_index
    
    def set_text(self, label, text):
        """Sets a text value in TXT2.texts that corresponds to the label."""
        index = self.get_text_index(label)
        self.TXT2.texts[index] = text

    def __str__(self):
        return f"""
header: {self.header}
sections: {self.sections}

LBL1: {self.LBL1}

TXT2: {self.TXT2}

ATR1: {self.ATR1}

    """