"""This file contains a convenient set of benchmark tests that are meant
to be run on different hardware."""

from timeit import timeit


tmult = int(1E6)    # 1E3 / 1E6 / 1E9 for ms / us / ns respectively
N = int(1E5)        # Generic number of tests



# Packet encoding / decoding =================================================
import helmholtz_cage_toolkit.codec.scc2q as scc   # Import codec

Bm_test = [1705321618.6226978, 278.0, -12.4, -123456.123456789]
bpacket_test = b"b1705321618.622697800278.000000000000-12.400000000000-123456.123456789###########################################################################################################################################################################################"
Bc_test = [123.0, -456.321, -123456.123456789]
cpacket_test = b"c123.000000000000-456.32100000000-123456.12345678###############################################################################################################################################################################################################"
msg_test = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in "
mpacket_test = b"mLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in "
seg_test = [35, 60, 355.932203, -83331.392, -55280.007, 18644.068]
spacket_test = b"s0000000000000000000000000000003500000000000000000000000000000060355.9322030000000000-83331.392000000-55280.00700000018644.0680000000###########################################################################################################################"

print(len(scc.encode_bpacket(Bm_test)))

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

xpacket_int_float = scc.encode_xpacket(*input_int_float)
xpacket_bool_str = scc.encode_xpacket(*input_bool_str)

n = N
print(f"scc.encode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.encode_bpacket(Bm_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.decode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.decode_bpacket(bpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.encode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.encode_cpacket(Bc_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.decode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.decode_cpacket(cpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.encode_mpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.encode_mpacket(msg_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.decode_mpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.decode_mpacket(mpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.encode_spacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.encode_spacket(*seg_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.decode_spacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('scc.decode_spacket(spacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"scc.encode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('scc.encode_xpacket(*input_int_float)', globals=globals(), number=int(n/2))
                + timeit('scc.encode_xpacket(*input_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), "us")

print(f"scc.decode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('scc.decode_xpacket(xpacket_int_float)', globals=globals(), number=int(n/2))
                + timeit('scc.decode_xpacket(xpacket_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), "us")

