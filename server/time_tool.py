import datetime

def get_time_for_file():
    return str(datetime.datetime.now())[0:19].replace('-', '_').replace(' ', '_')


def get_time():
    return str(datetime.datetime.now())[0:19]
