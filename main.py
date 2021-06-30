import mouse
import copy
from functools import reduce
from collections import OrderedDict
# from pynput import mouse
# from loguru import logger
import cmd
import eel
import json
from DMXClient import DMXClient
import snoop
import time
import threading
import argparse
import math
import keyboard

# TODO: [LIST]
# 1. [REFACTOR]
# 2. [EFFECT]
# Other: [POSITION], [CUSTOM]
# Clear function


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--gui', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--connect', action='store_true')
    args = parser.parse_args()

# other https://www.dmxis.com/

BLIND_STATUS = False  # TODO WHY THIS
VERBOSE = args.verbose
# DMX_BUFFER = [{1: (val := (int((k) * 255 / 88))), 2: val} for k in range(88)] ## this option drops less frames
# using a dictionary drops some frames

# HARDWARE


class DMXSender():
    '''
    Attributes:
        buffer (dict): buffer to be written to device (ie. effects are included)
        output (dict): copy of buffer showing DMX state
        raw_state (dict): dictionary of current DMX without effects written in
    '''

    def __init__(self):
        self.buffer = {}
        self.output = {}
        self.raw_state = {}
        self.client = DMXClient('PODU')
        self.CONNECTION_STATUS = False
        return

    def update_buffer(self, new_values):
        '''
        Args:
            new_values (dict): DMX values to be put into the buffer
        '''
        self.buffer.update(new_values)
        self.output.update(new_values)
        return

    def send_dmx(self, Hz=44):
        '''
        Args:
            Hz (int): DMX refresh rate. Note USB driver can only handle up to 29. Light may handle even less.
        '''
        start = time.time()
        counter = 0
        while True:
            next_frame = start + counter / Hz
            while time.time() < next_frame:
                pass
            if bool(self.buffer):
                self.client.write(self.buffer)
                self.buffer = {}
            counter += 1

    def connect(self):
        '''
        Connect to client device. Updates connection_status.
        '''
        self.client.connect()
        self.CONNECTION_STATUS = True
        self.sender = threading.Thread(target=self.send_dmx)
        self.sender.start()
        return

    def fade(self, arguments):
        '''
        Uses arguments to write to buffer.

        Args:
            []
        '''
        # TODO: refactor
        return

    def start_timecode(cuelist, cue_number=0):
        return


class Patching():

    patching = {}
    fixture_types = {}

    def import_patching(self):
        '''
        Load patching and import with either override or update
        '''
        # TODO: [IMPORT] new_function
        return

    def import_fixture_type(self, *fixture_types):
        for fixture_type in fixture_types:
            if fixture_type in fixture_types:
                # TODO: provide override or skip function
                continue
            with open(f'{fixture_type}.json', 'r') as f:
                fixture_types[fixture_type] = json.load(f)
            print(f'import_fixture_type [+]: {fixture_type} imported')
        return

    def map_patching(self):
        channel_assignment = [-1] + [0] * 512
        # ALT: change to a reduce function
        for _, (address, fixture_type) in self.patching.items():
            for channel in range(address, address + self.fixture_types[fixture_type]['channel']):
                channel_assignment[channel] += 1
            return channel_assignment

    def patch_fixtures(self, fixture_type, fixture_no, quantity, address=None, gap=0):
        '''
        Args:
            fixture_type (str): type of fixture
            fixture_no (int): number at which first fixture is patched
            quantity (int): number of fixtures
            address (int): custom address. If none, patch to next available.
            gap (int): gap between addresses
        '''
        # TODO: default address if None, fill next address
        # TODO: nil address required
        if fixture_type not in self.fixture_types:
            print(
                f'patch_fixtures [ERROR] Fixture type {fixture_type} does not exist')
            return
        channel_qty = self.fixture_types[fixture_type]['channels']
        start = address
        end = address + quantity * channel_qty
        if sum(self.map_patching()[start:end]) > 0:
            print(
                f'patch_fixtures [ERROR] Address targets are already occupied.')
        else:
            self.patching.update({
                fixture_no + i: [fixture_type, address + i * (channel_qty + gap)]
                for i in range(quantity)
            })
        return

    def check_patching(self):
        '''
        Check if there are any overlapping channels.
        '''
        # TODO: check if patching exceeds address 512
        overlapping_channels = [channel for channel, counter in enumerate(
            self.map_patching()) if counter > 1]
        if overlapping_channels:
            print(
                f'check_patching [-]: Overlapping channels are {str(overlapping_channels)}')
        else:
            print(f'check_patching [+]: No overlapping channels')
        return overlapping_channels

    def renumber_fixture(self, old, new):
        # TODO: update Palette groups if fixture number is changed
        if new not in self.patching:
            self.patching[new] = self.patching.pop(old)
        else:
            print(f'renumber_fixture [-]: fixture {new} already exists')
        return

    def readdress_fixture(self, fixture_no, address):
        fixture_type = self.patching[fixture_no][0]
        channel_qty = self.fixture_types[fixture_type]['channels']
        new_channels = self.map_patching()[address:address + channel_qty]
        if sum(new_channels) == 0:
            self.patching[fixture_no][1] = address
        else:
            print('repatch_fixture [-]: target address already occupied')
        return

