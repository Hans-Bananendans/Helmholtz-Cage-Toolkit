"""This file contains a convenient set of benchmark tests that are meant
to be run on different hardware."""

from timeit import timeit


tmult = int(1E6)    # 1E3 / 1E6 / 1E9 for ms / us / ns respectively
N = int(1E5)        # Generic number of tests



# Packet encoding / decoding =================================================
from scc2 import SCC    # Import codec

Bm_test = [1705321618.6226978, 278.0, -12.4, -123456.123456789]
bpacket_test = b"b1705321618.622697800278.000000000000-12.400000000000-123456.12345679"
Bc_test = [123.0, -456.321, -123456.123456789]
cpacket_test = b"c123.000000000000-456.32100000000-123456.12345679"
msg_test = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in m"
mpacket_test = b"mLorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Tellus elementum sagittis vitae et leo. Quam vulputate dignissim suspendisse in est ante in nibh mauris. Aliquam faucibus purus in m"

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

xpacket_int_float = SCC.encode_xpacket(*input_int_float)
xpacket_bool_str = SCC.encode_xpacket(*input_bool_str)


n = N
print(f"SCC.encode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('SCC.encode_bpacket(Bm_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"SCC.decode_bpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('SCC.decode_bpacket(bpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"SCC.encode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('SCC.encode_cpacket(Bc_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"SCC.decode_cpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round(timeit('SCC.decode_cpacket(cpacket_test)',
                   globals=globals(), number=n)*tmult/n, 3), "us")

print(f"SCC.encode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('SCC.encode_xpacket(*input_int_float)', globals=globals(), number=int(n/2))
                + timeit('SCC.encode_xpacket(*input_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), "us")

print(f"SCC.decode_xpacket() - t_avg (n={'{:1.0E}'.format(n)}):",
      round((
                timeit('SCC.decode_xpacket(xpacket_int_float)', globals=globals(), number=int(n/2))
                + timeit('SCC.decode_xpacket(xpacket_bool_str)', globals=globals(), number=int(n/2))
            )*tmult/n, 3), "us")

