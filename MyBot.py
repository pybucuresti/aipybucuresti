import logging
log = logging.getLogger('aipybucuresti')
log.setLevel(100) # disabled by default


def main():
    import itertools
    from PlanetWars import PlanetWars
    from strategy import DoTurn
    map_data = ''
    turn_counter = itertools.count(1)
    while True:
        current_line = raw_input()
        if len(current_line) >= 2 and current_line.startswith("go"):
            turn = turn_counter.next()
            pw = PlanetWars(map_data)
            log.debug("===== turn %3d =====", turn)
            DoTurn(log, pw)
            pw.FinishTurn()
            map_data = ''
        else:
            map_data += current_line + '\n'


if __name__ == '__main__':
    import sys
    if sys.argv[-1] == '--debug':
        from os import path
        log.setLevel(logging.DEBUG)
        log_path = path.join(path.dirname(__file__), 'ai.log')
        log.addHandler(logging.FileHandler(log_path))
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        try:
            main()
        except:
            log.exception("=======================================")
    except KeyboardInterrupt:
        print 'ctrl-c, leaving ...'
