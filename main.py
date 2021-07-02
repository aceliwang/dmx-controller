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
# [TODO]: [CLEAN] DMX_BUFFER = [{1: (val := (int((k) * 255 / 88))), 2: val} for k in range(88)] ## this option drops less frames
# [TODO]: [CLEAN] using a dictionary drops some frames

# DEFAULTS


class default():
    on_intensity = 100
    off_intensity = 0
    fade_time = 2
    cue_name = 'Cue'
    # TODO: [CONFIG]

# HARDWARE


class DMXSender():
    '''
    Attributes:
        buffer (dict): buffer to be written to device (ie. effects are included)
        output (dict): copy of buffer showing DMX state
        raw_state (dict): dictionary of current DMX without effects written in
    '''
    curves = {
        'linear': lambda delta, start, end, duration: int(start + (end - start) * delta / duration) if duration > 0 else int(end),
        'delay': lambda delta, start, end, duration: int(end) if delta >= duration else None,
        'sine': lambda delta, start, end, duration: int(start + (end - start) * delta / duration) if duration > 0 else int(end),
        # TODO: [FIX] conversion to sine
    }
    active_effects = {
        # channel: "time started", parameters
    }

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
            new_values (dict): DMX values to be put into the buffer to be written ie. raw + effects
        '''
        self.buffer.update(new_values)
        self.output.update(new_values)
        return

    def update_raw(self, new_values):
        '''
        Args:
            new_values (dict): raw calculated DMX values to be stored without effects
        '''
        self.raw_state.update(new_values)

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

    def fade(self, *fade_arguments, effects=None):
        # TODO: [EFFECT]
        '''
        Uses arguments to write to buffer.

        Args:
            Args (list): [channel, end, duration, curve] eg. (1, 255, 2, 'linear')
            Note: LTP. args at end will take priority
            Note: effects: (channel, amplitude, start, horizontal shift, frequency)
        '''
        # TODO: refactor
        # Calculate channel start
        # ie. arg => (channel, start, end, duration, curve)
        argument_q = [(channel, self.raw_state.get(channel, 0), end, duration, curve)
                      for (channel, end, duration, curve) in fade_arguments]
        # Run loop and calculate new values
        start = time.perf_counter()
        bounds = {channel: (start, end) for (
            channel, start, end, *_) in argument_q}  # subject to LTP
        max_duration = max(
            [duration for (_, _, duration, _c) in fade_arguments])
        while True:
            # TODO: [ALT] investigate if generating lists of commands with popping the DMX buffer is more fast
            delta_time = time.perf_counter() - start
            new_values = {channel: value for (channel, start, end, duration, curve) in argument_q
                          if ((value := self.curves[curve](delta_time, start, end, duration)))}
            self.update_raw(new_values)
            # Add on effects
            # HELP: effect parameters = []
            # effected_values = {channel: Effect.effect(value, prop, form, size, wlength, hoz, ver)
            # for channel, () in effected_values.items()}
            # self.update_buffer(new_values.update(effected_values))
            self.update_buffer(new_values)
            remaining_channels = {channel: value for (channel, value) in new_values.items()
                                  if (bounds[channel][1] - bounds[channel][0]) * (value - bounds[channel][1]) < 0}
            if len(remaining_channels) == 0 and delta_time > max_duration:
                break
        return

    @classmethod
    def start_timecode(self, cuelist, cue_number=0):
        # Identify all cues with timecode
        ## {timing: cue_number}
        # NOTE: dict used to look for latest cue only
        timecode_cues = {
            cue.timing: cue_number
            for cue_number, cue in enumerate(Show.cuelists[cuelist])
            if isinstance(cue.timing, (float, int))
        }
        # Sort all timecodes
        timecode_list = [item for item in timecode_cues.items()]
        timecode_list.sort(key=lambda cue: cue[0])
        # Extract timings and cues
        timings = [timing for timing, *_ in timecode_list]
        cues = [cue for _, cue in timecode_list]

        def run_timecode(cuelist, cue_number):
            current_timing = Show.cuelists[cuelist][cue_number].timing
            start = time.time() - current_timing
            # TODO: [TIMECODE] how to handle run_timecode if started on a manual cue
            start_index = cues.index(cue_number)
            for i in range(len(timings[start_index:])):
                while (time.time() - start) < timings[start_index:][i]:
                    pass
                self.play_cue(cuelist, cues[start_index:][i])

        run_timecode(cuelist, cue_number)
        return


class Patching():

    patching = {}
    fixture_types = {}
    dmx_to_human = {}  # TODO: implement with patching

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

    def template(self, value, selection):
        return


class Programmer():
    FADE_TIME = 0  # TODO: [CONFIG] map to config
    CUELIST_MODE = False
    programmer = {
        'commands': OrderedDict(),  # TODO: [CLEAN] why OrderedDict?
        # 101: {
        #     'intensity': [('command', 100), ('overlapping command', 50)]
        # },
        # 102: {
        #     'intensity': None
        # }
    }
    selection = []

    def __init__(self):
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
        #
        # Functions
        def search_colour_palette(fixture, value):
            pal = Palettes.palettes['colours'][value]
            if fixture in pal['fixture']:
                return pal['fixture'][fixture]
            elif (fixture_type := Patching.patching[fixture][0]) in pal['fixture types']:
                return pal['fixture types'][fixture_type]
            else:
                return pal['default']

        # Handle value
        if isinstance(value, str):
            # If in palette
            if (value := value.lower()) in (pal := Palettes.palettes['colours']):
                for fixture in Programmer.select(selection):
                    colour = search_colour_palette(fixture, value)
            else:
                print(f'set_colour [-]: invalid colour {value}')
        # Check value
        #
        # Generate fade arguments
        # TODO: refactor
        if VERBOSE:
            print('set_colour [TODO]')
        if self.CUELIST_MODE:
            return fade_arguments
        else:
            DMXSender.fade(*fade_arguments)

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

    @classmethod
    def start_mouse_tracker(self, primary_position=(100, 100), x_channel=False, y_channel=False):
        # TODO: [REFACTOR]
        # Move mouse to primary position ie. position to be stuck in
        x0, y0 = primary_position
        mouse.move(x0, y0)
        # TODO: CLEAN
        x_value = DMXSender.raw_state.get(x_channel, 0)
        y_value = DMXSender.raw_state.get(y_channel, 0)

        def handle_mouse(evt):
            # Cancel tracking if click
            if isinstance(evt, mouse._mouse_event.ButtonEvent):
                mouse.unhook(handle_mouse)
            new_x, new_y = mouse.get_position()
            if not keyboard.is_pressed(42):  # if not shift key
                if new_x > x0:
                    x_value += 3
                    direction = 'right'
                elif new_x < x0:
                    x_value -= 3
                    direction = 'left'
            if not keyboard.is_pressed(29):  # if not ctrl key
                if new_y > y0:
                    y_value -= 3
                    direction = 'down'
                elif new_y < y0:
                    y_value += 3
                    direction = 'up'
            if VERBOSE:
                print(
                    f'handle_mouse [+]: mouse moved {direction} {new_x=} {x_value=}')
            mouse.move(x0, y0)
            fade_arguments = []
            if x_channel is not False:
                fade_arguments.append([x_channel, x_value, 0, 'linear'])
            if y_channel is not False:
                fade_arguments.append([y_channel, y_value, 0, 'linear'])
            DMXSender.fade(*fade_arguments)
            eel.update_node(node, (x_value, y_value))
            return x_value, y_value
        mouse.hook(handle_mouse)
        return

    def record_programmer(self, cuelist=None):
        if cuelist is None:
            cuelist = Show.selected_cuelist
        Show.cuelists[cuelist].append(
            Cue(
                name=default.cue_name,
                desc='',
                commands={
                    f'{instruction} {value}': self.commands_lib[
                        (action := instruction.split(' ')[-1])
                    ][1](
                        selection=self.select(instruction.split(' ')[:-1]),
                        value=value,
                        fade_time=default.fade_time,
                        curve='linear',  # TODO: does this take into account programmer?
                        cuelist_mode=True
                    ) for instruction, value in Programmer.programmer['commands'].items()
                    # TODO: [CLEAN]. Make programmer a Class?
                },
            )
        )
        Show.cuelists[cuelist].update_state()
        if GUI.state:
            eel.refresh_timeline()
        return

    def knock(self, *selection):
        # TODO: new programmer structure
        for selected in self.select(selection):
            del self.programmer[selected]
        if GUI.state:
            eel.refresh_programmer(self.js_programmer())
        return

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
    selected_cuelist = ''

    def import_showfile(self):
        # TODO: [MAKE]
        return

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
        dmx = [arg for _, fade_arguments in commands.items()
               for arg in fade_arguments]
        if VERBOSE:
            print(f'play_cue [+]: {dmx=}')
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
            cue.state = state
            for channel, value, *_ in [dmx for command in cue.commands.values() for dmx in command]:
                state[channel] = value
            return cue
        self.cues = list(map(calculate_state), self.cues)
        return


class Cue():
    '''
    Attributes:
        commands (dict): eg. 'pars si 100': 
            This can be split up further for definitions:
                selection = 'pars'
                action = 'si'
                value = '100'
                instruction = 'pars si'
                sub_command = 'si 100'

    '''

    def __init__(self, name=False, desc='', timing='manual'):
        # TODO
        self.name = name  # TODO: config
        self.desc = desc
        self.commands = {
            # f'{instruction} {value}': Programmer.commands_lib[]
        }
        self.timing = timing
        self.state = []
        return

    def update_commands(self):
        pass


# UI


class GUI():
    state = False

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
        self.state = True

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

    # ALT: change arguments to dictionaries instead
    aliases = {
        'on': ['si', default.on_intensity],
        'off': ['si', default.off_intensity],
        'clear': ['select', []]
    }

    def clean_line(line):
        # TODO: refactor
        '''
        Convert line into array with consideration of quotation marks and ranges.
        If there is an '=', this will be put into its separate line
        '''
        # Handle assignments ie. '='
        # eg. input: midnight=rgb(1,2,3) -> midnight = rgb(1,2,3)
        line = line.replace('=', ' = ')

        raw_args = line.split()
        # Handle quotation marks
        def remove_quotes(raw_args):
            args = []
            space_mode = False
            # Analyse each arg and see how many quotation marks are in
            for arg in raw_args:
                count = arg.count('"')
                if count == 0:
                    args.append(arg.replace('"', ''))
                elif count == 1:
                    if space_mode:
                        args[-1] = ' '.join([args[-1], arg.replace('"', '')])
                        space_mode = False
                    elif not space_mode:
                        space_mode = True
                        args.append(arg.replace('"', ''))
                elif count == 2:
                    args.append(arg.replace('"', ''))
                else:
                    raise Exception  # TODO: [EXCEPTIONS]
            return args
        args = remove_quotes(raw_args)
        # Handle ranges ie. '>'
        while '>' in args:
            op_index = args.index('>')
            previous_arg_index = op_index - 1
            following_arg_index = op_index + 1
            args[previous_arg_index] = ''.join(
                args[previous_arg_index:following_arg_index + 1])
            args.pop(op_index)  # Pop the operator
            args.pop(op_index)  # Pop the following arg
        if VERBOSE:
            print(f'clean_line [+]: {args=}')
        return args

    def parse(self, line):
        def alias_parser():
            # TODO: START
            return

        if line == '':
            return
        # Handle line
        # eg. @20 pars si 100 sc 'red blue' in 2 # name / description
        # eg. midnight = rgb(0, 0, 0)
        args = self.clean_line(line)
        # -> [@20, pars, si, 100, sc, red blue, in, 2, #, name, /, description]
        # -> [midnight, =, rgb]
        
        # If line is assignment
        if '=' in args:
            index = args.index('=')
            names = args[:index]
            values = args[index + 1:]
            # TODO: parse the assignment
            if 'rgb' in values or 'hsl' in values or 'pos' in values:
                parse_assignment(values)
        
        # If line is programming
            # Separate into commands
        token_list = []
        # eg. [@20, pars, si 100, sc 'red blue', in 2, # name, / description]
        token_builder = [] # temporary array to build the above commands
        keywords = self.commands_lib.keys() + \
            self.aliases.keys() + \
            Palettes.palettes['groups'].keys() + \
            ['in']
        keyword_starter = ('@', '#', '/')
        for arg in args:
            if token_builder != [] and (arg in keywords or arg[0] in keyword_starter):
                token_list.append(token_builder)
                token_builder = []
            token_builder.append(arg)
        token_list.append(token_builder)
        print(f'parse [+]: PROGRAM {token_list=}')
            # Interpret commands
        # NOTE: I obviously have to do a temp_cue but what happens if this is going into the programmer?
        programmer_builder = {
            'commands': [],
            'curve': 'linear',
            'fade_time': default.fade_time
        } # temp programmer before updating
        selection_builder = []
        command_list = []
        for token in token_list:
            if token[0][0] == '@': # TIMING
                programmer_builder['timing'] = int(token[0][1:])
            elif (start := token[0]) == '#': # NAME
                programmer_builder['name'] = ' '.join(token[1:])
            elif start == '/': # DESCRIPTION
                programmer_builder['description'] = ' '.join(token[1:])
            elif start.isnumeric(): # FIXTURE NUMBER
                selection_builder.append(start)
            elif start in Palettes.palettes['groups']: # GROUP NAME
                selection_builder.append(start)
            elif start == 'in': # FADE TIME
                programmer_builder['fade_time'] = int(token[1])
            elif start in self.aliases:
                alias_parser(token)
            else:
                command_list.append(token)
        # If no commands
        if len(command_list) == 0:
            # TODO: Do I need to update programmer selection?
            eel.refresh_selection(Programmer.select(selection_builder))
        # Run commands
        # If cuelist_mode, save commands to cuelist and don't run
        # If not cuelist_mode, save commands to programmer and run
        for action, *values in command_list:
            command_type, command_function, *other = self.commands_lib[action]
            value = ' '.join(values)
            if command_type == 'program':
                if Programmer.CUELIST_MODE: # if importing
                    # ALT: use classes
                    command = ' '.join(selection_builder + [action] + values)
                    fade_arguments = command_function(
                        selection=Programmer.select(selection_builder),
                        value=value,
                        fade_time=programmer_builder['fade_time'],
                        curve=programmer_builder['curve']
                    )
                    programmer_builder['commands'][command] = fade_arguments
                else: # if live
                    # Run command
                    command_function(
                        selection=Programmer.select(selection_builder),
                        value=value,
                        fade_time=programmer_builder['fade_time'],
                        curve=programmer_builder['curve']
                    )
                    # Update programmer
                    instruction = ' '.join([selection_builder], [action])
                    if instruction in Programmer.programmer['commands']:
                        del Programmer.programmer['commands'][instruction]
                    Programmer.programmer['commands'][instruction] = value
                    # ALT [TODO]: convert this to an update?
                    for fixture in Programmer.select(selection_builder):
                        parameter = other[0]
                        if value.isnumeric(): value = int(value)
                        if fixture not in Programmer.programmer:
                            Programmer.programmer[fixture] = {}
                        if parameter not in Programmer.programmer[fixture]:
                            Programmer.programmer[fixture][parameter] = {}
                        elif instruction in Programmer.programmer[fixture][parameter]:
                            del Programmer.programmer[fixture][parameter][instruction]
                        Programmer.programmer[fixture][parameter][instruction]= value
            elif command_type == 'meta':
                command_function(*values)
        # Run commands
        if GUI.state and Programmer.programmer:
            eel.refresh_programmer(Programmer.js_programmer())
        return

    def parse_file(file):
        # TODO: [REMAKE]
        return


if args.connect:
    DMXSender.connect()
if args.gui:
    GUI.start()
Palettes.load('groups', 'colours', 'positions')  # TODO: change to config

# EXPOSED FUNCTIONS


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


@eel.expose
def start_timecode(cuelist, cue_number=0):
    Show.start_timecode(cuelist, cue_number)
    return


@eel.expose
def start_mouse_tracker(primary_position, x_channel, y_channel):
    Programmer.start_mouse_tracker(primary_position, x_channel, y_channel)
    return

# DEBUG


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

# SHOW STATE


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


# do i want fixture IDs? How is group behaviour meant to work? What happens if I change the fixture numbers later? Should the group refer to the same fixture numbers or the same fixures


def select_cuelist(*cuelist):
    cuelist = cuelist[0]
    if cuelist not in cuelists:
        cuelists[cuelist] = []  # TODO: change to a dictionary
    global SELECTED_CUELIST
    SELECTED_CUELIST = cuelist
    if GUI_STATE:
        eel.refresh_selected_cuelist(SELECTED_CUELIST)
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


# TODO: delay needs to be fixed


# class group: # groups
#     def __init__(self, name, fixtures):
#         self.name = name
#         self.fixtures = fixtures
#     # usage: macs = g(macs, select())
#     def __str__(self):
#         return self.name
#     def plus(self, fixtures):
#         self.fixtures += fixtures

# repatch_fixture(101, 103)
# colour.record('blue', (0, 0, 255), [103])


# colour fade resource: https://www.sparkfun.com/news/2844
# HSI resource: https://cc.bingj.com/cache.aspx?q=hsi+to+rgb+for+led&d=4642254276268138&mkt=en-AU&setlang=en-GB&w=uASazgpuZIk_DdvTn7CgRM5S0bT1kRge
# HSI resource: https://blog.saikoled.com/post/44677718712/how-to-convert-from-hsi-to-rgb-white


# resources: STOP SCROLLING: https://stackoverflow.com/questions/4770025/how-to-disable-scrolling-temporarily
# DONE: implement a form of timecode
# TODO: effects
# TODO: dualshock controller
# TODO: rebuild server into python?
# TODO: calibration for mouse tracking for

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
