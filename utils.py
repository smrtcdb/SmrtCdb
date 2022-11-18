import ujson
import utime

from lib.ulogging import logger
from settings import IFTT_API_KEY


def get_unique_id():
    """ returns a thing-shadow ID to be used when generating the AWS request for shadow state """
    from machine import unique_id
    id_reversed = unique_id()
    id_binary = [id_reversed[n] for n in range(len(id_reversed) - 1, -1, -1)]
    return "".join("{:02x}".format(x) for x in id_binary)


def to_json(dict_content):
    try:
        json_file = ujson.dumps(dict_content)
    except ValueError as e:
        logger.exc(e, "Got an error decoding the object %s", dict_content)
    else:
        return json_file


def read_from_json(file_path, key=None):
    # todo: Make sure that the file contains a dict. if not return
    try:
        with open(file_path, 'r') as f:
            dict_content = ujson.load(f)
    except ValueError as e:
        logger.exc(e, "%s is not properly formatted json", file_path)
    except OSError:
        logger.warning("%s does not exist", file_path)
    except MemoryError:
        logger.error("Memory error reading json: %s", file_path)
    except Exception as e:
        logger.exc(e, "Unhandled exception read_from_json: %s", file_path)
    else:
        return dict_content.get(key) if key and isinstance(dict_content, dict) else dict_content


def write_to_json(file_path, content):
    try:
        with open(file_path, 'w') as f:
            f.write(
                ujson.dumps(content) if isinstance(content, dict) else content
            )
    except ValueError:
        logger.error("%s cannot be parse into json", content)
    except MemoryError:
        logger.error("Memory error writing the json file %s", file_path)
    else:
        return content


def zfl(s, width):
    # Pads the provided string with leading 0's to suit the specified 'chrs' length
    # Force # characters, fill with leading 0's
    return '{:0>{w}}'.format(s, w=width)


# @timed_function
# Print time taken by a function call

def timed_function(f, *args, **kwargs):
    def new_func(*args, **kwargs):
        t = utime.ticks_us()
        result = f(*args, **kwargs)
        delta = utime.ticks_diff(utime.ticks_us(), t)
        logger.info('Function {} with k/args {} \n Time = {:6.3f}ms'.format(f.__name__, (args, kwargs), delta / 1000))
        return result

    return new_func


class TimeIt:
    def __init__(self):
        self.timer = 0

    def start_measure(self):
        self.timer = utime.ticks_us()

    def finish_measure(self):
        delta = utime.ticks_diff(utime.ticks_us(), self.timer)
        print('Time = {:6.3f}ms'.format(delta / 1000))
        self.timer = 0
