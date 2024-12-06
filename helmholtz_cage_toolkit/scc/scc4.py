"""
Simple Command Codec - iteration 4 (SCC4)

Code implementation to facilitate command and message serialization
over a point-to-point TCP/IP connection.

Author: Johan Monster


SSC4 comes with seven packet types. Two of these, the m_packet and x_packet are
best suited for general-purpose, non-time-critical applications. The other
packets are more specialized and designed with a specific purpose in mind, such
as reduction of overhead.


Packet types in SSC4:

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

Telemetry packet    t_packet    Packet containing telemetry in the form of many
                                measured parameters. Mainly used to get as much
                                useful data from the server to a client in a
                                single package. Contains a 20 B UNIX timestamp,
                                commanded step index, and tri-axial values of
                                Im, Bm, and Bc.

B-sample packet     b_packet    Packet containing a single measurement of the
                                triaxial magnetometer. Contains a 20 B UNIX
                                timestamp and 16 B signed float value in nT for
                                each axis. Preferred over t_packet if only Bm
                                data is needed and speed is critical:
                                Encoding + decoding b_packet:   5.55 us
                                Encoding + decoding t_packet:  18.75 us

                                Full in-the-loop test on 03-02-2024:
                                1E5 b-packets exchanged + processed: 57.6 us/p
                                1E5 t-packets exchanged + processed: 81.1 us/p
                                Conclusion: the additional encoding, decoding,
                                and server-side processing of t-packets result
                                in an absolute average overhead of 23.5 us per
                                package compared to b-packets.

Execution packet    x_packet    Packets meant for sending commands, taking
                                a <str> command name, and then any number of
                                arguments. The scc keeps track of the type
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
encoding and decoding functions in the scc automatically take care of these,
and the packet_type() function can be used on an encoded packet to find its
type.

None of the implemented functions allow you to manually set the type_id of the
packet, and this is to force a degree of consistency across implementations.
Users desiring additional functionality are advised to subclass SCC instead.
"""


packet_size = 256   # Referable packet length for buffer size configuration
_pad = "#"          # Packet padding character (cannot be @)
# _xps = "@"          # (now hardcoded!) Internal separator used for x-packets


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



def encode_bpacket(tm, Bm):
    """ Encodes a b_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Optimization:
    3750 ns/encode (FX-8350)
         ns/encode (Raspberry Pi 4)
    """
    return "b{:0<20.20}{:0<16.16}{:0<16.16}{:0<16.16}{}".format(
        str(tm),
        str(Bm[0]),
        str(Bm[1]),
        str(Bm[2]),
        _pad*187).encode()

def decode_bpacket(b_packet):
    """ Decodes a b_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Efficiency by virtue of the KISS principle:
    1780 ns/decode (FX-8350)
         ns/encode (Raspberry Pi 4)
    """
    b_decoded = b_packet.decode()
    return [
        float(b_decoded[1:21]),
        float(b_decoded[21:37]),
        float(b_decoded[37:53]),
        float(b_decoded[53:69])]



def encode_cpacket(Bc):
    """ Encodes a c_packet, which has the following anatomy:
    c (1 B)    Bc_X (16 B)    Bc_Y (16 B)    Bc_Z (16 B)

    Optimization:
    2750 ns/encode (FX-8350)
         ns/encode (Raspberry Pi 4)
    """
    return "c{:0<16.16}{:0<16.16}{:0<16.16}{}".format(
        str(Bc[0]),
        str(Bc[1]),
        str(Bc[2]),
        _pad*207).encode()

def decode_cpacket(c_packet):
    """ Decodes a c_packet, which has the following anatomy:
    c (1 B)    Bc_X (16 B)    Bc_Y (16 B)    Bc_Z (16 B)

    Efficiency by virtue of the KISS principle:
    1160 ns/decode (FX-8350)
         ns/encode (Raspberry Pi 4)
    """
    c_decoded = c_packet.decode()
    return [
        float(c_decoded[1:17]),
        float(c_decoded[17:33]),
        float(c_decoded[33:49])]



def encode_epacket(msg: str):
    """ Encodes an e_packet, which has the following anatomy:
    e (1 B)    msg (n B)

    Optimization:
    550 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    return ("e"+msg[:255]+_pad*(packet_size-len(msg)-1)).encode()

def decode_epacket(e_packet):
    """ Encodes an e_packet, which has the following anatomy:
    e (1 B)    msg (n B)

    Optimization:
    500 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    # return e_packet.decode()[1:].rstrip(_pad)
    e_packet_decoded = e_packet.decode()
    return e_packet_decoded[1:e_packet_decoded.find(_pad)]


def encode_mpacket(msg: str):
    """ Encodes an m_packet, which has the following anatomy:
    m (1 B)    msg (n B)

    The allowed length of msg is equal to packet_size-1

    Optimization:
    480 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    return ("m"+msg[:255]+_pad*(packet_size-len(msg)-1)).encode()

def decode_mpacket(m_packet):
    """ Encodes an m_packet, which has the following anatomy:
    m (1 B)    msg (n B)

    The allowed length of msg is equal to packet_size-1

    Optimization:
    400 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    return m_packet.decode()[1:].rstrip(_pad)



