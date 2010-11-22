import PlanetWars
import math
from itertools import groupby
from collections import namedtuple

Event = namedtuple('Event', 'owner num_ships turn')

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

    def average_distance(planet):
        try:
            return sum(pw.Distance(planet.id, p.id) for p in pw.MyPlanets()) / len(pw.MyPlanets())
        except:
            return 1

    def desirable_planets():
        planets = sorted(pw.NotMyPlanets(),
            key=lambda p: p.GrowthRate() ** 2 / (p.NumShips() + 1.0) / average_distance(p), reverse=True)
        return planets

    @memo
    def predict_planet(planet):
        """ Return number of turns until change owner """

        fleets = sorted([f for f in pw.Fleets() if f.DestinationPlanet() == planet.id],
            key=lambda f: f.TurnsRemaining())
        num_ships = planet.NumShips()
        owner = planet.Owner()
        event_log = [Event(owner, num_ships, 0)] #Owner, NumShip
        turn = 0
        for fleet_turn, fleets in groupby(fleets, key=lambda f: f.TurnsRemaining()):
            if owner != NEUTRAL:
                num_ships += (fleet_turn - turn) * planet.GrowthRate()
            turn = fleet_turn

            for fleet in fleets:
                if fleet.Owner() != owner:
                    num_ships -= fleet.NumShips()
                else:
                    num_ships += fleet.NumShips()
                if num_ships < 0:
                    owner = fleet.Owner()
                    num_ships = -num_ships
            event_log.append(Event(owner, num_ships, fleet_turn,))
        return event_log

    @memo
    def surplus(planet):
        events = predict_planet(planet)
        min_surplus = planet.NumShips()
        for event in events:
            if event[0] != planet.Owner():
                return 0 
            min_surplus = min(min_surplus, event[1])
        return min_surplus

    def try_conquer(target_planet):
        events = predict_planet(target_planet)
        my_planets = sorted(pw.MyPlanets(), key=lambda p: pw.Distance(target_planet.id, p.id))
        num_ships = 0
        ret = []
        for p in my_planets:
            the_surplus = surplus(p)
            num_ships += the_surplus
            if the_surplus:
                ret.append(p)
            if num_ships > events[-1][1]:
                return ret
        return None
     
    for planet in desirable_planets():
        event = predict_planet(planet)[-1]
        if event[0] == MYSELF:
            continue
        conquer = try_conquer(planet)
        if conquer is None:
            continue
        for my_planet in conquer:
            num_ships = surplus(my_planet) 
            log.info('attacking %d from %d with %d', planet.id, my_planet.id, num_ships)
            pw.IssueOrder(my_planet.id, planet.id, num_ships)
        return
