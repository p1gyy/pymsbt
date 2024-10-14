import struct

class MSBTWriter:
    def __init__(self, msbt_file, filepath=None):
        """
        Writes to a file in the MSBT format using the specified MSBTFile

            msbt_file: A MSBTFile instance
            filepath (optional): The path to write the ouput file to, defaults to the same filepath as the msbt file.
        """
        self.msbt = msbt_file
        self.filepath = filepath or self.msbt.filepath
        self.stream = open(self.filepath, 'wb')

        self.label_index = 0
        self.sec_offset = 0

        self._write_sections()
        self._write_header()

    def _pack_into_stream(self, format, offset, *args):
        """Packs a struct format into the class' file stream"""
        packed = struct.pack(format, *args)
        self.stream.seek(offset)
        self.stream.write(packed)

    def _write_header(self):
        """Writes the MSBT header to the file"""
        header = struct.pack(
            '<8s H H H H H I 10s',
            self.msbt.header.magic.encode('ascii'), #8s
            self.msbt.header.byte_order, # H
            0, # H
            self.msbt.header.version, #H
            self.msbt.header.section_count, #H
            0, # H
            self.stream.tell(), #I - file size
            b'\x00' * 10 # 10s
        )
        self.stream.seek(0)
        self.stream.write(header)

    def _fill_bytes(self, offset, remainder):
        """Fills a section of bytes with 0xAB to allign by 16 bytes, leaving a padding of 3 0x00 bytes"""

        #calculate next offset to allign by 16
        next_offset = offset
        while True:
            if next_offset % 16 == 0:
                break
            else:
                next_offset += 1

        #fill with filler bytes until next section
        fill_length = next_offset - offset
        self.stream.seek(self.sec_offset)
        padding = 0
        for i in range(3 - remainder):
            # write padding of 3 0x00 bytes if they don't overlap onto the next section
            if not (self.stream.tell() > next_offset):
                self.stream.write(b'\x00')
                padding += 1
            else:
                return # end early if they do overlap to the next section
        self.stream.write(b'\xAB' * (fill_length - padding))

    def _calculate_table_size(self, sec_start_offset, end_offset):
        table_size = (end_offset + 3) - (sec_start_offset + 16) # end offset + 3(padding) - section start offset + 16(header)
        total_offset = sec_start_offset + 16 + table_size # total offset of entire file to end of section
        byte_remainder = total_offset % 16  # must allign to 16 bytes, remainder amt of bytes that aren't alligned to 16.

        if (byte_remainder <= 3):
            return (table_size - byte_remainder), byte_remainder
        elif (byte_remainder >= 13):
            byte_remainder_sub = (16 - byte_remainder)
            return (table_size) - byte_remainder_sub, 0
        else:
            return table_size, 0

    def _write_sections(self):
        """Writes the MSBT sections to the file"""
        offset = 0x20
        for i in range(self.msbt.header.section_count):
            section = self.msbt.sections[i]
            table_size = section.table_size
            signature = section.signature

            self.next_section_offset = offset + (table_size + 16 + (16 - (table_size % 16)) % 16)
            if signature == "LBL1":
                print("Writing Labels section...")

                self._write_labels_section(offset)
            #elif signature == "ATR1":
            #    print("Writing Attributes section...")
            #
            #    self.write_attributes_section(offset, table_size)
            #    self._fill_bytes(self.sec_offset, next_section_offset)
            elif signature == "TXT2":
                print("Writing Text section...")

                self._write_text_section(offset)
            else:
                print(f"Unknown section: {signature}")

                # write copied bytes for unsupported sections
                self.stream.seek(offset)
                self.stream.write(section.bytes)

            # Move to the next section (aligned to 16 bytes)
            offset = self.next_section_offset


    # LABELS
    def _write_labels_section(self, section_offset):
        """Writes the MSBT LBL1 section to the file"""
        # Section starts after the 16-byte header
        offset = section_offset + 16
        # Get the number of entries in the offset table
        self._pack_into_stream("<I", offset, self.msbt.LBL1.offset_count)

        offset += 4
        offset_lbl = 0

        for i in range(self.msbt.LBL1.offset_count):
            str_count, str_offset = self.msbt.LBL1.offset_table[i]
            self._pack_into_stream("<II", offset, str_count, str_offset)
            offset += 8

            #print(f"Wrote Label {i}: StringCount={str_count}, StringOffset={str_offset}")

            self.sec_offset = self._write_label_string(section_offset + 16 + str_offset, str_count)

        #calculate table size and create header
        table_size, r = self._calculate_table_size(section_offset, self.sec_offset)
        self._pack_into_stream("<4sI", section_offset, b'LBL1', table_size)

        self._fill_bytes(self.sec_offset, r)

    def _write_label_string(self, label_offset, string_count):
        """Writes the LBL1 label strings to the file"""
        offset = label_offset
        for i in range(string_count):
            label = self.msbt.LBL1.labels[self.label_index]
            # Get the length of the string
            str_len = len(label.data)
            self._pack_into_stream("<B", offset, str_len)
            offset += 1 
            
            # write the null-terminated string
            self._pack_into_stream(f'<{str_len}s', offset, label.data.encode('ascii'))
            offset += str_len

            index = label.string_index
            #index = int.from_bytes(index, byteorder='little')
            self._pack_into_stream(f'<I', offset, index) #write index
            offset += 4 # move past index

            self.label_index += 1
        return offset - 3
    

    ## TEXT
    def _write_text_section(self, section_offset):
        """Writes the MSBT TXT2 section to the file"""
        offset = section_offset + 20 # skip past header and to-be-written offset count
        offset_count = self.msbt.TXT2.offset_count
        txt_offsets = []

        offset += 4 * offset_count # move past offsets to write texts
        for i in range(offset_count):
            txt_offsets.append(offset - (section_offset + 16))
            self._write_text_string(offset, i)
            offset = self.sec_offset + 2

        #after finished writing texts, create offsets
        offset = section_offset + 16 # skip section header

        self._pack_into_stream("<I", offset, offset_count)
        offset += 4

        print(self.msbt.TXT2.offset_table)
        print(txt_offsets)

        # write each string in the text section
        for i in range(offset_count):
            text_offset = txt_offsets[i]
            self._pack_into_stream("<I", offset, text_offset)
            offset += 4

        #calculate table size and create header
        table_size, r = self._calculate_table_size(section_offset, self.sec_offset)
        print(table_size, r)
        self._pack_into_stream("<4sI", section_offset, b'TXT2', table_size)

        self._fill_bytes(self.sec_offset, r)

    def _write_text_string(self, text_offset, index):
        """Writes the TXT2 text strings to the file, writing text commands if necessary"""
        components = self.msbt.TXT2.texts[index]
        offset = text_offset
        for component in components:

            if component.type == 'command':
                command = component.data
                offset = self._write_text_command(offset, command)
                self.sec_offset = offset
                continue

            for char in component.data:
                self._pack_into_stream("<H", offset, ord(char))
                offset += 2
            self._pack_into_stream("<H", offset, 0x0000)

            self.sec_offset = offset

    def _write_text_command(self, start_offset, command):
        """Writes a text command to the file"""
        offset = start_offset
        
        self._pack_into_stream(
            '<HHHH',
            offset,
            int(command.magic, 16),
            command.group,
            command.type,
            command.data_size
        )
        offset += 8
        if command.data:
            data = command.data.replace('0x', '')
            self._pack_into_stream(f'<{command.data_size}s', offset, bytes.fromhex(data))
        offset += command.data_size
        return offset

    
    ## ATTRIBUTES
    #def write_attributes_section(self, section_offset, table_size):
    #    offset = section_offset + 16  # skip section header
    #
    #    attr_count, attr_data_size = self.msbt.attr_header_data
    #    self._pack_into_stream("<II", offset, attr_count, attr_data_size)
    #    offset += 8
        
        #for i in range(attr_count):
        #    # Read each attribute entry (4-byte offset from beginning)
        #    attr_offset, = struct.unpack_from("<I", self.data, offset)
        #    self.attributes.append(attr_offset)
        #    offset += 4