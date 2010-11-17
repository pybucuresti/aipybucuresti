import PlanetWars
import math

SWEET_DEFENCE_FACTOR = 1
SWEET_DISTANCE_FACTOR = 4
DANGER_GROWTH_FACTOR = 5
DANGER_DISTANCE_FACTOR = 5

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
                garrison = - garrison
                planet_owner = fleet.Owner()

        return (planet_owner, garrison, turns)

    @memo
    def surplus(planet):
        if outcome(planet)[2] > 0:
            return 0 # ships inbound. approximate as "no surplus".
        spare = garrison = planet.NumShips() - departures[planet.id]
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
        return spare

    @memo
    def danger(planet):
        total = 0
        for enemy_planet in pw.EnemyPlanets():
            total += enemy_planet.NumShips()
            total += enemy_planet.GrowthRate() * DANGER_GROWTH_FACTOR
            total -= distance(planet, enemy_planet) * DANGER_DISTANCE_FACTOR
        return total

    departures = dict( (planet.id, 0) for planet in pw.MyPlanets() )

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

    while True:
        candidates = []

        for source in pw.MyPlanets():
            def sweet(target):
                f_growth = 10 * target.GrowthRate()
                f_distance = SWEET_DISTANCE_FACTOR * distance(source, target)
                defence = target.NumShips()
                if target.Owner() == 2:
                    defence += target.GrowthRate() * distance(source, target)
                f_defence = SWEET_DEFENCE_FACTOR * defence
                return f_growth - f_defence - f_distance

            for target in sorted((p for p in pw.Planets()),
                                 key=sweet, reverse=True):
                future_owner, future_garrison, turns = \
                        outcome(target)
                if future_owner == MYSELF:
                    continue

                dist = distance(source, target)
                extra_growth = (dist - turns) * target.GrowthRate()
                if future_owner == NEUTRAL or extra_growth < 0:
                    extra_growth = 0

                attack_force = extra_growth + future_garrison + 1
                if surplus(source) > attack_force:
                    #attack(source, target, attack_force)
                    candidates.append( (dist, (source, target, attack_force)) )

        if not candidates:
            break

        chosen = sorted(candidates)[0] # closest candidate
        attack(*chosen[1])

#    # feed forward any remaining surplus
#    for source in pw.MyPlanets():
#        my_surplus = surplus(source)
#        if my_surplus <= 0:
#            continue
#        for target in sorted(pw.Planets(), key=distance_to(source))[1:]:
#            future_owner, future_garrison, turns = \
#                    outcome(target)
#            if future_owner != MYSELF:
#                continue
#            if danger(target) > danger(source):
#                attack(source, target, my_surplus)
#                break