def encode_spacket(
    i_seg: int,
    n_seg: int,
    t_seg: float,
    Bx_seg: float,
    By_seg: float,
    Bz_seg: float):
    """ Encodes an s_packet, which has the following anatomy:
    s (1 B)    segment number (32 B)    number of segments (32 B)
        segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    Optimization:
    4160 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    return "s{:0>32.32}{:0>32.32}{:0<20.20}{:0<16.16}{:0<16.16}{:0<16.16}{}".format(
        str(i_seg),
        str(n_seg),
        str(t_seg),
        str(Bx_seg),
        str(By_seg),
        str(Bz_seg),
        _pad*123).encode()

def decode_spacket(s_packet):
    """ Decodes an s_packet, which has the following anatomy:
    s (1 B)    segment number (32 B)    number of segments (32 B)
        segment_time (20 B)    B_X (16 B)    B_Y (16 B)    B_Z (16 B)

    to segment values.

    Optimization:
    2280 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    s_decoded = s_packet.decode()
    return [
        int(float(s_decoded[1:33])),
        int(float(s_decoded[33:65])),
        float(s_decoded[65:85]),
        float(s_decoded[85:101]),
        float(s_decoded[101:117]),
        float(s_decoded[117:133])
    ]



def encode_tpacket(tm, i_step, Im, Bm, Bc):
    """ Encodes a t_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    i_step (32 B)    Im (3x12 B)
               Bm (3x16 B)         Bc (3x16 B)      padding (71 B)
    Optimization:
    12000 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    output = [str(tm), str(i_step), ]
    for par in (Im, Bm, Bc):
        output += [str(par[0]), str(par[1]), str(par[2])]
    return ("t{:0<20.20}"+"{:0>32.32}"+"{:0<12.12}"*3+"{:0<16.16}"*6+"#"*71
            ).format(*output).encode()


def decode_tpacket(t_packet):
    """ Decodes a t_packet, which has the following anatomy:
    b (1 B)    UNIX_time (20 B)    i_step (32 B)    Im (3x12 B)
               Bm (3x16 B)         Bc (3x16 B)      padding (71 B)
    Optimization:
    4450 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    t_decoded = t_packet.decode()
    return float(t_decoded[1:21]), \
        int(t_decoded[21:53]), \
        [
            float(t_decoded[53:65]),        # \
            float(t_decoded[65:77]),        # Im
            float(t_decoded[77:89]),        # /
        ], [
            float(t_decoded[89:105]),        # \
            float(t_decoded[105:121]),        # Bm
            float(t_decoded[121:137]),       # /
        ], [
            float(t_decoded[137:153]),      # \
            float(t_decoded[153:169]),      # Bc
            float(t_decoded[169:185]),      # /
        ]



def encode_xpacket(cmd: str, *args):
    """ Encodes an x_packet, which has the following anatomy:
    x (1 B)    cmd (32 B)    n_args(6 B)    type_id , arg (1+23 B each)

    The tail of an x_packet consists of n_args segments. Each starts with
    an arg_type_id ('s', 'i', 'f', 'b' for string, integer, float, and
    boolean respectively), followed by 23 bytes of encoded value.

    Unoptimized as of 25-01-2024:
    ~10000-20000 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """
    recognized_types = (int, float, str, bool)

    n_args = len(args)
    n_correct_type = sum([type(arg) in recognized_types for arg in args])

    if n_correct_type != n_args:
        raise TypeError(
            f"encode_xpacket() received {n_args - n_correct_type} argument(s) of incorrect type! (must be str, int, float, or bool)")

    xpacket_unencoded = "x{:@>32}{:0>6}".format(cmd, n_args)

    for arg in args:
        if type(arg) == float:
            xpacket_unencoded += "f{:0<23}".format(round(arg, 8))
        elif type(arg) == int:
            xpacket_unencoded += "i" + ("{:@>23}".format(arg))[:23]
        elif type(arg) == bool:
            if arg is True:
                xpacket_unencoded += "b" + "{:1>23}".format(1)
            else:
                xpacket_unencoded += "b" + "{:0>23}".format(0)
        elif type(arg) == str:
            xpacket_unencoded += "s{:@>23}".format(arg[:23])

    if len(xpacket_unencoded) > packet_size:
        raise AssertionError(f"Total packet length exceeds 256 B ({len(xpacket_unencoded)} B)!")
    else:
        xpacket_unencoded += "{}".format(_pad*(packet_size-len(xpacket_unencoded)))
        return xpacket_unencoded.encode()

def decode_xpacket(x_packet):
    """ Decodes a c_packet, which has the following anatomy:
    x (1 B)    cmd (32 B)    n_args(6 B)    type_id , arg (1+23 B each)

    Unoptimized as of 15-01-2024.
    ~5000-11000 ns/encode (FX-8350)
     ns/encode (Raspberry Pi 4)
    """

    xpacket_decoded = x_packet.decode().rstrip(_pad)

    cmd_name = xpacket_decoded[1:33].strip("@")
    n_args = int(xpacket_decoded[33:39])

    # print("cmd_name:", cmd_name, "n_args:", n_args)

    args = []
    for i_seg in range(n_args):
        seg = xpacket_decoded[39 + 24 * i_seg:39 + 24 * (i_seg + 1)]
        # print("[DEBUG]", i_seg, seg, end="  ->  ")

        if seg[0] == "f":
            args.append(float(seg[1:]))
        elif seg[0] == "i":
            args.append(int(seg[1:].strip("@")))
        elif seg[0] == "b":
            args.append(bool(int(seg[1])))
        elif seg[0] == "s":
            args.append(seg[1:].strip("@"))
        else:
            raise ValueError(
                f"decode_xpacket(): Encountered uninterpretable type_id '{seg[0]}' in segment {i_seg}: {seg}")

        # print(f"{args[i_seg]} ({type(args[i_seg])})")

    return cmd_name, args
