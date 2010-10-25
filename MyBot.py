#!/usr/bin/env python
#

"""
// The DoTurn function is where your code goes. The PlanetWars object contains
// the state of the game, including information about all planets and fleets
// that currently exist. Inside this function, you issue orders using the
// pw.IssueOrder() function. For example, to send 10 ships from planet 3 to
// planet 8, you would say pw.IssueOrder(3, 8, 10).
//
// There is already a basic strategy in place here. You can use it as a
// starting point, or you can throw it out entirely and replace it with your
// own. Check out the tutorials and articles on the contest website at
// http://www.ai-contest.com/resources.
"""

from PlanetWars import PlanetWars
import operator
import logging

logger = logging.getLogger('planeta')
logger.addHandler(logging.FileHandler('log'))
logger.setLevel(logging.DEBUG)

def DoTurn(pw):
  # (1) If we currently have a fleet in flight, just do nothing.
  if len(pw.MyFleets()) >= 3:
    return
  # (2) Find my strongest planet.
  source = -1
  source_score = -999999.0
  source_num_ships = 0
  my_planets = pw.MyPlanets()
  for p in my_planets:
    score = float(p.NumShips())
    if score > source_score:
      source_score = score
      source = p.PlanetID()
      source_num_ships = p.NumShips()
  # (3) Find the weakest enemy or neutral planet.
  dest = -1
  dest_score = -999999.0
  not_my_planets = pw.NotMyPlanets()
  for p in not_my_planets:
    score = 1.0 / (1 + p.NumShips())
    if score > dest_score:
      dest_score = score
      dest = p.PlanetID()

  def my_attractiveness(planet, planet_list):
    planets = [(p, pw.Distance(p.PlanetID(), planet.PlanetID())) for p in planet_list]
    planets.sort(key=operator.itemgetter(1))
    cumulative_ships = 0
    for (my_planet, distance) in planets:
      cumulative_ships += my_planet.NumShips()
      if cumulative_ships > planet.NumShips():
        return planet.GrowthRate() / ((50.0 + planet.NumShips()) * distance)
    else:
      return 0

  my_planet_list = pw.MyPlanets()
  enemy_planet_list = pw.EnemyPlanets()


  diff_attr_list = []
  for neutral_planet in pw.NotMyPlanets():
    diff_attractiveness = (my_attractiveness(neutral_planet, my_planet_list) -
      my_attractiveness(neutral_planet, enemy_planet_list))
    diff_attr_list.append((diff_attractiveness, neutral_planet))

  if not diff_attr_list:
    return

  dest = max(diff_attr_list)[1].PlanetID() #most attractive

  # (4) Send half the ships from my strongest planet to the weakest
  # planet that I do not own.
  if source >= 0 and dest >= 0:
    dest_planet = pw.GetPlanet(dest)
    defences = dest_planet.NumShips()
    if dest_planet.Owner() == 2:
      distance = pw.Distance(source, dest)
      defences += dest_planet.GrowthRate() * distance
    num_ships = int(defences * 1.1)
    if source_num_ships > num_ships:
      pw.IssueOrder(source, dest, num_ships)

def main():
  map_data = ''
  while(True):
    current_line = raw_input()
    if len(current_line) >= 2 and current_line.startswith("go"):
      pw = PlanetWars(map_data)
      try:
        DoTurn(pw)
      except:
        logger.exception("Something is Wrong")
      pw.FinishTurn()
      map_data = ''
    else:
      map_data += current_line + '\n'


if __name__ == '__main__':
  try:
    import psyco
    psyco.full()
  except ImportError:
    pass
  try:
    main()
  except KeyboardInterrupt:
    print 'ctrl-c, leaving ...'
