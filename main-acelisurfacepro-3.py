from pynput import mouse
from loguru import logger
import cmd
import eel
import json
from DMXClient import DMXClient
import snoop
import re

dClient = DMXClient('PODU')

def connect():
    dClient.connect()
    return

# load file

# interpret line
# parse line
# split everything with spaces
# combine operators
# interpret

# DATA OBJECTS

blindDMX = []
selection = []
p = {}
fixture_types = {}
patching = {
    101: [219, 'trimmer par'],
    102: [8, 'trimmer par']
}
cue_lists = {
    'mainCueList': [
        {
            'name': 'beat',
            'timing': 'manual',  # or timecode
            'dmx': [255, 255, 255]
        },
        {

        }
    ]
}

# PROGRAMMING
# PALETTES
palettes_to_load = [
    'groups',
    'colours',
    'positions'
]

def load():
    for file in palettes_to_load:
        with open(f'{file}.json') as f:
            p[file] = json.load(f)


load()
# palette groups for multiple parameters using function arguments (colour=), stored in

# PROGRAMMING


class PaletteConstructor():
    global p

    def __init__(self, paletteType):
        self.type = paletteType

    def palette_template(self, value, selection):
        palette = {
            'default': ['default'],
            'fixture types': {},
            'fixtures': {}
        }
        for fixture in selection:
            fixtureType = patching[fixture][1]
            if isinstance(fixture, int):
                palette['fixtures'][fixture] = value
            if isinstance(fixture, str):
                palette['fixture types'][fixtureType] = value
        return palette

    def verifyValue(self, value):
        if self.type == 'colour':
            return isinstance(value, tuple) and all([index < 5 and channelValue >= 0 and channelValue <= 255 for index, channelValue in enumerate(value)])
    
    def verifySelection(self, selection):
        selection = select(selection)
        return all([fixture in patching.keys() for fixture in selection])

    def record(self, name, value, selection):
        if self.verifyValue(value) and self.verifySelection(selection):
            # p[f'{self.type}s'][name] = value
            p[f'{self.type}s'][name] = self.palette_template(value, selection)
        eel.populateGroups()

    def rename(self, oldName, newName):
        return

    def __str__(self):
        return f'{self.type} constructor'

    def show(self):
        def iterdict(dict):
            for key, value in dict.items():
                if isinstance(value, dict):
                    iterdict(value)
                else:
                    print(f'{prefix}')
            return
        prefix = ''
        for key, value in p[self.type]:
            print(f'{key}')


colour = PaletteConstructor('colour')
position = PaletteConstructor('position')
beam = PaletteConstructor('beam')
custom = PaletteConstructor('custom')


def recordPalette(type, value):
    # TODO
    return


def setIntensity(selection, value, fade=0, seeBlindDMX=False, push=False):
    if isinstance(value, str) and value not in p.get('intensity').keys():
        print(f'[ERROR]: Invalid intensity chosen')
        return
    if value < 0 or value > 100:
        print(f'[ERROR]: Intensity {value} out of bounds')
        return
    def translate_value(value):
        return int((value / 100) * 255)
    selection = select(selection)
    value = translate_value(value)
    programDMX = []
    for fixture in selection:
        iChannel = findChannel(fixture, 'intensity')
        programDMX.extend([iChannel, value])
    if seeBlindDMX:
        print(f'[CHECK]: {programDMX}')
    blindDMX = programDMX
    if push:
        dClient.write(blindDMX)
    return programDMX

def setColour(selection, value, fade=0, seeBlindDMX=True, push=False):
    if isinstance(value, str) and value not in p['colours'].keys():
        print(f'[ERROR]: Colour "{value}" does not exist.')
        return
    # TODO: validate tuple
    selection = select(selection)
    programDMX = []
    def write_colour_to_DMX(fixture, colourValue):
        dmxChanges = []
        r, g, b, *a = colourValue
        rChannel = findChannel(fixture, 'red')
        gChannel = findChannel(fixture, 'green')
        bChannel = findChannel(fixture, 'blue')
        dmxChanges.extend([rChannel, r, gChannel, g, bChannel, b])
        if len(a) > 0:
            aChannel = findChannel(fixture, 'amber')
            dmxChanges.extend([aChannel, a[0]])
        return dmxChanges
    if isinstance(value, str):
        palettes = p['colours']
        for fixture in selection:
            try:
                colourValue = palettes[value]['fixtures'][fixture]
            except KeyError:
                colourValue = palettes[value]['fixture types'][patching[fixture][1]]
            finally:
                colourValue = palettes[value]['default']
            programDMX.extend(write_colour_to_DMX(fixture, colourValue))
    elif isinstance(value, tuple):
        colourValue = value
        for fixture in selection:
            programDMX.extend(write_colour_to_DMX(fixture, colourValue))
    def translate_colour():
        blindDMX.extend()
        return ()
    if seeBlindDMX:
        print(f'[CHECK]: {programDMX}')
    blindDMX.extend(programDMX)
    if push:
        dClient.write(blindDMX)
    return programDMX

