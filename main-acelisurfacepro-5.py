from pynput import mouse
# from loguru import logger
import cmd
import eel
import json
from DMXClient import DMXClient
import snoop
import time
import threading

# other https://www.dmxis.com/

CLIENT_CONNECTION_STATUS = False
BLIND_STATUS = False
dClient = DMXClient('PODU')



def connect():
    global CLIENT_CONNECTION_STATUS
    dClient.connect()
    CLIENT_CONNECTION_STATUS = True
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
    101: [1, 'trimmer par'],
    102: [9, 'trimmer par']
}
cuelists = {
    'mainCueList': [
        {
            'name': 'beat',
            'desc': 'pars flash',
            'timing': 'manual',  # or timecode
            'commands': {
                'pars on': [[1, 255, 0, 'linear']]
            },
            'state': [None, None, None] # put in cumulative values of beforehand
        },
        {
            'name': 'beat',
            'desc': 'pars flash', # how to get flashes working?????
            'timing': 'follow',
            'commands': {
                'pars off': [[1, 128, 0, 'linear']]
            },
            'state': [None, None, None]
        }
    ]
}

dmx_to_human = {
    219: [101, 'ON'],
    225: [101, 'R'],
}

# VARIABLES

DEFAULT_ON_INTENSITY = 100
DEFAULT_OFF_INTENSITY = 0

# SHOW STATE



@eel.expose
def play_cue(cue_list_name, cue_number=0):
    if cue_list_name in ACTIVE_CUELISTS:
        fade(cuelists[cue_list_name][cue_number]['dmx'])
        ACTIVE_CUELISTS[cue_list_name] = cue_number + 1
    return


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
programmer = {
    # 101: {
    #     'intensity': None
    # },
    # 102: {
    #     'intensity': None
    # }
}

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
        for key in p[self.type]:
            print(f'{key}')


colour = PaletteConstructor('colours')
position = PaletteConstructor('position')
beam = PaletteConstructor('beam')
custom = PaletteConstructor('custom')


import math
import keyboard


def set_intensity(selection, value, fade_time=0, curve='linear', verbose=False, cuelist_mode=False):
    # VALUE OPTIONS
    # STR: group name or value
    # INT: value
    if isinstance(value, str):
        if (intensity_palette := p.get('intensity')) and value not in intensity_palette.keys():
            print(f'[ERROR]: Invalid intensity chosen')
            return
        elif value.isnumeric():
            value = int(value)
    elif value < 0 or value > 100:
        print(f'[ERROR]: Intensity {value} out of bounds')
        return
    translate_value = lambda value : math.ceil((value / 100) * 255)
    value = translate_value(value)
    fade_arguments = []
    for fixture in select(selection):
        iChannel = findChannel(fixture, 'intensity')
        fade_arguments.append((iChannel, value, fade_time, curve))
    if verbose: print(f'[CHECK]: {fade_arguments}')
    if cuelist_mode: return fade_arguments
    else:
        print(fade_arguments)
        fade(*fade_arguments)
    return fade_arguments

def setColour(selection, value, fade=0, curve='linear', verbose=False, cuelist_mode=False):
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
        return
    # if seeBlindDMX:
    #     print(f'[CHECK]: {programDMX}')
    blindDMX.extend(programDMX)
    # if push:
    #     dClient.write(blindDMX)
        # fade((channel, end, length), curve)
        ## how does this work for colour
    return programDMX

# command > dmxValues ie. program DMX > cueList
# command > dmxValues

def setPosition(selection, value, fade=0, curve='linear', verbose=False, cuelist_mode=False):
    # VALUE OPTIONS
    # STR
    # TUPLE
    if isinstance(value, str):
        if (position_palette := p.get('positions')):
            return
        elif position_palette: return
    return

active_effects = {

}

def set_effect(selection, value_args, fade=0, curve='linear', verbose=False, cuelist_mode=False):
    # [selection, parameter, formula, amplitude, absolute/relative, vertical shift, horizontal shift, spread, buddy]
    formula = {
        'sine': lambda x, amp, absrel, ver, hor, freq: amp * math.sin(freq * x),
        'cosine': lambda x: math.cosine(x),
        'ramp': lambda x: x % 1
    }
    def effect():
        return
    timer = time.perf_counter()
    while True:
        deltaTime = time.perf_counter() - timer
        if CLIENT_CONNECTION_STATUS: dClient.write(new_values)
    return