# PROGRAMMING


class Palettes():
    palettes = {
        'groups': {},
        'intensity': {},
        'colours': {},
        'positions': {},
        'beams': {},
        'custom': {},
    }

    @classmethod
    def load(self, *palette_list):
        for file in palette_list:
            with open(f'{file}.json') as f:
                self.palettes[file] = json.load(f)
        return

class Programmer():
    FADE_TIME = 0  # TODO: [CONFIG] map to config
    CUELIST_MODE = False
    programmer = {
        'commands': OrderedDict(), # TODO: [CLEAN] why OrderedDict?
        # 101: {
        #     'intensity': [('command', 100), ('overlapping command', 50)]
        # },
        # 102: {
        #     'intensity': None
        # }
    }

    def __init__(self):
        self.selection = []
        self.selected_cuelist = None
        # TODO: [REFACTOR]
        return

    def select(*selection):
        # Handle selection
        if len(selection) == 0:
            return []
        if isinstance(selection[0], list):
            selection = selection[0]
        # TODO: should I be handling non-existent fixtures in here or later on?
        # TODO: select backward ranges, buddies, odds/even, steps

        def translate_or_expand(arg):
            '''
            Look through the arguments in the selection list.
            If group name, convert to fixtures.
            If range, expand range.
            '''
            if isinstance(arg, str):
                # Handle groups
                if arg in Palettes.palettes['groups']:
                    return Palettes.palettes['groups'][arg]
                # Handle range
                elif '>' in arg:
                    # TODO: Handle unbound ranges
                    lower_bound, *upper_bound = arg.split('>')
                    if upper_bound:
                        upper_bound = upper_bound[0]
                    return [fixture for fixture in range(
                        int(lower_bound),
                        int(upper_bound) + 1)]
                # Handle fixture number
                else:
                    return [int(arg)]
            elif isinstance(arg, int):
                return [arg]
        return [fixture for i in selection for fixture in translate_or_expand(i)]

    def set_intensity(self, selection, value, fade_time, curve='linear'):
        '''
        Set intensity of 'selection' to 'value' across 'fade_time'

        Args:
            selection (list, int, str): either group, fixture or multiple fixtures
            value (int, str): intensity value between 0 and 100 or palette name
        '''
        # Handle value
        if isinstance(value, str):
            if value in (pal := Palettes.palettes['intensity']):
                value = pal[value]
            elif value.isnumeric():
                value = int(value)
            else:
                print(f'set_intensity [-]: invalid intensity {value}')
                return
        # Check value
        if value < 0 or value > 100:
            print(f'set_intensity [-]: intensity {value} is out of bounds')
            return
        # Translate value to DMX
        dmx_value = math.ceil((value / 100) * 255)
        # Generate fade arguments
        fade_arguments = [
            [self.find_channel(fixture, 'intensity'),
             dmx_value, fade_time, curve]
            for fixture in self.select(selection)
        ]
        if self.CUELIST_MODE:
            return fade_arguments
        DMXSender.fade(*fade_arguments)
        return

    def set_colour(self, selection, value, fade_time, curve='sine'):
        '''
        Set colour of 'selection' to 'value' across 'fade_time'

        Args:
            selection (list, int, str): either group, fixture or multiple fixtures
            value (int, str): colour value as HSI, RGB or palette name
        '''
        # Handle value
        if isinstance(value, str):
            if value in (pal := Palettes.palettes['colours']):
                value = pal[value]
            else:
                print(f'set_colour [-]: invalid colour {value}')
        # Check value
        # Translate value to DMX
        # Generate fade arguments
        # TODO: refactor

        if self.CUELIST_MODE:
            return fade_arguments
        DMXSender.fade(*fade_arguments)
        return

    def set_position(self, selection, value, fade_time, curve='linear'):
        '''
        Set position of 'selection' to 'value' across 'fade_time'

        Args:
            selection (list, int, str): either group, fixture or multiple fixtures
            value (int, str): position value as Pan/Tilt or palette name
        '''
        # TODO: [POSITION]
        return

    def set_parameter(self, selection, parameter, value, fade_time, curve='linear'):
        '''
        Example: set(pars, intensity, 100)
        '''
        # TODO: [CUSTOM] is value meant to be DMX, does it find range. What happens if channel is divided into different groups
        dmx_value = translate(parameter, value)
        fade_arguments = [
            [self.find_channel(fixture, parameter),
             dmx_value, fade_time, curve]
            for fixture in self.select(selection)
        ]
        return

    def find_channel(fixture, parameter):
        '''
        Translate parameter to DMX channel

        Args:
            fixture (int, tuple): either a fixture number or a tuple with the address and fixture_type already provided 
            parameter (str): which parameter is being searched for
        '''
        # Handle fixture
        if isinstance(fixture, (tuple, list)):
            address, fixture_type = fixture
        else:
            address, fixture_type = Patching.patching[int(fixture)]
        # Find channel
        channel = address + \
            Patching.fixture_types[fixture_type]['mapping'][parameter]['channel'] - 1
        return channel

    def track_mouse_move(self, x, y):
        pass

    @classmethod
    def js_programmer(self):
        '''
        Converts programmer into javascript-friendly arrays instead
        '''
        # TODO: [CLEAN] figure out if this is really needed. Do I need the order?
        def arrayed(x):
            if isinstance(x, dict):
                return {parameter: list(value_dict.items()) for parameter, value_dict in x.items()}
            else:
                return x
        js_programmer = {
            key: arrayed(value) for key, value in self.programmer.items()
        }
        return js_programmer


