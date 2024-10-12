import struct

class MSBTWriter:
    def __init__(self, msbt_file, filepath):
        self.msbt = msbt_file
        self.filepath = filepath
        self.stream = open(filepath, 'wb')

        self.label_index = 0
        self.sec_offset = 0

        self.write_header()
        self.write_sections()

    def pack_into_stream(self, format, offset, *args):
        packed = struct.pack(format, *args)
        self.stream.seek(offset)
        self.stream.write(packed)

    def write_header(self):
        header = struct.pack(
            '<8s H H H H H I 10s',
            self.msbt.magic.encode('ascii'), #8s
            self.msbt.byte_order, # H
            0, # H
            self.msbt.version, #H
            self.msbt.section_count, #H
            0, # H
            self.msbt.file_size, #I
            b'\x00' * 10 # 10s
        )
        self.stream.write(header)

    def write_sections(self):
        offset = 0x20
        for i in range(self.msbt.section_count):
            section = self.msbt.sections[i]
            table_size = section['table_size']
            signature = section['signature']

            self.pack_into_stream("<4sI", offset, signature.encode('ascii'), table_size)

            next_section_offset = offset + (table_size + 16 + (16 - (table_size % 16)) % 16)
            if signature == "LBL1":
                print("Writing Labels section...")
                self.write_labels_section(offset, table_size)
            elif signature == "ATR1":
                print("Writing Attributes section...")
                self.write_attributes_section(offset, table_size)
            elif signature == "TXT2":
                print("Writing Text section...")
                self.write_text_section(offset, table_size)
            else:
                print(f"Unknown section: {signature}")

            #fill with filler bytes until next section
            fill_length = next_section_offset - self.sec_offset
            self.stream.seek(self.sec_offset)
            self.stream.write(b'\xAB' * fill_length)

            # Move to the next section (aligned to 16 bytes)
            offset = next_section_offset


    # LABELS
    def write_labels_section(self, section_offset, table_size):
        # Section starts after the 16-byte header
        offset = section_offset + 16
        # Get the number of entries in the offset table
        self.pack_into_stream("<I", offset, self.msbt.labels_stringcount)

        offset += 4
        offset_lbl = 0

        for i in range(self.msbt.labels_stringcount):
            str_count, str_offset = self.msbt.label_offsets[i]
            self.pack_into_stream("<II", offset, str_count, str_offset)
            offset += 8

            #print(f"Wrote Label {i}: StringCount={str_count}, StringOffset={str_offset}")

            self.sec_offset = self.write_label_string(section_offset + 16 + str_offset, str_count)

    def write_label_string(self, label_offset, string_count):
        offset = label_offset
        for i in range(string_count):
            label = self.msbt.labels[self.label_index]
            # Get the length of the string
            str_len = len(label)
            self.pack_into_stream("<B", offset, str_len)
            offset += 1  # Move past the length byte
            
            # write the null-terminated string
            self.pack_into_stream(f'<{str_len}s', offset, label.encode('ascii'))
            offset += str_len  # Move past the string

            index = self.msbt.label_indexes[self.label_index]
            index = int.from_bytes(index, byteorder='little')
            self.pack_into_stream(f'<I', offset, index) #write index
            offset += 4 # move past index

            self.label_index += 1
        return offset
    

    ## TEXT
    def write_text_section(self, section_offset, table_size):
        offset = section_offset + 16 # skip section header

        self.pack_into_stream("<I", offset, self.msbt.text_count)
        offset += 4  # Move past the text count
        
        # Now read each string in the text section
        for i in range(self.msbt.text_count):
            text_offset = self.msbt.text_offsets[i]
            self.pack_into_stream("<I", offset, text_offset)
            offset += 4
            self.write_text_string(section_offset + 16 + text_offset, i)

    def write_text_string(self, text_offset, index):
        text = self.msbt.texts[index]
        offset = text_offset
        for char in text:
            self.pack_into_stream("<H", offset, ord(char))
            offset += 2
        self.pack_into_stream("<H", offset, 0x0000)
        self.sec_offset = offset + 2

    
    ## ATTRIBUTES
    def write_attributes_section(self, section_offset, table_size):
        offset = section_offset + 16  # skip section header

        attr_count, attr_data_size = self.msbt.attr_header_data
        self.pack_into_stream("<II", offset, attr_count, attr_data_size)
        offset += 8
        
        #for i in range(attr_count):
        #    # Read each attribute entry (4-byte offset from beginning)
        #    attr_offset, = struct.unpack_from("<I", self.data, offset)
        #    self.attributes.append(attr_offset)
        #    offset += 4