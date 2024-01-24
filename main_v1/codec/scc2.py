"""
Simple Command Codec - iteration 2 (SCC2)

Code implementation to facilitate command and message serialization
over a point-to-point TCP/IP connection.

SSC2 comes with six packet types:

Message packet      m_packet    Packets meant for sending long <str> messages

Echo packet         e_packet    This packet type is identical to the message
                                packet, but it is meant to signal to the
                                receiving socket to echo the contents back.
                                This is mainly useful for troubleshooting the
                                TCP socket connection.

Control packet      c_packet    Packet meant to control the power supplies to
                                be set to a certain current output
                                proportional to a magnetic field strength.
                                Packet contains 3 signed <float> values in nT

B-sample packet     b_packet    Packet containing a single measurement of the
                                triaxial magnetometer. Contains a 20 B UNIX
                                timestamp and 16 B signed float value in nT
                                for each axis.

Execution packet    x_packet    Packets meant for sending commands, taking
                                a <str> command name, and then any number of
                                arguments. The codec keeps track of the type
                                of each argument, with the following types
                                currently supported: <str>, <int>, <float>,
                                <bool>.

B-schedule segment  s_packet    Packets containing a single line of a
                                B-schedule, which can be used to send a
                                complete B-schedule between client and server.
                                Consists of a type_id, a segment number, the
                                total number of segments in the schedule, the
                                segment's time, and three Bc values.


Each packet starts with a single character type_id, which can be used to
identify an incoming packet even if only a single byte has arrived. The
encoding and decoding functions in the codec automatically take care of these,
and the packet_type() function can be used on an encoded packet to find its
type.

None of the implemented functions allow you to manually set the type_id of the
packet, and this is to force a degree of consistency across implementations.
Users desiring additional functionality are advised to subclass SCC instead.
"""

