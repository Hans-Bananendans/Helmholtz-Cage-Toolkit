from helmholtz_cage_toolkit.server.server_config import server_config as config

pinnames_0 = {
    "dac": {
        0: "pin0",
        1: "pin1",
        2: "pin2",
    },
    "adc": {
        0: "pin0",
        1: "pin1",
        2: "pin2",
    }
}

# pinnames = dict([
#     ("dac", {i: "pin"+str(i) for i in range(16)}),
#     ("adc", {i: "pin"+str(i) for i in range(16)})
# ])

pinnames = dict([
    ("dac", {i: "" for i in range(16)}),
    ("adc", {i: "" for i in range(16)})
])

print(pinnames)

for k, v in config.items():
    if k[0:4] == "pin_":
        pinnames[k[4:7]][v] = k[8:]


print(pinnames)