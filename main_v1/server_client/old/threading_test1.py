from time import time, sleep
from numpy.random import random
from threading import Thread


def do_count(name, t):
    pf = f"[{name}]> "
    print(f"{pf}I am thread '{name}'")
    print(f"{pf}I am going to count to {t}")

    t0 = time()

    th2 = Thread(target=do_spam, args=(f"Spammer {int(random()*1E5)}",), daemon=True)
    th2.start()

    lc = 0
    while True:
        tc = time()
        if tc >= t0 + t:
            break
        sleep(0.001)
        lc += 1

    print(f"{pf} I finished counting to {t}. Loop count: {lc}")
    print(f"{pf} Done. Terminating {th2.name}...")
    th2.join(timeout=0)

    print(f"{pf} Goodbye")


def do_spam(name):
    pf = f"[{name}]> "
    print(f"{pf}Started.")
    i = 0
    while True:
        print(f"{pf}{i}")
        i += 1
        sleep(1)


th1 = Thread(target=do_count, args=(f"Counter {int(random()*1E5)}", 6))
th1.run()
