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
        planet_owner = planet.Owner()
        #turns = 0 # TODO: factor in planetary growth
        garrison = planet.NumShips()
        for fleet in sorted_fleets:
            if fleet.DestinationPlanet() != planet.PlanetID():
                continue
            if planet_owner == fleet.Owner():
                garrison += fleet.NumShips() # planet is reinfoeced
            else:
                garrison -= fleet.NumShips() # planet is attacked
            if garrison < 0: # planet is conquered
                garrison = - garrison
                planet_owner = fleet.Owner()

        return (planet_owner, garrison)

    scoreboard = {
        'ship-delta': dict( (planet.PlanetID(), planet.NumShips())
                            for planet in pw.MyPlanets() ),
        'conflict': dict( (planet.PlanetID(), predict(planet))
                          for planet in pw.Planets() ),
    }
    from pprint import pformat
    log.info(pformat(scoreboard))

    def attack(source, target, num_ships):
        dist = distance(source, target)
        sorted_fleets.append(PlanetWars.Fleet(MYSELF, num_ships,
                 source.PlanetID(), target.PlanetID(), dist, dist))
        sorted_fleets.sort(key=get_turns_remaining)
        scoreboard['conflict'][source.PlanetID()] = predict(source)
        scoreboard['conflict'][target.PlanetID()] = predict(target)
        scoreboard['ship-delta'][source.PlanetID()] -= num_ships
        pw.IssueOrder(source.PlanetID(), target.PlanetID(), num_ships)

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
            owner, garrison = scoreboard['conflict'][target.PlanetID()]
            if owner == MYSELF:
                continue

            attack_force = garrison + 1
            if scoreboard['ship-delta'][source.PlanetID()] > attack_force:
                attack(source, target, attack_force)