# command > dmxValues ie. program DMX > cueList
# command > dmxValues


def findChannel(fixture, parameter):
    # fixture: fixture number according to patching
    # parameter: fixture type parameter name according to json
    address, fixtureType = patching[fixture]
    dmxChannel = address - 1 + \
        fixture_types[fixtureType]['mapping'][parameter]['channel']
    return dmxChannel


# do i want fixture IDs? How is group behaviour meant to work? What happens if I change the fixture numbers later? Should the group refer to the same fixture numbers or the same fixures

# TODO: update palettes if change fixture number

def select(*args):
    selection = args
    groupNames = p['groups'].keys()
    if len(selection) == 0: return []
    if isinstance(selection[0], list): selection = selection[0]
    def convert_or_expand(arg):
        if isinstance(arg, str):
            if '>' in arg:
                limits = arg.split('>')
                return [number for number in range(int(limits[0]), int(limits[1])+1)]
            elif arg in groupNames:
                return p['groups'][arg]
            else:
                return [int(arg)]
        elif isinstance(arg, int):
            return [arg]
    print([fixture for i in selection for fixture in convert_or_expand(i)])
    return [fixture for i in selection for fixture in convert_or_expand(i)]
    # TODO: select backwards ranges, every second, etc.

def clear():
    return select()


def set(fixtureGroup, parameter, value):
    def translateValue():
        return
    for fixture in fixtureGroup:
        address, fixtureType = patching[fixture]
        dmxChannel = address + \
            fixtureType[fixture]['mapping'][parameter].channel - 1
        dmxValue = translate(parameter, value)
        blindDMX.extend([dmxChannel, value])
        DMXClient.write()

# set(pars, intensity, 100)


# PATCHING

def import_fixture_type(*fixtureType):
    for fixture in fixtureType:
        if fixture not in fixture_types.keys():
            with open(f'{fixture}.json', 'r') as f:
                fixture_types[fixture] = json.load(f)
            print(f'[SUCCESS] Fixture type {fixture} imported.')
        else:
            print(f'[ERROR] Fixture type {fixture} already imported.')
    return


def patch(fixtureType, fixtureNo, address=None, step=False):
    return

# // patching
# fixtureType.patch((101, 105), 'start address', 'default ie. name.json')
# (101, 105).patch(fixtureType, 'start address', 'step address')
# patch 'trimmer pars' 101 > 105 from 322 every 100
# // figure out how to do
# // patch dmx output device

def map_patching():
    channelAssignment = [-1] + [0] * 255
    for fixtureNo, (address, fixtureType) in patching.items():
        for channel in range(address, address + fixture_types[fixtureType]['channels'] - 1):
            channelAssignment[channel] += 1
    return channelAssignment


def check_patching():
    overlappingChannels = [index for index, counter in enumerate(
        map_patching()) if counter > 1]
    if overlappingChannels:
        print(
            f'[ERROR] Patching tested. Overlapping channels are: {str(overlappingChannels)}')
    else:
        print(f'[SUCCESS] Patching tested. No overlapping channels.')
    return overlappingChannels


def renumber_fixture(oldFixtureNo, newFixtureNo):
    # if type(oldFixtureNo) is not int: print
    if newFixtureNo not in patching.keys():
        # validate key not already used
        patching[newFixtureNo] = patching.pop(oldFixtureNo)
    else:
        print(f'[ERROR]: Renumbering fixture. Fixture {newFixtureNo} already exists.')
    return

def repatch_fixture(fixtureNo, newAddress):
    # TODO: have to test entire run not just start
    # print('test', len(check_patching()))
    channel_count = fixture_types[patching[fixtureNo][1]]['channels']
    new_channels = map_patching()[newAddress:newAddress + channel_count]
    if sum(new_channels) == 0:
        patching[fixtureNo][0] = newAddress
    else:
        print('[ERROR]: Repatching fixture. Target channels already occupied. ')
    return


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

previousMousePosition = (None, None)


def on_move(x, y):
    global previousMousePosition
    previousX, previousY = previousMousePosition
    direction = []
    if x > previousX:
        direction.append('right')
    elif x < previousX:
        direction.append('left')
    if y > previousY:
        direction.append('down')
    elif y < previousY:
        direction.append('up')
    print(f'Pointer moved {" and ".join(direction)}')
    previousMousePosition = (x, y)


def on_click(*args):
    return False


listener = mouse.Listener(
    on_move=on_move,
    on_click=on_click
)