class Show():
    '''
    Controls playback

    Attributes:
        active_cuelists: cuelists currently in playback eg. {'showcase': 0}
    '''
    cuelists = {}
    active_cuelists = {
        # cuelist: cue_number
    }

    def play_cue(self, cuelist, cue_number=False, source='back'):
        # TODO: [REFACTOR]
        # Handle cue number
        if not cue_number:
            if cuelist in self.active_cuelists:
                cue_number = self.active_cuelists[cuelist]
            else:
                cue_number = 0
        # Update active_cuelists
        self.update_active(cuelist, cue_number)
        # Find what commands have been generated
        commands = self.cuelists[cuelist][cue_number]['commands']
        # Flatten all commands to extract dmx
        dmx = [arg for _, fade_arguments in commands.items() for arg in fade_arguments]
        if VERBOSE: print(f'play_cue [+]: {dmx=}')
        DMXSender.fade(*dmx)
        if source == 'back':
            eel.remove_cue_from_selection(cuelist, cue_number)
            eel.add_cue_to_selection(cuelist, cue_number + 1)
        return

    def update_active(self, cuelist, cue_number):
        self.active_cuelists[cuelist] = cue_number

    def save(self):
        # TODO: [EXPORT]
        show_file = {
            'palettes': Palettes.palettes,
            'fixture types': Patching.fixture_types,
            'patching': Patching.patching,
            'cuelists': Show.cuelists,
        }
        return show_file


class Cuelist():
    def __init__(self):
        self.cues = []
        return

    @property
    # TODO: [CLEAN] what does this decorator do?
    def cues(self):
        return self.cues

    def add_cue(self, parameters):
        # TODO: [REFACTOR] refactor from record
        self.cues.append()
        return

    def update_state(self):
        state = [None] * 256
        # TODO: [EFFECT] store effect into state somehow
        def calculate_state(cue):
            cue['state'] = state
            for channel, value, *_ in [dmx for command in cue['commands'].values() for dmx in command]:
                state[channel] = value
            return cue
        self.cues = list(map(calculate_state), self.cues)
        return


class Cue():
    def __init__(self):
        # TODO
        return

# UI


class GUI():
    GUI_STATE = False

    def start_gui():
        '''
        Initialise eel.js
        '''
        eel.init('app')
        eel.start('index.html', mode='edge')
        return

    @classmethod
    def start(self):
        self.gui = threading.Thread(target=self.start_gui)
        self.gui.start()
        self.GUI_STATE = True

    @classmethod
    def stop(self):
        self.gui.join()


