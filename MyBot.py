SWEET_GROWTH_RATE = 5

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

    def sweet(planet):
        return (SWEET_GROWTH_RATE * planet.GrowthRate() - planet.NumShips())

    for target in sorted((p for p in pw.NotMyPlanets()),
                         key=sweet, reverse=True):
        friendly, enemy = in_flight(target)
        if friendly > target.NumShips():
            continue
        else:
            break # found a target
    else:
        return # no target!

    for source in pw.MyPlanets():
        pw.IssueOrder(source.PlanetID(), target.PlanetID(), source.NumShips())
