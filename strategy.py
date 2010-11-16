import math

DEFENCE_FACTOR = 1
DISTANCE_FACTOR = 4
ATTACK_FACTOR = 1.1

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
            friendly, enemy = in_flight(target)
            defence_force = target.NumShips() - friendly
            if target.Owner() == 2:
                defence_force += target.GrowthRate() * distance(source, target)
            if defence_force < 0:
                continue

            attack_force = math.ceil(defence_force * ATTACK_FACTOR)
            if ships_left > attack_force:
                pw.IssueOrder(source.PlanetID(), target.PlanetID(),
                              attack_force)
                ships_left -= attack_force