class CMD():
    # TODO: tidy up commands_lib
    commands_lib = {
        # command: (type, function, parameter)
        # 'select': {'function': 'select'},
        # 'record': None,
        # 'sp': None,
        'patch': ('meta', Patching.patch_fixtures),
        # 'startcl': ('meta', select_cuelist),
        # 'scl': ('meta', select_cuelist),
        'in': None,
        'seti': ('program', Programmer.set_intensity, 'intensity'),
        'si': ('program', Programmer.set_intensity, 'intensity'),
        'sc': ('program', Programmer.set_colour, 'colour'),
        # 'knock': ('meta', knock),
        # 'record': ('meta', record)
    }

    def clean_line(line):
        # TODO: refactor
        '''
        Convert line into array with consideration of quotation marks and ranges
        '''
        raw_args = line.split(' ')
        # Handle quotation marks
        def remove_quotes(raw_args):
            args = []
            space_mode = False
            # Analyse each arg and see how many quotation marks are in
            for arg in raw_args:
                count = arg.count('"')
                if count == 0: args.append(arg.replace('"', ''))
                elif count == 1:
                    if space_mode:
                        args[-1] = ' '.join([args[-1], arg.replace('"', '')])
                        space_mode = False
                    elif not space_mode:
                        space_mode = True
                        args.append(arg.replace('"', ''))
                elif count == 2: args.append(arg.replace('"', ''))
                else:
                    raise Exception # TODO: [EXCEPTIONS]
            return args
        args = remove_quotes(raw_args)
        # Handle ranges ie. '>'
        while '>' in args:
            op_index = args.index('>')
            previous_arg_index = op_index - 1
            following_arg_index = op_index + 1
            args[previous_arg_index] = ''.join(args[previous_arg_index:following_arg_index + 1])
            args.pop(op_index) # Pop the operator
            args.pop(op_index) # Pop the following arg
        if VERBOSE: print(f'clean_line [+]: {args=}')
        return args

    def parse(self, line):
        if line == '':
            return
        # Handle line
        args = self.clean_line(line)
        command_list = []
        command_builder = []  # TODO: what is this for?
        keywords = [self.commands_lib.keys()] + \
            [Palettes.palettes['groups'].keys()]
        for arg in args:
            if command_builder != [] and arg in keywords:
                command_list.append(command_builder)
                command_builder = []
            command_builder.append(arg)
        command_list.append(command_builder)
        print(f'parse [+]: {command_list=}')
        return

    def parse_file(file):
        # TODO: [REMAKE]
        return

if args.connect: DMXSender.connect()
if args.gui: GUI.start()
Palettes.load('groups', 'colours', 'positions')  # TODO: change to config

### EXPOSED FUNCTIONS

@eel.expose
def get_palette():
    return Palettes.palettes

@eel.expose
def get_cuelists():
    return Show.cuelists

@eel.expose
def get_programmer():
    # TODO: return a function that deals with this internally
    return Programmer.js_programmer()

@eel.expose
def get_patching():
    patching_details = copy.deepcopy(Patching.patching)
    # Add on channel count for easier processing on GUI
    return {fixture_number: fixture_details + [Patching.fixture_types[fixture_details[0]]['channels']]
            for fixture_number, fixture_details in patching_details.items()}

@eel.expose
def get_active_cuelists():
    return Show.active_cuelists

@eel.expose
def get_selected_cuelist():
    # TODO: [CLEAN]
    return Show.selected_cuelist

@eel.expose
def play_cue(cuelist, cue_number=False, source='back'):
    Show.play_cue(cuelist, cue_number, source)
    return

### DEBUG

def rl(line):
    CMD.parse(line)
    return

def bye():
    try:
        DMXSender.sender.join()
        GUI.join()
    finally:
        exit()

_______OLDCODE___________ = None
# OLD CODE





# DATA OBJECTS

selection = []
patching = {
    101: [1, 'trimmer par'],
    102: [9, 'trimmer par']
}
cuelists = {
    'mainCueList': [
        {
            'name': 'beat',
            'desc': 'pars flash',
            'timing': 0.0,  # or timecode or follow
            'commands': {
                'pars on': [[1, 255, 0, 'linear'], [9, 255, 0, 'linear']],
                'effects': []
            },
            # put in cumulative values of beforehand
            'state': [None, None, None]
        },
        {
            'name': 'beat',
            'desc': 'pars flash',  # how to get flashes working?????
            'timing': 1.0,
            'commands': {
                'pars off': [[1, 0, 0, 'linear'], [9, 0, 0, 'linear']]
            },
            'state': [None, None, None]
        },
        {
            'name': 'beat',
            'desc': 'pars flash',
            'timing': 2.0,  # or timecode or follow
            'commands': {
                'pars on': [[1, 255, 0, 'linear'], [9, 255, 0, 'linear']]
            },
            # put in cumulative values of beforehand
            'state': [None, None, None]
        },
        {
            'name': 'beat',
            'desc': 'pars flash',  # how to get flashes working?????
            'timing': 'manual',
            'commands': {
                'pars off': [[1, 128, 0, 'linear']]
            },
            'state': [None, None, None]
        },
    ]
}

# TODO: with patching
dmx_to_human = {
    219: [101, 'ON'],
    225: [101, 'R'],
}

# VARIABLES

