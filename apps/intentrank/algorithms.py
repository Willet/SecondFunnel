import random as real_random


def first(from_set, num_results):
    """sample whichever ones come first"""
    return from_set[:num_results]


def last(from_set, num_results):
    """sample whichever ones come last"""
    return from_set[:-num_results]


def random(from_set, num_results):
    """sample without replacement (all other algos are stubs)"""
    return real_random.sample(from_set, num_results)


def random_repeat(from_set, num_results):
    """sample with replacement"""
    raise NotImplementedError()