previousMousePosition = mouse.Controller().position
# listener.start()

# PLAYBACK

activeCueLists = {
    'main': 0
}



# MAIN

if __name__ == '_main_':
    pass


# PARSER


def clean_line(line):
    # quoted = [(m.start(0), m.end(0)) for m in re.finditer('"(.*?)"', line)]
    args = line.split(' ') # startcl, "main, cuelist" vs startcl, main cuelist, 
    def line_to_commands(line):
        args = []
        spaceMode = False
        for arg in line:
            count = arg.count('"')
            if count == 0:
                args.append(arg.replace('"',''))
            elif count == 1:
                if spaceMode:
                    args[-1] = ' '.join([args[-1], arg.replace('"', '')])
                    spaceMode = False
                elif not spaceMode:
                    spaceMode = True
                    args.append(arg.replace('"',''))
            elif count == 2:
                args.append(arg.replace('"', ''))
        return args
    args = line_to_commands(args)
    while '>' in args:
        originalOperatorIndex = args.index('>')
        arg1Index = originalOperatorIndex - 1
        arg2Index = originalOperatorIndex + 1
        args[originalOperatorIndex -
             1] = ''.join(args[arg1Index:arg2Index + 1])
        args.pop(originalOperatorIndex)  # pop operator
        args.pop(originalOperatorIndex)  # pop arg 2
    return args

class cli(cmd.Cmd):
    intro = 'Command-line interface for'
    pass

defaultOnIntensity = 100
defaultOffIntensity = 0

aliases = {
    'on': setIntensity,
    'off': setIntensity
}

@eel.expose
# @snoop
def read_line(line, cueList=False, groupNames=["macs", "pars"]):
    commandsDict = {
        # 'select': {'function': 'select'},
        # 'record': None,
        # 'seti': 'setIntensity',
        # 'si': 'setIntensity',
        'sc': setColour,
        # 'sp': None,
        'patch': 'patch',
        # 'startcl': 'startCueList',
        'in': None
    }
    args = clean_line(line)
    ### split into commands and arguments
    command_list = []
    temp_commands = []
    for arg in args:
        if temp_commands != [] and (arg in commandsDict.keys() or
                                    arg[0] in ('@', '#', '/') or
                                    arg in groupNames or
                                    arg in ('in') or
                                    arg in aliases.keys()):
            command_list.append(temp_commands)
            temp_commands = []
        temp_commands.append(arg)
    command_list.append(temp_commands)
    ###
    ### perform commands
    cue = {}
    selection = []
    for command in command_list:
        if command[0][0] == '@': cue['timing'] = int(command[0][1:])
        # needs to figure out how to do a selection
        elif command[0] == '#': cue['name'] = ' '.join(command[1:])
        elif command[0] == '/': cue['description'] = ' '.join(command[1:])
        elif command[0] in groupNames: selection.append(command[0])
        elif command[0] == 'in': cue['fadeTime'] = int(command[1])
        elif command[0].isnumeric(): selection.append(command[0])
        else:
            print(select(selection))
            commandsDict[command[0]](select(selection), *command[1:])
    def startCueList():
        return
    print(command_list)
    return cue, command_list


# print(read_line("@100 pars sc red # cue name / when they start dancing"))
# read_line("101 102 sc blue")
# commandsDict[command][function](commandsDict[command][args]) # TODO


def read_file(file):
    cueListMode = False
    cueGroupMode = False
    groupNames = [name for name in p[groups].keys()]
    for line in file:
        read_line(line, cueListMode, groupNames)


def read_script(file):
    for line in file:
        args = clean_line(line)
        command = args.pop(0)
        if command in ('select', 's'):  # select
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
            setColour()
        elif command in ('setb', 'sb'):
            continue
        elif command in ('set'):
            continue
        elif command in ('flash'):
            continue
        elif command in ('import'):
            continue
        elif args[0] == '=' and args[1] == 'select':  # unknown variable
            # groupName = select 1 2 3 > 100
            groupName = args[1]

            groups()


# class group: # groups
#     def __init__(self, name, fixtures):
#         self.name = name
#         self.fixtures = fixtures
#     # usage: macs = g(macs, select())
#     def __str__(self):
#         return self.name
#     def plus(self, fixtures):
#         self.fixtures += fixtures

# TESTS

clean_line('pars si 100')
select('1', '2', '3>5')
# setColour(['pars'], 'red', True)
import_fixture_type('trimmer par')
findChannel(101, 'red')
clear()
# repatch_fixture(101, 103)
# colour.record('blue', (0, 0, 255), [103])

### JAVASCRIPT EXPOSED

@eel.expose
def palette():
    return p


def startGUI():
    eel.init('app')
    eel.start('index.html', size=(300, 200), mode='edge')  # Start

# startGUI()
