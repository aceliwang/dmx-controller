# Timeline

- [DONE] Get '101 si 100' working
- [DONE] Get programmer to reflect states for '101 si 100'
- [TODO] Get programmer to reflect palette state in programmer for '101 si 100'
- [TODO] Set colour, set position, set effects
- [TODO] If repatch, change all palettes for reference
- [TODO] Programmer
  - Programmer is a dictionary with each fixture and each parameter
  - {'commands': [list of commands], 101: {"intensity": [('command', 100)], "colour": red}}
  - How to handle overlapping commands? LTP
  - How to handle knock out? 
  - Figure out overwrite behaviour. Ordered dicts are annoying.

## Programming

- [TODO] Get mouse hook working to tie into programmer
- [TODO] Remove from programmer
- [TODO] Remove parameters specific to fixtures from programmer
- [TODO] Empty palettes with only names

## Cuelists

- [TODO] Click to select cuelist
- [TODO] Edit cues in cuelist

## General Palettes

- [TODO] Enable empty palettes or default palette?

## Colours
- [TODO] Create all colours
- [TODO] RGB to RGBW conversion
- [TODO] HSL to HS conversion

## ArtNet
- [TODO] ArtNet output
- [TODO] Universe support


# // patching
# fixtureType.patch((101, 105), 'start address', 'default ie. name.json')
# (101, 105).patch(fixtureType, 'start address', 'step address')
# patch 'trimmer pars' 101 > 105 from 322 every 100
# // figure out how to do
# // patch dmx output device


# group = select(101, 104, (201, 205))
# // GROUPS(DOES NOT REQUIRE SAVE TO VARIABLE)
# // select(a, (b, c) ...)
# // select a and range from b to c
# // alt = s
# // can save to variable ie group or can be cleared
# grand = select(all)
# // default establishment
# // should be an active call or integrated into patch

# group.plus(a, b, c)
# // append to group


# state.record()
# state.add()
# // group of presets ie.

# colour.record(0, 100, 'a, optional')
# // COLOUR
# // record 0, 100 for fixtures 'a' to 'colour name'
# // hs, rgb
#  record (0, 100) for fixtures 'a' as red

# position.record()

# beam.record('gobo', 3)

# clear()

# fixture.si(a, 5)
# // set intensity to a over 5 seconds
# // how do i make changing the 5 second fade easy in theatre
# // can replace 5 with manual for mouse input

# fixture.ss()

# fixture.sc()
# // set colour
# fixture.on()
# // fixture.sc(default on intensity)
# fixture.off()
# // fixture.sc(default off intensity: 0)

# fixture.sp(tilt, pan)
# // set position
# // use a mouse to program position
# // use a modifier key to transform orientation

# fixture.sb('gobo')
# // set beam

# fixture.set('custom', value)
# // is everything else a function call of this?


# repeat()
# // create function for chase


# fixture.se(effect)
# effect.record(default rate) {
#     fixture.si('sine', 50)
#     for(i in range 100) {
#         fixture.si(50)
#     }
# }
# // create effect

# //  # cue sequence
# seq = function() {
#     cyc.on()
#     at(4).cyc.off()
# }

# // artnet output
# // osc output
# fixture.sosc('asdfasdfs')

# // CUES

# // need to figure out timing

# clock.start(0) // start clock at 0
# at(0) cyc.on().sc(blue)
# at(2.5) {
#     cyc.off()
#     pars.on()
# }
# at(0).every(5)
# // repeat every 5 seconds from time 0
# // how do i put many fixtures together
# cyc.start(cycleblue)
# grand.si(0)
# clock.stop(0)
# // todo
# // dmx output monitor
# // patch chart integrated into dmx output
# // timeline editor
# // grand master
# osc support
