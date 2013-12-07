from random import random


def get_image_url(width=512, height=512, message='wow such tile', bgcolor=None, fgcolor ='ffffff'):

    if bgcolor is None:
        bgcolor = ''
        try:
            seed = int(message) * 200/60
        except:
            seed = int(random.random * 100 + 1)

        for i in range(3):
            next = hex((i * 42 + seed) % 200)[2:]
            while len(next) < 2:
                next = '0' + next
            bgcolor += next

    url = str.format('http://placehold.it/{width}x{height}/{bgcolor}/'
                     '{fgcolor}&text={message}',
                     message=message, fgcolor=fgcolor, bgcolor=bgcolor,
                     width=width, height=height)
    return url