def run_effects():
    return


def findChannel(fixture, parameter):
    # fixture: fixture number according to patching
    # parameter: fixture type parameter name according to json
    address, fixtureType = patching[fixture]
    dmxChannel = address - 1 + \
        fixture_types[fixtureType]['mapping'][parameter]['channel']
    return dmxChannel


# do i want fixture IDs? How is group behaviour meant to work? What happens if I change the fixture numbers later? Should the group refer to the same fixture numbers or the same fixures

# TODO: update palettes if change fixture number

def select(*selection):
    groupNames = p['groups'].keys()
    if len(selection) == 0: return []
    if isinstance(selection[0], list): selection = selection[0]
    def convert_or_expand(arg):
        if isinstance(arg, str):
            if '>' in arg:
                limits = arg.split('>')
                return [number for number in range(int(limits[0]), int(limits[1])+1)]
            elif arg in groupNames: return p['groups'][arg]
            else: return [int(arg)]
        elif isinstance(arg, int):
            return [arg]
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

ACTIVE_CUELISTS = {
    'main': 0
}

SELECTED_CUELIST = None



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
    print(args)
    return args

class cli(cmd.Cmd):
    intro = 'Command-line interface for'
    pass

aliases = {
    'on': [set_intensity, DEFAULT_ON_INTENSITY],
    'off': [set_intensity, DEFAULT_OFF_INTENSITY],
    'clear': [select, []],
}

def select_cuelist(*cuelist):
    cuelist = cuelist[0]
    if cuelist not in cuelists:
        cuelists[cuelist] = []
    global SELECTED_CUELIST
    SELECTED_CUELIST = cuelist
    if GUI_STATE: eel.refresh_selected_cuelist(SELECTED_CUELIST)
    return

def knock(*selection):
    for selected in select(selection):
        del programmer[selected]
    if GUI_STATE: eel.refresh_programmer(programmer)
    return

@eel.expose
# @snoop
def read_line(line, cuelist=None, groupNames=["macs", "pars"]):
    if line == '': return
    cuelist = SELECTED_CUELIST
    commands_dict = {
        # command: (type, function, parameter)
        # 'select': {'function': 'select'},
        # 'record': None,
        # 'sp': None,
        'patch': ('meta', patch),
        'startcl': ('meta', select_cuelist),
        'scl': ('meta', select_cuelist),
        'in': None,
        'seti': ('program', set_intensity, 'intensity'),
        'si': ('program', set_intensity, 'intensity'),
        'sc': ('program', setColour),
        'knock': ('meta', knock)
    }
    args = clean_line(line)
    ### split into commands and arguments
    command_list = []
    temp_commands = []
    for arg in args: # if 
        if temp_commands != [] and (arg in commands_dict.keys() or
                                    arg[0] in ('@', '#', '/') or
                                    arg in groupNames or
                                    arg in ('in') or
                                    arg in aliases.keys()):
            command_list.append(temp_commands)
            temp_commands = []
        temp_commands.append(arg)
    command_list.append(temp_commands)
    print(f'command list: {command_list}')
    
    ###
    ### perform commands
    cue = {
        'commands': {},
        'fadeTime': 0,
        'timing': 'manual',
    }
    selection = []
    temp_commands = []
    if '=' in command_list: # assignment type
        index = command.index('=')
        before_args = command[:index] # name
        after_args = command[index+1:] # assignments
        if 'rgb' in after_args or 'hsl' in after_args: # colour
            parse_assignment(after_args)
        elif 'pos' in after_args:
            parse_assignment(after_args)
        else:
            parse_assignment(after_args)
    for command in command_list: # cue line
        if command[0][0] == '@': cue['timing'] = int(command[0][1:]) # if timing
        # needs to figure out how to do a selection
        elif (start := command[0]) == '#': cue['name'] = ' '.join(command[1:]) # if cue name
        elif start == '/': cue['description'] = ' '.join(command[1:]) # if cue description
        elif start in groupNames: selection.append(start) # if group selection
        elif start.isnumeric(): selection.append(start) # if fixture selection
        elif start == 'in': cue['fadeTime'] = int(command[1]) # if fade time
        elif start in aliases.keys():
            do = aliases[start]
            dmx = do[0](select(selection), do[1:])
            temp_commands.append(command)
        else: # if command
            temp_commands.append(command)
    print(cue)
    print('cuelist', cuelist)
    if len(temp_commands) == 0: eel.refresh_selection(select(selection))
    for command in temp_commands:
        if (command_type := commands_dict[command[0]][0]) == 'program':
            if cuelist:
                cue['commands'][' '.join(selection + command)] = commands_dict[command[0]][1](
                    selection=select(selection),
                    value=command[1],
                    fade_time=cue['fadeTime'],
                    curve='linear',
                    cuelist_mode=True
                )
                del cue['fadeTime']
                cuelists[SELECTED_CUELIST].append(cue)
                calculate_state(SELECTED_CUELIST)
            else:
                commands_dict[command[0]][1](
                    selection=select(selection),
                    value=command[1],
                    fade_time=cue['fadeTime'],
                    curve='linear',
                    cuelist_mode=False
                )
            if GUI_STATE and not BLIND_STATUS:
                print('refresh timeline')
                eel.fillTimeline()
            for selected in select(selection):
                parameter = commands_dict[command[0]][2]
                value = command[1]
                if selected not in programmer: programmer[selected] = {}
                programmer[selected][parameter] = value
        elif command_type == 'meta':
            commands_dict[command[0]][1](*command[1:])
    if programmer: eel.refresh_programmer(programmer)
    # return a cue: {timing, fadeTime, name} and temp commands [macs si 25] [macs sp home]
    return cue

