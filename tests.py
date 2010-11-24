""" Tests bot on all maps and log ones where it loses
"""
import os
import logging
from datetime import datetime

logger = logging.getLogger('tests')
logger.setLevel(100)
logger.setLevel(logging.DEBUG)
log_path = os.path.join(os.path.dirname(__file__), 'tests.log')
logger.addHandler(logging.FileHandler(log_path))

def main():
    """ Run tests
    """
    maps = os.listdir('maps')
    maps.sort()

    logger.debug("=== Start: %s ===", datetime.now())
    for gmap in maps:
        cmd = ('java -jar tools/PlayGame.jar maps/%(map)s 200 1000 log.txt'
               ' "python MyBot.py" "java -jar example_bots/DualBot.jar" '
               '>> ai-tests.log' % {'map': gmap})
        stdout, stdin, stderr = os.popen3(cmd)
        if 'Player 2' in stderr.read():
            logger.debug(gmap)

        stdin.close()
        stdout.close()
        stderr.close()

    logger.debug("=== Done: %s ===", datetime.now())

if __name__ == "__main__":
    main()
