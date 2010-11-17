import PlanetWars
import math

DEFENCE_FACTOR = 1
DISTANCE_FACTOR = 4
ATTACK_FACTOR = 1.1

NEUTRAL = 0
MYSELF = 1
ENEMY = 2

def DoTurn(log, pw):
    def in_flight(planet):
        friendly, enemy = 0, 0
        for fleet in pw.Fleets():
            if fleet.DestinationPlanet() != planet.PlanetID():
                continue
            if fleet.Owner() == 1:
                friendly += fleet.NumShips()
            else:
                enemy += fleet.NumShips()
        return friendly, enemy

    def distance(planet1, planet2):
        return pw.Distance(planet1.PlanetID(), planet2.PlanetID())

    get_turns_remaining = lambda f: f.TurnsRemaining()

    sorted_fleets = sorted(pw.Fleets(), key=get_turns_remaining)

    def predict(planet):
        # calculate who conquers this planet
        planet_owner = planet.Owner()
        turns = 0
        garrison = planet.NumShips()
        for fleet in sorted_fleets:
            if fleet.DestinationPlanet() != planet.PlanetID():
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

    def surplus(planet):
        if scoreboard['conflict'][planet.PlanetID()][2] > 0:
            return 0
        return planet.NumShips()

    scoreboard = {}
    scoreboard['conflict'] = dict( (planet.PlanetID(), predict(planet))
                                   for planet in pw.Planets() )
    scoreboard['surplus'] = dict( (planet.PlanetID(), surplus(planet))
                                  for planet in pw.MyPlanets() )
    from pprint import pformat
    log.info(pformat(scoreboard))

    def attack(source, target, num_ships):
        dist = distance(source, target)
        sorted_fleets.append(PlanetWars.Fleet(MYSELF, num_ships,
                 source.PlanetID(), target.PlanetID(), dist, dist))
        sorted_fleets.sort(key=get_turns_remaining)
        scoreboard['conflict'][source.PlanetID()] = predict(source)
        scoreboard['conflict'][target.PlanetID()] = predict(target)
        scoreboard['surplus'][source.PlanetID()] -= num_ships
        pw.IssueOrder(source.PlanetID(), target.PlanetID(), num_ships)
        log.info("attack from %d to %d with %d ships, distance is %d",
                 source.PlanetID(), target.PlanetID(), num_ships, dist)

    for source in pw.MyPlanets():
        def sweet(target):
            f_growth = 10 * target.GrowthRate()
            f_distance = DISTANCE_FACTOR * distance(source, target)
            defence = target.NumShips()
            if target.Owner() == 2:
                defence += target.GrowthRate() * distance(source, target)
            f_defence = DEFENCE_FACTOR * defence
            return f_growth - f_defence - f_distance

        ships_left = source.NumShips()

        for target in sorted((p for p in pw.NotMyPlanets()),
                             key=sweet, reverse=True):
            future_owner, future_garrison, turns = \
                    scoreboard['conflict'][target.PlanetID()]
            if future_owner == MYSELF:
                continue

            dist = distance(source, target)
            extra_growth = (dist - turns) * target.GrowthRate()
            if future_owner == NEUTRAL or extra_growth < 0:
                extra_growth = 0

            attack_force = extra_growth + future_garrison + 1
            if scoreboard['surplus'][source.PlanetID()] > attack_force:
                attack(source, target, attack_force)
