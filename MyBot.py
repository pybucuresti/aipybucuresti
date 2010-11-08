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
  aggressiveness = 0.5
  num_own_ships = 0
  for pl in pw.MyPlanets():
    num_own_ships += pl.NumShips()
  num_neutral_ships = 0
  for pl in pw.NeutralPlanets():
    num_neutral_ships += pl.NumShips()
  num_enemy_ships = 0
  for pl in pw.EnemyPlanets():
    num_enemy_ships += pl.NumShips()
  adaptive_aggressiveness = 2 * num_own_ships / (num_neutral_ships + 2 * num_enemy_ships)
  # (1) If we currently have a fleet in flight, just do nothing.
  #if len(pw.MyFleets()) >= 3:
  #  return
  ## (2) Find my strongest planet.
  #source = -1
  #source_score = -999999.0
  #source_num_ships = 0
  #my_planets = pw.MyPlanets()
  #for p in my_planets:
  #  score = float(p.NumShips())
  #  if score > source_score:
  #    source_score = score
  #    source = p.PlanetID()
  #    source_num_ships = p.NumShips()
  ## (3) Find the weakest enemy or neutral planet.
  #dest = -1
  #dest_score = -999999.0
  #not_my_planets = pw.NotMyPlanets()
  #for p in not_my_planets:
  #  score = 1.0 / (1 + p.NumShips())
  #  if score > dest_score:
  #    dest_score = score
  #    dest = p.PlanetID()

  def get_fleets_to_planet(planet, attacker):
    '''
    return (my_fleet, enemy_fleet)
    '''
    num_ships = 0
    for fleet in pw.Fleets():
      if fleet.DestinationPlanet() == planet:
        if fleet.Owner()==attacker:
          num_ships -= fleet.NumShips()
        else:
          num_ships += fleet.NumShips()
    return num_ships

  def attractiveness(planet, planet_list, attacker):
    planets = [(p, pw.Distance(p.PlanetID(), planet.PlanetID())) for p in planet_list]
    planets.sort(key=operator.itemgetter(1))
    cumulative_ships = 0
    num_ships = planet.NumShips() + get_fleets_to_planet(planet, attacker)

    if num_ships < 0:
      return {'attr': 0, 'planets': planets}
    for i, (my_planet, distance) in enumerate(planets):
      defences = num_ships
      if planet.Owner() not in [ attacker, 0 ]:
        defences += planet.GrowthRate() * distance
      num_ships = int(defences * 1.2)
      cumulative_ships += my_planet.NumShips() * aggressiveness
      if cumulative_ships > num_ships:
        return {'attr': planet.GrowthRate() / ((50.0 + planet.NumShips()) * distance),
                'planets': planets[:i+1]}
    else:
      return {'attr': 0, 'planets': planets}

  my_planet_list = pw.MyPlanets()
  enemy_planet_list = pw.EnemyPlanets()


  diff_attr_list = []
  for planet in pw.NotMyPlanets():
    my = attractiveness(planet, my_planet_list, 1)
    enemy = attractiveness(planet, enemy_planet_list, 2)
    diff_attractiveness = my['attr'] - enemy['attr']
    diff_attr_list.append((diff_attractiveness, planet, my['planets']))

  if not diff_attr_list:
    return

  target_tup = max(diff_attr_list) #most attractive
  dest = target_tup[1].PlanetID()
  planets = target_tup[2]

  # (4) Send half the ships from my strongest planet to the weakest
  # planet that I do not own.
  for my_planet, distance in planets:
    pw.IssueOrder(my_planet.PlanetID(), dest, my_planet.NumShips() * aggressiveness)


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
