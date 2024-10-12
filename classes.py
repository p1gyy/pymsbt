import struct

class MSBTHeader:
    def __init__(self, data):

        # get the msbt file header
        self.magic = data[0:8].decode('ascii')
        self.byte_order = struct.unpack("<H", data[0x8:0x0A])[0]
        self.version = struct.unpack("<H", data[0x0C:0x0E])[0]
        self.section_count = struct.unpack("<H", data[0x0E:0x10])[0]
        self.file_size = struct.unpack("<I", data[0x12:0x16])[0]

        # magic must be MsgStdBn
        if self.magic != "MsgStdBn":
            raise ValueError(f"Invalid MSBT file magic: {self.magic}")
        
        print(f"MSBT Header: Magic={self.magic}, Byte order={self.byte_order} Version={self.version}, SectionCount={self.section_count}, FileSize={self.file_size}")

    def __str__(self):
        return (f"Magic: {self.magic}, Byte Order: {self.byte_order}, Version: {self.version}, Section Count: {self.section_count}, File Size: {self.file_size}")

class MSBTSection:
    # msbt section header containing signature (magic) and table size
    def __init__(self, data, offset):
        self.encoded_signature, self.table_size = struct.unpack_from("<4sI", data, offset)
        self.signature = self.encoded_signature.decode('ascii')

    def __str__(self):
        return f"MSBT Section:  Signature: {self.signature}  Table Size: {self.table_size}"

class LBL1Section:
    def __init__(self, data, section_offset, table_size):
        self.magic = 'LBL1'
        self.offset_count = 0
        self.offset_table = []
        self.labels = []

        # starts after the section header
        offset = section_offset + 16

        # get number of entries in the offset table
        self.offset_count, = struct.unpack_from("<I", data, offset)

        offset += 4

        for i in range(self.offset_count):
            # 4byte string count and 4byte string offset
            str_count, str_offset = struct.unpack_from("<II", data, offset)
            offset += 8

            self.offset_table.append((str_count, str_offset))
            #print(f"Label {i}: StringCount={str_count}, StringOffset={str_offset}")
            
            # parse actual strings
            self.parse_label_strings(data, section_offset + 16 + str_offset, str_count)

    def parse_label_strings(self, data, label_offset, string_count):
        offset = label_offset
        for _ in range(string_count):

            # get length of the string
            str_len = data[offset]
            offset += 1
            
            # read the label string
            label = data[offset:offset + str_len].decode('ascii')
            offset += str_len

            index = data[offset:offset + 4]
            offset += 4

            # create new MSBTLabel and add to list
            self.labels.append(MSBTLabel(label, str_len, index))

    def __str__(self):
        return (f"Magic: {self.magic}, Offset Count: {self.offset_count}, Labels: {[str(label) for label in self.labels]}, ")

class TXT2Section:
    def __init__(self, data, section_offset, table_size):
        self.magic = 'TXT2'
        self.offset_count = 0
        self.offset_table = []
        self.texts = []

        # start after the 16-byte header
        offset = section_offset + 16
        self.offset_count, = struct.unpack_from("<I", data, offset)
        offset += 4  # Move past the text count
        
        # read each string in the text section
        for i in range(self.offset_count):
            text_offset, = struct.unpack_from("<I", data, offset)
            self.offset_table.append(text_offset)
            offset += 4
            self.parse_text_string(data, section_offset + 16 + text_offset)
    
    def parse_text_string(self, data, text_offset):
        # text and text commands are represented as components with 'type' and 'data'
        components = []
        offset = text_offset
        text = ""

        while True:
            # text command parsing
            if data[offset] == 0x0E or data[offset] == 0xf: #0x0E and 0fx are tag headers
                text_command = TextCommand(data, offset)
                if len(text) > 0:
                    # if there's already data in text variable, create component before adding text command
                    components.append({'type': 'text', 'data': text})
                    text = ""
                components.append({'type': 'command', 'data': text_command})
                offset = text_command.end_offset
                continue

            char = struct.unpack_from("<H", data, offset)[0]
            if char == 0x0000:
                # end text parsing
                break

            text += chr(char)
            offset += 2
        
        #after parsing finished, create component and add to component list
        if len(text) > 0:
            components.append({'type': 'text', 'data': text})
            self.texts.append(components)

    def __str__(self):
        return (f"Offset Count: {self.offset_count}, Texts: {self.texts}, ")

class MSBTLabel:
    def __init__(self, value, length, str_index):
        self.data = value
        self.length = length
        self.string_index = str_index.hex()

    def __str__(self):
        return (f"data: {self.data}, length: {self.length}, string_index: {self.string_index}")
    def __repr__(self): # this needs to be here for print to work if in a list 
        return self.__str__()

#class TextComponent: | not used anymore
#    def __init__(self, type, data):
#        self.type = type
#        self.data = data
#
#    def __str__(self):
#        return (f"Type: {self.type}, Data: {str(self.data)}")
#    def __repr__(self):
#        return self.__str__()

class TextCommand:
    def __init__(self, msbt_data, start_offset):
        self.start_offset = start_offset
        offset = start_offset
        
        unpacked = struct.unpack_from('<HHHH', msbt_data, offset)

        self.magic = hex(unpacked[0]) #0xe of 0xf for data-less tags
        self.group = unpacked[1]
        self.type = unpacked[2]
        self.data_size = unpacked[3]
        offset += 8

        self.data, = struct.unpack_from(f'<{self.data_size}s', msbt_data, offset)

        if self.data: # to deal with empty text commands
            self.data = '0x' + self.data.hex()
        else:
            self.data = None

        offset += self.data_size
        self.end_offset = offset # so the text parser would know the offset after the tag

    def __str__(self):
        return (f"Type: {self.group}:{self.type}, Size: {self.data_size}, Data: {self.data})")

    def __repr__(self): # this needs to be here for print to work if in a list 
        return self.__str__()