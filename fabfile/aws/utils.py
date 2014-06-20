import itertools


def flatten_reservations(reservations):
    instances = [r.instances for r in reservations]
    chain = itertools.chain(*instances)

    return [i for i in list(chain)]