from functools import reduce
def parse_assignment(string):
    if ('rgb' in string):
        string = string.replace('rgb', '')
        assignmentType = 'rgb'
    elif ('hsl' in string):
        string = string.replace('hsl', '')
        assignmentType = 'hsl'
    elif ('pos' in string):
        string = string.replace('pos', '')
    elif ('select' in string):
        string = string.replace('select', '')
    def reduce_function(a, b):
        if b in (' ', '(', ')'): return a
        else: return a + b
    args = [int(i) for i in reduce(reduce_function, list(string), '').split(',')]
    return assignmentType, args

def calculate_state(cue_list):
    state = [None] * 256
    for cue in cuelists[cue_list]:
        for command in cue['commands'].values():
            for channel, value, fade, curve in command:
                state[channel] = value
        cue['state'] = state
    return

def save():
    show_file = {
        'palettes': p,
        'fixture types': fixture_types,
        'patching': patching,
        'cue lists': cuelists,
    }
    return show_file

def import_show_file(show_file):
    return


# TODO: delay needs to be fixed

# print(read_line("@100 pars sc red # cue name / when they start dancing"))
# read_line("101 102 sc blue")
# commands_dict[command][function](commands_dict[command][args]) # TODO


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

def play_cue(cuelist, cue_number=False):
    if not cue_number:
        if cuelist in ACTIVE_CUELISTS:
            cue_number = ACTIVE_CUELISTS[cuelist]
        else: cue_number = -1
    ACTIVE_CUELISTS[cuelist] = cue_number
    fade(cuelists[cuelist][cue_number])
    return True

@eel.expose
def print_in_javascript(msg):
    print(msg)

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
def get_palette():
    return p

@eel.expose
def get_cuelists():
    return cuelists

@eel.expose
def get_programmed():
    return programmer

import copy

@eel.expose
def get_patching():
    patching_details = copy.deepcopy(patching)
    for fixture_id, fixture_details in patching_details.items():
        fixture_details += [fixture_types[fixture_details[1]]['channels']]
        patching_details[fixture_id] = fixture_details
    return patching_details

@eel.expose
def get_active_cue_list():
    return ACTIVE_CUELISTS

@eel.expose
def get_selected_cuelist():
    return SELECTED_CUELIST


GUI_STATE = False

