# from wrappers import select
import cmd
import eel


# // patching
# fixtureType.patch((101, 105), 'start address', 'default ie. name.json')
# (101, 105).patch(fixtureType, 'start address', 'step address')
# // figure out how to do
# // patch dmx output device

## load file

## interpret line
## parse line
## split everything with spaces
## combine operators
## interpret

for line in file:
    args = line.split(' ')
    while '>' in args:
        originalOperatorIndex = args.index('>')
        arg1Index = originalOperatorIndex - 1
        arg2Index = originalOperatorIndex + 1
        args[originalOperatorIndex - 1] = ''.join(args[arg1Index:arg2Index + 1])
        args.pop(originalOperatorIndex) # pop operator
        args.pop(originalOperatorIndex) # pop arg 2
    command = args.pop(0)
    if command in ('select', 's'): # select
        # eg. select 102 104 105 106 > 1020
        select(*args[:])
    elif command in ('clear', 'c'):
        select([])
    elif command in ('record', 'r'):
        continue
    elif command in ('seti', 'si'):
        continue
    elif command in ('setp', 'sp'):
        continue
    elif command in ('setc', 'sc'):
        continue
    elif command in ('setb', 'sb'):
        continue
    elif command in ('set'):
        continue
    elif command in ('flash'):
        continue
    elif args[0] == '=' and args[1] == 'select': # unknown variable
        # groupName = select 1 2 3 > 100
        groupName = args[1]

        groups()
        



class g: # groups
    def __init__(self, name, fixtures):
        self.name = name
        self.fixtures = fixtures
    # usage: macs = g(macs, select())
    def __str__(self):
        return self.name
    def plus(self, fixtures):
        self.fixtures += fixtures

class groups(g):
    def __init__(self, name, fixtures):
        super().__init__(name, fixtures)

selection = []

def select(*selection):
    # selection = list of fixtureGroups, either fixture or fixtureRange
    # if fixtureRange, unpack
    # if fixture, put in array
    selection = [fixtureGroup.split('>') if '>' in fixtureGroup else int(fixtureGroup) for fixtureGroup in selection]
    selection = [[fixture for fixture in range(fixtureGroup[0], fixtureGroup[1] + 1)]
                 if isinstance(fixtureGroup, (list, tuple)) else [fixtureGroup]
                 for fixtureGroup in selection]
    flattenedSelection = [
        fixture for fixtureGroup in selection for fixture in fixtureGroup]
    return flattenedSelection

def clear():
    return select()






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