DEFAULT_ON_INTENSITY = 100
DEFAULT_OFF_INTENSITY = 0
DEFAULT_FADE_TIME = 2
DEFAULT_CUE_NAME = 'Cue'

# SHOW STATE


@eel.expose
def start_timecode(cuelist, cue_number=0):
    cuelist = 'mainCueList'
    timecodePrep = {}
    # for index, cue in enumerate(cuelists[cuelist]):
    #     # if I want to run multiple cues? I do want to run multiple cues together
    #     # for index, cue in enumerate(cuelists[list]):
    #     timing = cue['timing']
    #     if not isinstance(timing, (float, int)):
    #         continue
    #     if timing in timecodePrep:
    #         timecodePrep[timing].append(index)
    #     else:
    #         timecodePrep[timing] = [index]
    timecodePrep = {cue['timing']: index for index, cue in enumerate(
        cuelists[cuelist]) if isinstance(cue['timing'], (float, int))}
    # if time
    timecodeList = [item for item in timecodePrep.items()]
    timecodeList.sort(key=lambda x: x[0])
    timings = [timing for timing, *_ in timecodeList]
    matchedCues = [cues for _, cues in timecodeList]

    def activate_timecode(cuelist, cue_number):
        # TORESUME
        startTime = time.time() - cuelists[cuelist][cue_number]['timing']
        # cuelist = cuelists[list] if extracting the cuelist
        startIndex = matchedCues.index(cue_number)
        for i in range(len(timings[startIndex:])):
            while (time.time() - startTime) < timings[startIndex:][i]:
                pass
            print(f'[PLAYBACK: {cuelist}]: {time.time() - startTime}')
            play_cue(cuelist, matchedCues[startIndex:][i])
            # TODO: select the relevant cue on the gui
    activate_timecode(cuelist, cue_number)
    return


# def play_cue(cue_list_name, cue_number=0):
#     if cue_list_name in ACTIVE_CUELISTS:
#         if cuelists[cue_list_name][cue_number]['timing'] == 0:
#             # start_timecode()
#             pass
#         fade(cuelists[cue_list_name][cue_number]['dmx'])
#         ACTIVE_CUELISTS[cue_list_name] = cue_number + 1
#     return

# palette groups for multiple parameters using function arguments (colour=), stored in



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


def set_colour(selection, value, fade_time=0, curve='linear', verbose=False, cuelist_mode=False):
    if isinstance(value, str) and value not in p['colours'].keys():
        print(f'[ERROR]: Colour "{value}" does not exist.')
        return
    # TODO: validate tuple
    selection = select(selection)
    fade_arguments = []

    def write_colour_to_DMX(fixture, colour_value):
        # ARG: colour_value = [red, green, blue]
        # colour_value = [255, 0, 0], default = red, green, blue
        dmxChanges = []
        # red, green, blue = colour_value
        # colour_value = {}
        address, fixture_type = patching[fixture]
        # colourType = fixture_types[fixture_type]['colour_mapping']
        colourType = 'rgb'
        colourDict = {
            'r': 'red',
            'g': 'green',
            'b': 'blue',
            'a': 'amber',
            'w': 'white',
            'u': 'uv'
        }

        def translate_colour(colour_value, colourType):
            # colour_value: given in HSI
            # colourType: RGB, RGBA, RGBAW, RGBW, ?UV
            return colour_value
            if colourType == 'rgb':
                return colour_value
            if colourType == 'rgbw':
                # converts HSI to RGBW
                hueDeg, sat, intensity = colour_value
                hueDeg = hueDeg % 360
                hueRad = hueDeg * math.pi / 180
                sat = max(0, min(sat, 1))
                intensity = max(0, min(intensity, 1))
                if hueDeg < 120:
                    cos_h = math.cos(hueRad)
                    cos_1047_h = math.cos(math.pi / 3 - hueRad)
                    red = sat * 255 * intensity / 3 * \
                        (1 + cos_h/cos_1047_h)  # TODO: check fraction
                    green = sat * 255 * intensity / \
                        3 * (1 + (1 - cos_h/cos_1047_h))
                    blue = 0
                    white = 255 * (1 - sat) * intensity
                elif hueDeg < 240:
                    hueRad = hueRad - math.pi * 2 / 3
                    cos_h = math.cos(hueRad)
                    cos_1047_h = math.cos(math.pi / 3 - hueRad)
                    green = sat * 255 * intensity / 3 * (1 + cos_h/cos_1047_h)
                    blue = sat * 255 * intensity / 3 * \
                        (1 + (1 - cos_h/cos_1047_h))
                    red = 0
                    white = 255 * (1 - sat) * intensity
                else:
                    hueRad = hueRad - math.pi * 4 / 3
                    cos_h = math.cos(hueRad)
                    cos_1047_h = math.cos(math.pi / 3 - hueRad)
                    blue = sat * 255 * intensity / 3 * (1 + cos_h/cos_1047_h)
                    red = sat * 255 * intensity / 3 * \
                        (1 + (1 - cos_h/cos_1047_h))
                    green = 0
                    white = 255 * (1 - sat) * intensity
            return [round(i) for i in (red, green, blue, white)]
        return [(findChannel((address, fixture_type), colourDict[colour]),
                # TODO
                 end := translate_colour(colour_value, colourType)[index],
                 fade_time,
                 'sine') for index, colour in enumerate(colourType)]
        rChannel = findChannel(fixture, 'red')
        gChannel = findChannel(fixture, 'green')
        bChannel = findChannel(fixture, 'blue')
        dmxChanges.extend([rChannel, r, gChannel, g, bChannel, b])
        if len(a) > 0:
            aChannel = findChannel(fixture, 'amber')
            dmxChanges.extend([aChannel, a[0]])
        dmxChanges = [(rChannel, r, fade_time, 'sine')]
        return dmxChanges  # return [(address, end, length, curve) * 3]
    if isinstance(value, str):
        palettes = p['colours']
        value = value.lower()
        for fixture in selection:
            try:
                colourValue = palettes[value]['fixtures'][fixture]
                break
            except KeyError:
                try:
                    colourValue = palettes[value]['fixture types'][patching[fixture][1]]
                    break
                except KeyError:
                    colourValue = palettes[value]['default']

            # finally: # TODO: fix
            #     colourValue = palettes[value]['default']
            fade_arguments.extend(write_colour_to_DMX(fixture, colourValue))
    elif isinstance(value, tuple):
        colourValue = value
        for fixture in selection:
            fade_arguments.append(write_colour_to_DMX(fixture, colourValue))
    if verbose:
        print(f'[CHECK]: {fade_arguments}')
    if cuelist_mode:
        return fade_arguments
    else:
        print(fade_arguments)
        fade(*fade_arguments)
    return fade_arguments