class SCC:
    buffer_size = 256

    @staticmethod
    def packet_type(packet):
        """ Returns the first character of the packet, which is the type
        identifier.

        On optimizations:
        Previously, this function was implemented as:
            return packet.decode()[0]
        Whilst both implementations are similar in performance for short
        packets, the execution time of the current implementation does not
        grow with increasing packet size:

        Package size:               69 B     256 B    2048 B
        -------------------------------------------------------
        Old implementation:       175 ns    210 ns    512 ns
        Current implementation:   165 ns    165 ns    165 ns

        (n = 1E7, CPU = AMD FX-8350 @ 4.0 GHz)
        """
        return packet[0:1].decode()

    # @staticmethod
    # def encode_bpacket(Bm):
    #     """ Encodes a b_packet, which has the following anatomy:
    #     b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)
    #
    #     Efficiency by virtue of the KISS principle: ~6850 ns/encode (FX-8350)
    #     """
    #     return "b{:0<20}{:0<16}{:0<16}{:0<16}".format(
    #         round(float(Bm[0]), 8),
    #         round(float(Bm[1]), 8),
    #         round(float(Bm[2]), 8),
    #         round(float(Bm[3]), 8)).encode()

    @staticmethod
    def encode_bpacket(Bm):
        """ Encodes a b_packet, which has the following anatomy:
        b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

        Efficiency by virtue of the KISS principle: ~3700 ns/encode (FX-8350)
        """
        return "b{:0<20}{:0<16}{:0<16}{:0<16}".format(
            str(Bm[0])[:20],
            str(Bm[1])[:20],
            str(Bm[2])[:20],
            str(Bm[3])[:20]).encode()

    @staticmethod
    def decode_bpacket(b_packet):
        """ Decodes a b_packet, which has the following anatomy:
        b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

        Efficiency by virtue of the KISS principle: ~1750 ns/decode (FX-8350)
        """
        b_decoded = b_packet.decode()
        return [
            float(b_decoded[1:21]),
            float(b_decoded[21:37]),
            float(b_decoded[37:53]),
            float(b_decoded[53:69])]

    # @staticmethod
    # def encode_cpacket(Bc):
    #     """ Encodes a c_packet, which has the following anatomy:
    #     c (1 B)    Bc_X (16 B)    Bc_Y (16 B)    Bc_Z (16 B)
    #
    #     Efficiency by virtue of the KISS principle: ~4600 ns/encode (FX-8350)
    #     """
    #     return "c{:0<16}{:0<16}{:0<16}".format(
    #         round(float(Bc[0]), 8),
    #         round(float(Bc[1]), 8),
    #         round(float(Bc[2]), 8)).encode()

    @staticmethod
    def encode_cpacket(Bc):
        """ Encodes a c_packet, which has the following anatomy:
        c (1 B)    Bc_X (16 B)    Bc_Y (16 B)    Bc_Z (16 B)

        Efficiency by virtue of the KISS principle: ~2700 ns/encode (FX-8350)
        """
        return "c{:0<16}{:0<16}{:0<16}".format(
            str(Bc[0])[:16],
            str(Bc[1])[:16],
            str(Bc[2])[:16]).encode()


    @staticmethod
    def decode_cpacket(c_packet):
        """ Decodes a c_packet, which has the following anatomy:
        c (1 B)    Bc_X (16 B)    Bc_Y (16 B)    Bc_Z (16 B)

        Efficiency by virtue of the KISS principle: ~1060 ns/decode (FX-8350)
        """
        c_decoded = c_packet.decode()
        return [
            float(c_decoded[1:17]),
            float(c_decoded[17:33]),
            float(c_decoded[33:49])]

    @staticmethod
    def encode_mpacket(msg: str):
        """ Encodes an m_packet, which has the following anatomy:
        m (1 B)    msg (n B)

        The allowed length of msg is equal to BUFFER_SIZE-1

        Efficiency by virtue of the KISS principle: ~290 ns/encode (FX-8350)
        """
        return ("m"+msg).encode()

    @staticmethod
    def decode_mpacket(m_packet):
        """ Encodes an m_packet, which has the following anatomy:
        m (1 B)    msg (n B)

        The allowed length of msg is equal to BUFFER_SIZE-1

        Efficiency by virtue of the KISS principle: ~320 ns/decode (FX-8350)
        """
        return m_packet.decode()[1:]

    @staticmethod
    def encode_epacket(msg: str):
        """ Encodes an e_packet, which has the following anatomy:
        e (1 B)    msg (n B)
        """
        return ("e"+str(msg)).encode()

    @staticmethod
    def decode_epacket(e_packet):
        """ Encodes an e_packet, which has the following anatomy:
        e (1 B)    msg (n B)
        """
        return e_packet.decode()[1:]

    @staticmethod
    def encode_xpacket(cmd: str, *args):
        """ Encodes an x_packet, which has the following anatomy:
        x (1 B)    cmd (24 B)    n_args(8 B)    type_id , arg (1+23 B each)

        The tail of an x_packet consists of n_args segments. Each starts with
        an arg_type_id ('s', 'i', 'f', 'b' for string, integer, float, and
        boolean respectively), followed by 23 bytes of encoded value.

        Unoptimized as of 15-01-2024. ~10000-20000 ns/encode (FX-8350)
        """
        recognized_types = (int, float, str, bool)

        n_args = len(args)
        n_correct_type = sum([type(arg) in recognized_types for arg in args])

        if n_correct_type != n_args:
            raise TypeError(
                f"encode_xpacket() received {n_args - n_correct_type} argument(s) of incorrect type! (must be str, int, float, or bool)")

        xpacket_unencoded = "x{:#>23}{:0>8}".format(cmd, n_args)

        for arg in args:
            if type(arg) == float:
                xpacket_unencoded += "f{:0<23}".format(round(arg, 8))
            elif type(arg) == int:
                xpacket_unencoded += "i" + ("{:#>23}".format(arg))[:23]
            elif type(arg) == bool:
                if arg is True:
                    xpacket_unencoded += "b" + "{:1>23}".format(1)
                else:
                    xpacket_unencoded += "b" + "{:0>23}".format(0)
            elif type(arg) == str:
                xpacket_unencoded += "s{:#>23}".format(arg[:23])

        if len(xpacket_unencoded) > 256:    # TODO: Currently hardcoded, should be referenced from a config
            raise AssertionError(f"Total packet length exceeds 256 B ({len(xpacket_unencoded)} B)!")
        else:
            return xpacket_unencoded.encode()

    @staticmethod
    def decode_xpacket(x_packet):
        """ Decodes a c_packet, which has the following anatomy:
        x (1 B)    cmd (24 B)    args (24 B each)

        Unoptimized as of 15-01-2024. ~5000-10000 ns/decode (FX-8350)
        """

        xpacket_decoded = x_packet.decode()

        # print(xpacket_decoded[1:24])  # TODO: Remove debug comments once done testing
        # print(xpacket_decoded[24:32])
        cmd_name = xpacket_decoded[1:24].strip("#")
        n_args = int(xpacket_decoded[24:32])

        # print("cmd_name:", cmd_name, "n_args:", n_args)

        args = []
        for i_seg in range(n_args):
            seg = xpacket_decoded[32 + 24 * i_seg:32 + 24 * (i_seg + 1)]
            # print("[DEBUG]", i_seg, seg, end="  ->  ")

            if seg[0] == "f":
                args.append(float(seg[1:]))
            elif seg[0] == "i":
                args.append(int(seg[1:].strip("#")))
            elif seg[0] == "b":
                args.append(bool(int(seg[1])))
            elif seg[0] == "s":
                args.append(seg[1:].strip("#"))
            else:
                raise ValueError(
                    f"decode_xpacket(): Encountered uninterpretable type_id '{seg[0]}' in segment {i_seg}: {seg}")

            # print(f"{args[i_seg]} ({type(args[i_seg])})")

        return cmd_name, args


    @staticmethod
    def vals_to_segment(i_seg: int, n_seg: int, t_seg: float, Bc_seg: [float]):
        """Encodes engineering values to a segment string. ~1250 ns/encode"""
        return f"{i_seg} {n_seg} {t_seg} {Bc_seg[0]} {Bc_seg[1]} {Bc_seg[2]}"

    @staticmethod
    def segment_to_vals(segment: str):
        """Decodes a segment string into engineering values. ~1150 ns/encode"""
        i_seg, n_seg, t_seg, BcX, BcY, BcZ = segment.split(" ")
        return int(i_seg), int(n_seg), float(t_seg), [float(BcX), float(BcY), float(BcZ)]

    @staticmethod
    def encode_spacket_fromvals(i_seg: int, n_seg: int, t_seg: float, Bc_seg: [float]):
        """ Encodes an s_packet, which has the following anatomy:
        s (1 B)    segment number (32 B)    number of segments (32 B)
            segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

        Optimization: 2500 ns/encode (FX-8350)
        """
        return "s{:0>32}{:0>32}{:0<20}{:0<16}{:0<16}{:0<16}".format(
            str(i_seg)[:16],
            str(n_seg)[:16],
            str(t_seg)[:16],
            str(Bc_seg[0])[:16],
            str(Bc_seg[1])[:16],
            str(Bc_seg[2])[:16]).encode()

    # @staticmethod
    # def encode_spacket_fromsegment(segment):
    #     """ Encodes an s_packet, which has the following anatomy:
    #     s (1 B)    segment number (32 B)    number of segments (32 B)
    #         segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)
    #
    #     from a B-schedule segment
    #
    #     Important note: This function is optimized for B-schedule generators that
    #     already perform proper rounding on floats, ensuring that they do not
    #     exceed 16 characters when converted to a string. It throws away as many
    #     characters from the right as it needs to fit within 16 bytes. This means
    #     that for very large numbers, you may lose some precision at the bottom end.
    #
    #     Example: -1234567890.1234567890 (22 B) -> -1234567890.1234 (16 B)
    #
    #     This is deemed acceptable for the application for which it is intended, but
    #     users aiming to use this codec for other applications should take note.
    #
    #     Optimization: 1440 ns/encode (FX-8350)
    #     """
    #     split = segment.split(" ")
    #     return "s{:0>32}{:0>32}{:0<20}{:0<16}{:0<16}{:0<16}".format(
    #         split[0][:16],
    #         split[1][:16],
    #         split[2][:16],
    #         split[3][:16],
    #         split[4][:16],
    #         split[5][:16]).encode()

    @staticmethod
    def decode_spacket_tovals(s_packet):
        """ Decodes an s_packet, which has the following anatomy:
        s (1 B)    segment number (32 B)    number of segments (32 B)
            segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

        to engineering values.

        Optimization: 1900 ns/decode (FX-8350)
        """
        s_decoded = s_packet.decode()
        return [
            int(s_decoded[1:33]),
            int(s_decoded[33:65]),
            float(s_decoded[65:85]),
            [
                float(s_decoded[85:101]),
                float(s_decoded[101:117]),
                float(s_decoded[117:133])
            ]
        ]

    # @staticmethod
    # def decode_spacket_tosegment(s_packet):
    #     """ Decodes an s_packet, which has the following anatomy:
    #     s (1 B)    segment number (32 B)    number of segments (32 B)
    #         segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)
    #
    #     to a segment line.
    #     Optimization: 3400 ns/decode (FX-8350)
    #     """
    #     s_decoded = s_packet.decode()
    #     return f"{int(s_decoded[1:33])} " \
    #            f"{int(s_decoded[33:65])} " \
    #            f"{float(s_decoded[65:85])} " \
    #            f"{float(s_decoded[85:101])} " \
    #            f"{float(s_decoded[101:117])} " \
    #            f"{float(s_decoded[117:133])}"