def startGUI():
    global GUI_STATE
    GUI_STATE = True
    eel.init('app')
    eel.start('index.html', size=(300, 200), mode='edge')  # Start
    return

def stopGUI():
    eel.stop()


gui = threading.Thread(target=startGUI)
gui.start()
# startGUI()

currentDMX = [0] * 256
def fade(*instructions, effects=None): # channel, end, length, curve
    # instruction = array of tuples.
    # NOTE: LTP. instructions at the end take priority
    # each tuple = (channel, end, duration, curve)
    # eg. (1, 255, 2, 'linear')
    # NOTE EFFECTS: (channel, amplitude, start, horizontal shift, frequency)
    # STEP 1: calculate each channel start
    # ie. tuple => (channel, start, end, duration) eg. (1, 0, 255, 2, 'linear')
    # instructions = [(1, 255, 2, 'linear'), (1, 0, 2, 'delay')]
    instruction_q = [(channel, currentDMX[channel], end, duration, curve) for (channel, end, duration, curve, *others) in instructions]
    # STEP 2: run loop. calculate new values for each channel according to duration and write
    curves = {
        'linear': lambda delta, start, end, duration : int(start + (end - start) * delta / duration) if duration > 0 else int(end),
        'delay': lambda delta, start, end, duration : int(end) if delta >= duration else None,
    }
    # STEP 2A: calculate new values according to multiple instructions and add these instructions together
    timer = time.perf_counter()
    # directions = [int((end - start) / abs(end - start)) for (channel, end, length), start in zip(fadingChannels, currentValues)]
    # previousValues = [i for i in currentValues]
    end_values = {channel: (start, end) for (channel, start, end, duration, curve) in instruction_q} # looks at LTP and order of array
    max_duration = max([duration for (a, b, duration, c) in instructions])
    # end_values = {1: 0}
    # break criteria: if deltaTime >= duration && previous_value <= or >= end_value
    while True:
        # TODO: when to break out? how to compare to end value
        # CONTINUE GOING CRITERIA: if (end - start) * (previous - end) < 0, continue
        # CONTINUE GOING CRITERIA: if (end - start) * (previous - end) >= 0, achieved > remove from comparison. Once all removed from comparison, break?
        deltaTime = time.perf_counter() - timer
        # calculate values according to curves
        new_values = {channel: value for (channel, start, end, duration, curve) in instruction_q if ((value := curves[curve](deltaTime, start, end, duration)) is not None)}
        # {1: 255} then {1: 0}
        if CLIENT_CONNECTION_STATUS: dClient.write(new_values)
        for channel in new_values.keys():
            currentDMX[channel] = new_values[channel]
        previous_values = new_values
        end_checker = {channel: previous_value for (channel, previous_value) in previous_values.items() if (
            (end_values[channel][1] - end_values[channel][0]) * (previous_value - end_values[channel][1]) < 0
            )}
        if len(end_checker) == 0 and (deltaTime > max_duration): break
    return previous_values

import mouse
@eel.expose
def init_listen_to_movement(startingPosition=[50, 50], channel=1):
    x_coordinate, y_coordinate = startingPosition
    mouse.move(x_coordinate, y_coordinate)
    new_x = currentDMX[channel]
    new_y = 0
    def listen_to_movement(event):
        nonlocal new_x, new_y
        if isinstance(event, mouse._mouse_event.ButtonEvent):
            print('buttonevent', listen_to_movement)
            mouse.unhook(listen_to_movement)
            # print('unhooked')
        x, y = mouse.get_position()
        if x > x_coordinate: 
            new_x += 3
            print('right', x, new_x)
        elif x < x_coordinate:
            new_x -= 3
            print('left', x, new_x)
        if y > y_coordinate:
            new_y -= 3
            print('down', y, new_y)
        elif y < y_coordinate:
            new_y += 3
            print('up', y, new_y)
        mouse.move(x_coordinate, y_coordinate)
        fade([channel, new_y, 0, 'linear'])
        eel.change_intensity((new_x, new_y))
        return new_x, new_y
    mouse.hook(listen_to_movement)
    return





# colour fade resource: https://www.sparkfun.com/news/2844