# command > dmxValues ie. program DMX > cueList
# command > dmxValues


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
        if CLIENT_CONNECTION_STATUS:
            dClient.write()
    return



# do i want fixture IDs? How is group behaviour meant to work? What happens if I change the fixture numbers later? Should the group refer to the same fixture numbers or the same fixures


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
previousMousePosition = (None, None)


# def on_move(x, y):
#     global previousMousePosition
#     previousX, previousY = previousMousePosition
#     direction = []
#     if x > previousX:
#         direction.append('right')
#     elif x < previousX:
#         direction.append('left')
#     if y > previousY:
#         direction.append('down')
#     elif y < previousY:
#         direction.append('up')
#     print(f'Pointer moved {" and ".join(direction)}')
#     previousMousePosition = (x, y)


# def on_click(*args):
#     return False


@eel.expose
def init_listen_to_movement(startingPosition=[50, 50], channel=1):
    x_coordinate, y_coordinate = startingPosition
    mouse.move(x_coordinate, y_coordinate)
    # new_x = currentDMX[channel]
    new_x = 22
    new_y = 0

    def listen_to_movement(event):
        nonlocal new_x, new_y
        if isinstance(event, mouse._mouse_event.ButtonEvent):
            print('buttonevent', listen_to_movement)
            mouse.unhook(listen_to_movement)
            # print('unhooked')
        x, y = mouse.get_position()
        if not keyboard.is_pressed(42):  # shift key
            if x > x_coordinate:
                new_x += 3
                print('right', x, new_x)
            elif x < x_coordinate:
                new_x -= 3
                print('left', x, new_x)
        if not keyboard.is_pressed(29):  # ctrl key
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

# listener = mouse.Listener(
#     on_move=on_move,
#     on_click=on_click
# )

# previousMousePosition = mouse.Controller().position
# listener.start()


aliases = {
    'on': [set_intensity, DEFAULT_ON_INTENSITY],
    'off': [set_intensity, DEFAULT_OFF_INTENSITY],
    'clear': [select, []],
}


def select_cuelist(*cuelist):
    cuelist = cuelist[0]
    if cuelist not in cuelists:
        cuelists[cuelist] = []  # TODO: change to a dictionary
    global SELECTED_CUELIST
    SELECTED_CUELIST = cuelist
    if GUI_STATE:
        eel.refresh_selected_cuelist(SELECTED_CUELIST)
    return


def knock(*selection):  # TODO: new programmer structure
    for selected in select(selection):
        del programmer[selected]
    if GUI_STATE:
        eel.refresh_programmer(programmer)
    return


