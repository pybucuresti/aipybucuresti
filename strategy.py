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
    for planet in pw.Planets():
        planet.id = planet.PlanetID()

    def in_flight(planet):
        friendly, enemy = 0, 0
        for fleet in pw.Fleets():
            if fleet.DestinationPlanet() != planet.id:
                continue
            if fleet.Owner() == MYSELF:
                friendly += fleet.NumShips()
            else:
                enemy += fleet.NumShips()
        return friendly, enemy

    def distance(planet1, planet2):
        return pw.Distance(planet1.id, planet2.id)

    def distance_to(planet):
        return lambda other_planet: distance(planet, other_planet)

    get_turns_remaining = lambda f: f.TurnsRemaining()

    sorted_fleets = sorted(pw.Fleets(), key=get_turns_remaining)

    @memo
    def outcome(planet):
        # calculate who conquers this planet
        planet_owner = planet.Owner()
        turns = 0
        garrison = planet.NumShips()
        limit = None
        if planet_owner == MYSELF:
            limit = garrison
        for fleet in sorted_fleets:
            if fleet.DestinationPlanet() != planet.id:
                continue

            if planet_owner != NEUTRAL: # calculate growth incrementally
                turns_delta = fleet.TurnsRemaining() - turns
                garrison += turns_delta * planet.GrowthRate()
            turns = fleet.TurnsRemaining()

            if planet_owner == fleet.Owner():
                garrison += fleet.NumShips() # planet is reinfoeced
            else:
                garrison -= fleet.NumShips() # planet is attacked
            if garrison < 0: # planet is conquered
                if limit > 0:
                    limit = garrison # which is negative
                garrison = - garrison
                planet_owner = fleet.Owner()
            else:
                limit = min(limit, garrison)

        return (planet_owner, garrison, turns, limit)

    @memo
    def surplus(planet):
        garrison = planet.NumShips() - departures[planet.id]
        if outcome(planet)[2] > 0:
            spare = min(max(outcome(planet)[3], 0), garrison)
        else:
            spare = garrison
        turns = 0
        for other_planet in sorted(pw.Planets(), key=distance_to(planet))[1:]:
            # skip the first one since it's `planet` (because distance = 0)
            dist = distance(planet, other_planet)
            garrison += (dist - turns) * planet.GrowthRate()
            turns = dist
            if other_planet.Owner() == ENEMY:
                garrison -= other_planet.NumShips() # assume they attack
                spare = min(spare, garrison)
            elif other_planet.Owner() == MYSELF:
                garrison += other_planet.NumShips() # assume we reinforce
            if spare < 0:
                break # panic!
        return max(spare, 0)

    @memo
    def danger(planet):
        total = 0
        for enemy_planet in pw.EnemyPlanets():
            total += enemy_planet.NumShips()
            total += enemy_planet.GrowthRate() * DANGER_GROWTH_FACTOR
            total -= distance(planet, enemy_planet) * DANGER_DISTANCE_FACTOR
        return total

    departures = dict( (planet.id, 0) for planet in pw.MyPlanets() )

    def potential_defense(target, turns):
        total = target.NumShips()
        if target.Owner() == ENEMY:
            total += turns * target.GrowthRate()
        for planet in pw.NotMyPlanets():
            if planet.id == target.id:
                continue
            dist = distance(planet, target)
            if dist < turns:
                planet_can_send = planet.NumShips()
                planet_can_send += planet.GrowthRate() * (turns - dist - 1)
                for fleet in pw.Fleets():
                    if fleet.DestinationPlanet() == planet.id:
                        if fleet.TurnsRemaining() < (turns - dist):
                            planet_can_send += fleet.NumShips()
                total += planet_can_send
        return total + 1

    def attack(source, target, num_ships):
        dist = distance(source, target)
        sorted_fleets.append(PlanetWars.Fleet(MYSELF, num_ships,
                 source.id, target.id, dist, dist))
        sorted_fleets.sort(key=get_turns_remaining)
        departures[source.id] += num_ships
        outcome.invalidate(source)
        outcome.invalidate(target)
        surplus.invalidate(source)
        assert surplus(source) >= 0
        pw.IssueOrder(source.id, target.id, num_ships)
        log.info("attack from %d to %d with %d ships, distance is %d",
                 source.id, target.id, num_ships, dist)

    # calculate who needs help
    for target in pw.MyPlanets():
        future_owner, future_garrison, turns, limit = outcome(target)
        if limit < 0: # needs help
            needed = min(-limit + 1, future_garrison)
            for source in sorted(pw.MyPlanets(), key=distance_to(target))[1:]:
                to_send = min(needed, surplus(source))
                if to_send > 0:
                    attack(source, target, to_send)
                    needed -= to_send
                if needed <= 0:
                    break

    total_surplus = sum(map(surplus, pw.MyPlanets()))
    if not total_surplus > 0:
        return

    def juicy(target):
        mean_distance = ( sum( p.GrowthRate() * distance(p, target)
                               for p in pw.MyPlanets() )
                          / float(len(pw.MyPlanets())) )

        pd = float(potential_defense(target, int(mean_distance)))
        cost_factor = float(target.NumShips()) / total_surplus

        return ( target.GrowthRate()
               - mean_distance * JUICY_DISTANCE
               - cost_factor * JUICY_COST )

    # calculate what we want to attack
    for target in sorted(pw.NotMyPlanets(), key=juicy, reverse=True):
        future_owner, future_garrison, turns, limit = outcome(target)
        if future_owner == MYSELF:
            continue

        army = []
        army_size = 0
        for source in sorted(pw.MyPlanets(), key=distance_to(target)):
            if not surplus(source) > 0:
                continue
            army.append(source)
            army_size += surplus(source)

            dist = distance(source, target)
            extra_growth = (dist - turns) * target.GrowthRate()
            if future_owner == NEUTRAL or extra_growth < 0:
                extra_growth = 0
            needed = extra_growth + future_garrison + 1

            if army_size >= needed:
                for source in army:
                    num_ships = min(needed, surplus(source))
                    attack(source, target, num_ships)
                    needed -= num_ships
                assert needed == 0
                break

    # feed forward any remaining surplus
    for source in pw.MyPlanets():
        my_surplus = surplus(source)
        if my_surplus <= 0:
            continue
        for target in sorted(pw.Planets(), key=distance_to(source))[1:]:
            future_owner, future_garrison, turns, limit = outcome(target)
            if future_owner != MYSELF:
                continue
            if danger(target) > danger(source):
                attack(source, target, my_surplus)
                break
