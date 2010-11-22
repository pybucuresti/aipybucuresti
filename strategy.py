import PlanetWars
import math

DANGER_GROWTH_FACTOR = 5
DANGER_DISTANCE_FACTOR = 5

JUICY_DISTANCE = 0.2
JUICY_COST = 5.0

NEUTRAL = 0
MYSELF = 1
ENEMY = 2

def memo(func):
    results = {}
    def wrapper(planet):
        if planet.id not in results:
            results[planet.id] = func(planet)
        return results[planet.id]
    wrapper.invalidate = lambda planet: results.pop(planet.id, None)
    return wrapper

def DoTurn(log, pw):
    import random
    def distance(planet1, planet2):
        return pw.Distance(planet1.id, planet2.id)

    def distance_to(planet):
        return lambda other_planet: distance(planet, other_planet)

    def desirable_planets():
        planets = sorted(pw.NotMyPlanets(), key=lambda p: p.GrowthRate() / (p.NumShips() + 1.0), reverse=True)
        return planets

    target = desirable_planets()[0]
    try:
        source = random.choice(pw.MyPlanets())
    except IndexError:
        return
    num_ships = random.randint(1, source.NumShips())
    log.info('attacking %d from %d with %d', target.id, source.id, num_ships)
    pw.IssueOrder(source.id, target.id, num_ships)