def record():
    cue = {
        'name': DEFAULT_CUE_NAME,
        'desc': ' ',
        'commands': {
            f'{instruction} {value}': commandsDict[(instructionArgs := instruction.split(' '))[-1]][1](
                selection=select(instructionArgs[:-1]),
                value=value,
                fade_time=DEFAULT_FADE_TIME,
                curve='linear',
                cuelist_mode=True
            ) for instruction, value in programmer['commands'].items()
        },
        'timing': 'manual',
    }
    cuelists[SELECTED_CUELIST].append(cue)
    calculate_state(SELECTED_CUELIST)
    if GUI_STATE:
        eel.refresh_timeline()
    return


@eel.expose
def read_line(line, cuelist=None, groupNames=["macs", "pars"]):
    if line == '':
        return
    cuelist = SELECTED_CUELIST

    args = clean_line(line)
    # split into commands and arguments
    command_list = []
    temp_commands = []
    for arg in args:  # if
        if temp_commands != [] and (arg in commandsDict.keys() or
                                    arg[0] in ('@', '#', '/') or
                                    arg in groupNames or
                                    arg in ('in') or
                                    arg in aliases.keys()):
            command_list.append(temp_commands)
            temp_commands = []
        temp_commands.append(arg)
    command_list.append(temp_commands)
    print(f'read_line command list: {command_list}')

    ###
    # perform commands
    cue = {
        'commands': {},
        'fadeTime': 0,
        'timing': 'manual',
    }
    selection = []
    temp_commands = []
    if '=' in command_list:  # assignment line
        index = command.index('=')
        before_args = command[:index]  # name
        after_args = command[index+1:]  # assignments
        if 'rgb' in after_args or 'hsl' in after_args:  # colour
            parse_assignment(after_args)
        elif 'pos' in after_args:
            parse_assignment(after_args)
        else:
            parse_assignment(after_args)
    for command in command_list:  # cue line
        if command[0][0] == '@':
            cue['timing'] = int(command[0][1:])  # if timing
        # needs to figure out how to do a selection
        elif (start := command[0]) == '#':
            cue['name'] = ' '.join(command[1:])  # if cue name
        elif start == '/':
            cue['description'] = ' '.join(command[1:])  # if cue description
        elif start in groupNames:
            selection.append(start)  # if group selection
        elif start.isnumeric():
            selection.append(start)  # if fixture selection
        elif start == 'in':
            cue['fadeTime'] = int(command[1])  # if fade time
        elif start in aliases.keys():
            do = aliases[start]
            dmx = do[0](select(selection), do[1:])
            temp_commands.append(command)
        else:  # if command
            temp_commands.append(command)
    print(f'read_line selected cuelist: {cuelist}')
    if len(temp_commands) == 0:
        eel.refresh_selection(select(selection))
    for command in temp_commands:
        if (command_type := commandsDict[command[0]][0]) == 'program':
            if cuelist:
                cue['commands'][' '.join(selection + command)] = commandsDict[command[0]][1](
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
                commandsDict[command[0]][1](
                    selection=select(selection),
                    value=command[1],
                    fade_time=cue['fadeTime'],
                    curve='linear',
                    cuelist_mode=False
                )
            if GUI_STATE and not BLIND_STATUS:
                eel.refresh_timeline()
            instruction = ' '.join(selection + [command[0]])
            value = command[1]
            if instruction in programmer['commands']:
                # change insertion order
                del programmer['commands'][instruction]
            programmer['commands'][instruction] = value
            for fixture in select(selection):  # save into programmer: visualise
                parameter = commandsDict[command[0]][2]
                value = int(
                    command[1]) if command[1].isnumeric() else command[1]
                if fixture not in programmer:
                    programmer[fixture] = {}
                if parameter not in programmer[fixture]:
                    programmer[fixture][parameter] = OrderedDict()
                elif instruction in programmer[fixture][parameter]:
                    del programmer[fixture][parameter][instruction]
                programmer[fixture][parameter][instruction] = value
        elif command_type == 'meta':
            commandsDict[command[0]][1](*command[1:])
    if GUI_STATE and programmer:
        eel.refresh_programmer(wrap_programmer(programmer))
    # print(f'read_line cue package: {cue}')
    # return a cue: {timing, fadeTime, name} and temp commands [macs si 25] [macs sp home]
    return cue


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
        if b in (' ', '(', ')'):
            return a
        else:
            return a + b
    args = [int(i)
            for i in reduce(reduce_function, list(string), '').split(',')]
    return assignmentType, args

def import_show_file(show_file):
    return


# TODO: delay needs to be fixed

# print(read_line("@100 pars sc red # cue name / when they start dancing"))
# read_line("101 102 sc blue")
# commandsDict[command][function](commandsDict[command][args]) # TODO


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


currentDMX = [0] * 256


def fade(*instructions, effects=None):  # channel, end, length, curve
    # instruction = array of tuples.
    # NOTE: LTP. instructions at the end take priority
    # each tuple = (channel, end, duration, curve)
    # eg. (1, 255, 2, 'linear')
    # NOTE EFFECTS: (channel, amplitude, start, horizontal shift, frequency)
    # STEP 1: calculate each channel start
    # ie. tuple => (channel, start, end, duration) eg. (1, 0, 255, 2, 'linear')
    # instructions = [(1, 255, 2, 'linear'), (1, 0, 2, 'delay')]
    instruction_q = [(channel, currentDMX[channel], end, duration, curve)
                     for (channel, end, duration, curve, *others) in instructions]
    # STEP 2: run loop. calculate new values for each channel according to duration and write
    curves = {
        'linear': lambda delta, start, end, duration: int(start + (end - start) * delta / duration) if duration > 0 else int(end),
        'delay': lambda delta, start, end, duration: int(end) if delta >= duration else None,
        # TODO: convert to sine
        'sine': lambda delta, start, end, duration: int(start + (end - start) * delta / duration) if duration > 0 else int(end),
    }
    # STEP 2A: calculate new values according to multiple instructions and add these instructions together
    timer = time.perf_counter()
    # directions = [int((end - start) / abs(end - start)) for (channel, end, length), start in zip(fadingChannels, currentValues)]
    # previousValues = [i for i in currentValues]
    end_values = {channel: (start, end) for (
        channel, start, end, duration, curve) in instruction_q}  # looks at LTP and order of array
    max_duration = max([duration for (a, b, duration, c) in instructions])
    # end_values = {1: 0}
    # break criteria: if deltaTime >= duration && previous_value <= or >= end_value
    while True:  # TODO: change to generator function
        # TODO: when to break out? how to compare to end value
        # CONTINUE GOING CRITERIA: if (end - start) * (previous - end) < 0, continue
        # CONTINUE GOING CRITERIA: if (end - start) * (previous - end) >= 0, achieved > remove from comparison. Once all removed from comparison, break?
        deltaTime = time.perf_counter() - timer
        # calculate values according to curves
        new_values = {channel: value
                      for (channel, start, end, duration, curve) in instruction_q if ((value := curves[curve](deltaTime, start, end, duration)) is not None)}
        # {1: 255} then {1: 0}
        effected_values
        if channel in active_effects:
            effected_values[channel]
        DMX_BUFFER.update(new_values)
        for channel in new_values.keys():
            currentDMX[channel] = new_values[channel]
        previous_values = new_values
        end_checker = {channel: previous_value for (channel, previous_value) in previous_values.items() if (
            (end_values[channel][1] - end_values[channel][0]) *
            (previous_value - end_values[channel][1]) < 0
        )}
        if len(end_checker) == 0 and (deltaTime > max_duration):
            break
    return previous_values




@eel.expose
def record_programer_to_cuelist(cuelist=None):
    if cuelist is None:
        cuelist = SELECTED_CUELIST
    cuelists[cuelist].append(programmer)


# colour fade resource: https://www.sparkfun.com/news/2844
# HSI resource: https://cc.bingj.com/cache.aspx?q=hsi+to+rgb+for+led&d=4642254276268138&mkt=en-AU&setlang=en-GB&w=uASazgpuZIk_DdvTn7CgRM5S0bT1kRge
# HSI resource: https://blog.saikoled.com/post/44677718712/how-to-convert-from-hsi-to-rgb-white


# resources: STOP SCROLLING: https://stackoverflow.com/questions/4770025/how-to-disable-scrolling-temporarily
# DONE: implement a form of timecode
# TODO: effects
# TODO: dualshock controller
# TODO: rebuild server into python?
# TODO: calibration for mouse tracking for


effectsLib = {
    1: "time since it started", parameters: hi
}
# how to manage state


def in_fade():
    if channel in effectsLib:
        modifier = effect(channel, size, )
        return original_value + modifier


# cuelist = [commands, effects=[to start]]
def effect(channel, lib, parameters):

    # if relative: apply to fade value?
    # TODO: if absolute: override fade value?
    # tbh this should all be in a generator function with fade
    def sine(x): return size * math.sin(length * x + hoz) + ver
    def tangent(x): return size * math.tan(length * x + hoz) + ver
    def none(x): return x
    # x is the time value since start of the effect
    # TODO: clamp value between 0 and 255
    return
