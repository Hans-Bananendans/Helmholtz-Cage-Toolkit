"""This file contains a convenient set of benchmark tests that are meant
to be run on different hardware."""

from timeit import timeit


tmult = int(1E6)    # 1 / 1E3 / 1E6 / 1E9 for s / ms / us / ns respectively
N = int(1E6)        # Generic number of tests

if tmult == 1:
    t_unit = "s"
elif tmult == 1E3:
    t_unit = "ms"
elif tmult == 1E6:
    t_unit = "\u03bcs"
elif tmult == 1E9:
    t_unit = "ns"
else:
    t_unit = "?s"

print("Running tests with N={:.0E}...".format(N))

# Packet encoding / decoding =================================================
import helmholtz_cage_toolkit.scc.scc4 as codec   # Import scc

Bm_test = [1705321618.6226978, [278.0, -12.4, -123456.12345678]]
bpacket_test = b"b1705321618.622697800278.000000000000-12.400000000000-123456.12345678############################################################################################################################################################################################"
Bc_test = [123.0, -456.321, -123456.12345678]
cpacket_test = b"c123.000000000000-456.32100000000-123456.12345678###############################################################################################################################################################################################################"
msg_test = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in "
mpacket_test = b"mLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in "
seg_test = [35, 60, 355.932203, -83331.392, -55280.007, 18644.068]
spacket_test = b"s0000000000000000000000000000003500000000000000000000000000000060355.9322030000000000-83331.392000000-55280.00700000018644.0680000000###########################################################################################################################"

input_t = {
    "tm": 1705321618.6226978,
    "i_step": 1_234_567_890,
    "Im": [1234.1234, 1234.2345, 1234.3456],
    "Bm": [-12345.12345, -12345.23456, -12345.34567],
    "Bc": [-92345.12345, -82345.23456, -72345.34567],
}
tpacket_test = b't1705321618.622697800000000000000000000000001000000051234.12340001234.23450001234.3456000-12345.123450000-12345.234560000-12345.345670000-92345.123450000-82345.234560000-72345.345670000#######################################################################'

input_int_float = (
    "int_float_test",
    1,                                  # int
    -12345,                             # signed int
    -12345678901234567890123456,        # int that exceeds length
    0,                                  # zero int
    1.0,                                # float
    -345.6,                             # signed float
    -12345678901234567890123456.7,      # float that exceeds length
    0.0,                                # zero float
    1.4E6,                              # scientific notation input
)
input_bool_str = (
    "bool_str_test",
    True,                               # bool 1
    False,                              # bool 0
    "Normal string",                    # normal string
    "1.23",                             # number string
    "String that is too long to fit",   # string that is too long to fit in segment
    "",                                 # empty string
    "Иностранные буквы",                # foreign, non-ASCII characters
    "@$%^&*()_+=-{}[]'\\/<>`~"          # potentially problematic characters
)



xpacket_int_float = codec.encode_xpacket(*input_int_float)
xpacket_bool_str = codec.encode_xpacket(*input_bool_str)



print("\n ==== LENGTH CHECKS ====")
length_checks = {
    "bpacket": len(codec.encode_bpacket(*Bm_test)),
    "cpacket": len(codec.encode_cpacket(Bc_test)),
    "mpacket": len(codec.encode_mpacket(msg_test)),
    "spacket": len(codec.encode_spacket(*seg_test)),
    "tpacket": len(codec.encode_tpacket(*input_t.values())),
    "xpacket": len(codec.encode_xpacket(*input_int_float)),
}
for key in length_checks.keys():
    print(key, ":", length_checks[key], "B")

if all(l == codec.packet_size for l in length_checks.values()):
    print("   PASS")
else:
    print("   FAIL")



print("\n ==== COMMUTATION CHECKS ====")
b_packet_decoded = codec.decode_bpacket(codec.encode_bpacket(*Bm_test))
if Bm_test == b_packet_decoded:
    print("bpacket : PASS")
else:
    print("bpacket : FAIL")
    print("PRE  :", Bm_test)
    print("POST :", b_packet_decoded)

c_packet_decoded = codec.decode_cpacket(codec.encode_cpacket(Bc_test))
if Bc_test == c_packet_decoded:
    print("cpacket : PASS")
else:
    print("cpacket : FAIL")
    print("PRE  :", Bc_test)
    print("POST :", c_packet_decoded)

m_packet_decoded = codec.decode_mpacket(codec.encode_mpacket(msg_test))
if msg_test == m_packet_decoded:
    print("mpacket : PASS")
else:
    print("mpacket : FAIL")
    print("PRE  :", msg_test)
    print("POST :", m_packet_decoded)

s_packet_decoded = codec.decode_spacket(codec.encode_spacket(*seg_test))
if seg_test == s_packet_decoded:
    print("spacket : PASS")
else:
    print("spacket : FAIL")
    print("PRE  :", seg_test)
    print("POST :", s_packet_decoded)

t_packet = codec.encode_tpacket(*input_t.values())
t_packet_decoded = list(codec.decode_tpacket(t_packet))
if list(input_t.values()) == t_packet_decoded:
    print("tpacket : PASS")
else:
    print("tpacket : FAIL")
    print("PRE  :", list(input_t.values()))
    print("POST :", list(t_packet_decoded))



n = N
print("\n ==== TIMING BENCHMARKS ====")
print(f"codec.encode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.encode_bpacket(*Bm_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)

print(f"codec.decode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.decode_bpacket(bpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)


print(f"codec.encode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.encode_cpacket(Bc_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)

print(f"codec.decode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.decode_cpacket(cpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)


print(f"codec.encode_mpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.encode_mpacket(msg_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)

print(f"codec.decode_mpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.decode_mpacket(mpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)


print(f"codec.encode_spacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.encode_spacket(*seg_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)

print(f"codec.decode_spacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.decode_spacket(spacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)


print(f"codec.encode_tpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.encode_tpacket(*input_t.values())',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)

print(f"codec.decode_tpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('codec.decode_tpacket(tpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), t_unit)


print(f"codec.encode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('codec.encode_xpacket(*input_int_float)', globals=globals(), number=int(n/2))
                + timeit('codec.encode_xpacket(*input_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), t_unit)

print(f"codec.decode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('codec.decode_xpacket(xpacket_int_float)', globals=globals(), number=int(n/2))
                + timeit('codec.decode_xpacket(xpacket_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), t_unit)

