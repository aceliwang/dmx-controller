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
    programmer_fade_time = 2
    cue_fade_time = 2
    cue_name = 'Cue'
    # TODO: [CONFIG]
    effect_size = 100
    effect_length = 1
    effect_hoz = 0
    effect_ver = 0
    effect_absrel = 'rel'

    @staticmethod
    def is_number(arg):
        try:
            float(arg)
            return True
        except ValueError:
            return False

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
        # 1: "time started", parameters
    }
    # TODO: change below to instance attributes if implementing multiple output devices
    buffer = {}
    output = {}
    raw_state = {}
    client = DMXClient('PODU')
    CONNECTION_STATUS = False

    def __init__(self):
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
            if bool(self.active_effects):
                self.run_effects(self, time.time())
            if bool(self.buffer):
                self.client.write(self.buffer)
                self.buffer = {}
            counter += 1
        return

    @classmethod
    def connect(self):
        '''
        Connect to client device. Updates connection_status.
        '''
        self.client.connect()
        self.CONNECTION_STATUS = True
        self.sender = threading.Thread(target=self.send_dmx, args=[self])
        self.sender.start()
        return

    def run_effects(self, start):
        '''
        Args:
            effects (dict): (channel: start, parameters)
            Note: parameters = size, wavelength, hoz, ver shift, abs/rel
        '''
        # Supplied effects
        effected_values = {channel: Programmer.effect(self.raw_state.get(channel, 0), time=self.active_effects[channel][0], start=start, parameters=self.active_effects[channel][1])
                               for channel in self.active_effects}
        self.update_buffer(self, effected_values)
        return

    @classmethod
    def fade(self, *fade_arguments, effects={}):
        # TODO: [EFFECT]
        '''
        Uses arguments to write to buffer.

        Args:
            Args (list): [channel, end, duration, curve] eg. (1, 255, 2, 'linear')
            Note: LTP. args at end will take priority
            
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
        print(f'{fade_arguments=}')
        max_duration = max(
            [duration for (_, _, duration, _c) in fade_arguments])
        # Add effects to active effects
        effects = {channel: (start, parameters)
                   for channel, parameters in effects.items()}
        self.active_effects.update(effects)
        for channel, (_, parameters) in effects.items():
            if parameters['form'] == 'none':
                del self.active_effects[channel]
        while True:
            # TODO: [ALT] investigate if generating lists of commands with popping the DMX buffer is more fast
            delta_time = time.perf_counter() - start
            new_values = {channel: value for (channel, start, end, duration, curve) in argument_q
                          if ((value := self.curves[curve](delta_time, start, end, duration)) is not None)}
            self.update_raw(self, new_values)
            self.update_buffer(self, new_values)
            remaining_channels = {channel: value for (channel, value) in new_values.items()
                                  if (bounds[channel][1] - bounds[channel][0]) * (value - bounds[channel][1]) < 0}
            if len(remaining_channels) == 0 and delta_time > max_duration:
                break
        return
    
    @classmethod
    def fade_instant(self, *fade_arguments):
        new_values = {channel: value for channel, value, *_ in fade_arguments}
        self.update_raw(self, new_values)
        self.update_buffer(self, new_values)
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

    @classmethod
    def import_fixture_type(self, *fixture_types):
        for fixture_type in fixture_types:
            if fixture_type in self.fixture_types:
                # TODO: provide override or skip function
                continue
            with open(f'{fixture_type}.json', 'r') as f:
                self.fixture_types[fixture_type] = json.load(f)
            print(f'import_fixture_type [+]: {fixture_type} imported')
        return

    @classmethod
    def map_patching(self):
        channel_assignment = [-1] + [0] * 512
        # ALT: change to a reduce function
        for _, (fixture_type, address) in self.patching.items():
            for channel in range(address, address + self.fixture_types[fixture_type]['channels']):
                channel_assignment[channel] += 1
        return channel_assignment

    @classmethod
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
        fixture_info = self.fixture_types[fixture_type] 
        channel_qty = fixture_info['channels']
        start = address
        end = address + quantity * channel_qty
        if sum(self.map_patching()[start:end]) > 0:
            print(
                f'patch_fixtures [ERROR] Address targets are already occupied.')
            return
        else:
            patching_update = {
                fixture_no + i: [fixture_type, address + i * (channel_qty + gap)]
                for i in range(quantity)
            }
            if (cell_qty := fixture_info.get('cells', 0)) > 0:
                for i in range(quantity):
                    for cell_no in range(cell_qty):
                        # cell_no = cell_no + 1 # offset from 0
                        cell_id = f'cell_{cell_no + 1}'
                        cell = fixture_info['mapping'].get(cell_id, {})
                        print(cell_id, cell.get('default#', 0))
                        patching_update.update(
                            {
                                fixture_no + i + cell.get('default#', 0): [fixture_type, address + i * (channel_qty + gap), cell_id]
                            }
                        )

            self.patching.update(patching_update)
            ## [TODO]: Set defaults
            # for item in patching_update.items():
            #     DMXSender.fade([channel, end, 0, 'linear'])
            print(f'patching_fixtures [+]: {fixture_type} patched at {start}')
        return self.patching

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
        'effects': {},
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

    def record(self, name, value, selection):
        return  # TODO


class Programmer():

    '''
    Attributes:
        CUELIST_MODE: either False or specified as cuelist
    '''

    FADE_TIME = 0  # TODO: [CONFIG] map to config
    CUELIST_MODE = False
    FADE_MODE = False
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
                    return [float(arg)]
            elif isinstance(arg, (int, float)):
                return [arg]
        return [fixture for i in selection for fixture in translate_or_expand(i)]

    @staticmethod
    def clamp(value):
        return max(min(255, round(value)), 0)

    def activate_cuelist_mode(self, cuelist):
        if cuelist in Show.cuelists:
            self.CUELIST_MODE = cuelist
            print(f'active_cuelist_mode [+]: successfully activated')
            if GUI.state: eel.refresh_selected_cuelist(cuelist)
        else:
            # TODO: make new cuelist
            new_cuelist = Cuelist(name=cuelist)
            Show.cuelists.append(new_cuelist)
            print(f'activate_cuelist_mode [-]: cuelist created')
        return

    @classmethod
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
            [self.find_channel(self, fixture, 'intensity'),
             dmx_value, fade_time, curve]
            for fixture in self.select(selection)
        ]
        if self.CUELIST_MODE:
            return fade_arguments
        if VERBOSE: print(f'set_intensity [+]: {fade_arguments=}')
        DMXSender.fade(*fade_arguments)
        return

    @classmethod
    def set_colour(self, selection, value, fade_time, curve='sine'):
        '''
        Set colour of 'selection' to 'value' across 'fade_time'

        Args:
            selection (list, int, str): either group, fixture or multiple fixtures
            value (int, str): colour value as HSI, RGB or palette name
        '''

        # Functions
        def search_colour_palette(fixture, value):
            pal = Palettes.palettes['colours'][value]
            if fixture in pal.get('fixture', []):
                return pal['fixture'][fixture]
            elif (fixture_type := Patching.patching[fixture][0]) in pal.get('fixture types', []):
                return pal['fixture types'][fixture_type]
            else:
                return pal['default']

        def rgb_to_rgbw(rgb):
            return rgb

        def hsi_to_rgbw(hsi):
            # converts HSI to RGBW
            hue_deg, sat, intensity = hsi
            hue_deg = hue_deg % 360
            hue_rad = hue_deg * math.pi / 180
            sat = max(0, min(sat, 1))
            intensity = max(0, min(intensity, 1))
            if hue_deg < 120:
                cos_h = math.cos(hue_rad)
                cos_1047_h = math.cos(math.pi / 3 - hue_rad)
                red = sat * 255 * intensity / 3 * \
                    (1 + cos_h/cos_1047_h)  # TODO: check fraction
                green = sat * 255 * intensity / \
                    3 * (1 + (1 - cos_h/cos_1047_h))
                blue = 0
                white = 255 * (1 - sat) * intensity
            elif hue_deg < 240:
                hue_rad = hue_rad - math.pi * 2 / 3
                cos_h = math.cos(hue_rad)
                cos_1047_h = math.cos(math.pi / 3 - hue_rad)
                green = sat * 255 * intensity / 3 * (1 + cos_h/cos_1047_h)
                blue = sat * 255 * intensity / 3 * \
                    (1 + (1 - cos_h/cos_1047_h))
                red = 0
                white = 255 * (1 - sat) * intensity
            else:
                hue_rad = hue_rad - math.pi * 4 / 3
                cos_h = math.cos(hue_rad)
                cos_1047_h = math.cos(math.pi / 3 - hue_rad)
                blue = sat * 255 * intensity / 3 * (1 + cos_h/cos_1047_h)
                red = sat * 255 * intensity / 3 * \
                    (1 + (1 - cos_h/cos_1047_h))
                green = 0
                white = 255 * (1 - sat) * intensity
            return [self.clamp(i) for i in (red, green, blue, white)]

        # Libs
        colour_lib = {
            'r': 'red',
            'g': 'green',
            'b': 'blue',
            'a': 'amber',
            'w': 'white',
            'u': 'uv'
        }

        # Handle value
        if isinstance(value, str):
            # If in palette
            if (value := value.lower()) in (pal := Palettes.palettes['colours']):
                for fixture in Programmer.select(selection):
                    colour = search_colour_palette(fixture, value)
                    # TODO: translate the colour to fixture colour mapping
            else:
                try:
                    CMD.parse_colour(value)  # TODO: new_function
                except InvalidError:  # TODO: invalid_function
                    print(f'set_colour [-]: invalid colour {value}')
        elif isinstance(value, tuple):
            colour = value

        # Check value TODO
        # Generate fade arguments
        def colour_to_fade_argument(colour, colour_type, fixture):
            return [
                [
                    self.find_channel(self, fixture, colour_lib[colour_name]),
                    value,
                    fade_time,
                    curve
                ]
                for colour_name, value in zip(colour_type, colour)
            ]

        fade_arguments = []
        for fixture in self.select(selection):
            fade_arguments.extend(
                colour_to_fade_argument(
                    colour=colour,  # TODO: fix this
                    colour_type=Patching.fixture_types[(
                        fixture_type := Patching.patching[fixture][0])]['colour_mapping'],
                    fixture=fixture
                )
            )
        if VERBOSE:
            print('set_colour [TODO]')
        if self.CUELIST_MODE:
            return fade_arguments
        else:
            DMXSender.fade(*fade_arguments)
        return

    @classmethod
    def set_position(self, selection, value, fade_time, curve='linear'):
        '''
        Set position of 'selection' to 'value' across 'fade_time'

        Args:
            selection (list, int, str): either group, fixture or multiple fixtures
            value (int, str): position value as Pan/Tilt or palette name
        '''
        # TODO: [POSITION]
        # Handle value
        if isinstance(value, str):
            if value in (pal := Palettes.palettes['positions']):
                value = pal[value]
            
        # parse position name
        # transform according to coarse/fine

        return

    @classmethod
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

    @classmethod
    def effect(self, value, time, start, parameters={}):
        # TODO: cuelist needs to be changed to [commands, effects=[effects to start]]
        '''
        Effect_var (dict):
            form: waveform/effect
            size: amplitude
            length: wavelength
            hoz: horizontal shift
            ver: vertical shift
            absrel: absolute or relative mode
        '''
        form = parameters.get('form')
        size = parameters.get('size', default.effect_size)
        length = math.pi * parameters.get('length', default.effect_length)
        hoz = parameters.get('hoz', default.effect_hoz)
        ver = parameters.get('ver', default.effect_ver)
        absrel = parameters.get('absrel', default.effect_absrel)
        # TODO: implement absolute override
        effects_lib = {
            'sine': lambda x: size * math.sin(length * x + hoz) + ver,
            'tangent': lambda x: size * math.tan(length * x + hoz) + ver,
            'none': lambda x: x
        }
        return self.clamp(value + effects_lib[form](time - start))

    def find_channel(self, fixture, parameter):
        '''
        Translate parameter to DMX channel

        Args:
            fixture (int, tuple): either a fixture number or a tuple with the address and fixture_type already provided 
            parameter (str): which parameter is being searched for
        '''
        # Handle fixture
        if isinstance(fixture, (tuple, list)):
            fixture_type, address, *cell = fixture
        else:
            fixture_type, address, *cell = Patching.patching[float(fixture)]
        if len(cell) > 0: cell = cell[0] # TODO: clean up handling cells
        else: cell = 0
        # Find channel
        if cell:
            channel = address + \
                Patching.fixture_types[fixture_type]['mapping'][cell]['mapping'][parameter]['channel'] - 1
        else:
            channel = address + \
                Patching.fixture_types[fixture_type]['mapping'][parameter]['channel'] - 1
        return channel

    def find_parameter_options(self, fixture_type, parameter):
        return

    @classmethod
    def start_mouse_tracker(self, primary_position=(100, 100), x_channel=False, y_channel=False):
        # TODO: [REFACTOR]
        # Move mouse to primary position ie. position to be stuck in
        # Programmer.start_mouse_tracker(x_channel=1, y_channel=2)
        if x_channel is False and y_channel is False: return
        x0, y0 = primary_position
        mouse.move(x0, y0)
        # TODO: CLEAN

        def handle_mouse(evt, x0=x0, y0=y0):
            # Cancel tracking if click
            x_value = DMXSender.raw_state.get(x_channel, 0)
            y_value = DMXSender.raw_state.get(y_channel, 0)
            if isinstance(evt, mouse._mouse_event.ButtonEvent):
                mouse.unhook(handle_mouse)
            new_x, new_y = mouse.get_position()
            direction = 'none'
            shortcut_return = False
            if not keyboard.is_pressed(42):  # if not shift key
                if new_x > x0:
                    x_value = self.clamp(x_value + 5)
                    direction = 'right'
                elif new_x < x0:
                    x_value = self.clamp(x_value - 5)
                    direction = 'left'
                else:
                    shortcut_return = True
            if not keyboard.is_pressed(29):  # if not ctrl key
                if new_y > y0:
                    y_value = self.clamp(y_value - 5)
                    direction = 'down'
                elif new_y < y0:
                    y_value = self.clamp(y_value + 5)
                    direction = 'up'
                elif shortcut_return:
                    return
            if VERBOSE:
                print(
                    f'handle_mouse [+]: mouse moved {direction} {new_x=} {x_value=} {new_y=} {y_value=}')
            mouse.move(x0, y0)
            fade_arguments = []
            print(f'{x_channel=}, {y_channel=}, {x_value=}, {y_value=}')
            if x_channel is not False:
                fade_arguments.append([x_channel, x_value, 0, 'linear'])
            if y_channel is not False:
                fade_arguments.append([y_channel, y_value, 0, 'linear'])
            DMXSender.fade_instant(*fade_arguments)
            # DMXSender.fade(*fade_arguments)
            # mouse.unhook(handle_mouse)
            # eel.update_node(node, (x_value, y_value))
            return x_value, y_value
        mouse.hook(handle_mouse)
        return

    @classmethod
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
                return {parameter: (list(value_dict.items()) if isinstance(value_dict, dict) else value_dict) for parameter, value_dict in x.items()}
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

    @classmethod
    def play_cue(self, cuelist, cue_number=False, source='back'):
        # TODO: [REFACTOR]
        # Handle cue number
        if cue_number is False:
            if cuelist in self.active_cuelists:
                cue_number = self.active_cuelists[cuelist]
            else:
                cue_number = 0
        # Update active_cuelists
        self.update_active(self, cuelist, cue_number)
        # Find what commands have been generated
        commands = self.cuelists[cuelist].cues[cue_number].commands
        # Flatten all commands to extract dmx
        dmx = [arg for _, fade_arguments in commands.items()
               for arg in fade_arguments]
        # Find what effects are to be generated
        effects = self.cuelists[cuelist].cues[cue_number].effects
        if VERBOSE:
            print(f'play_cue [+]: {dmx=} {effects=}')
        self.update_active(self, cuelist, cue_number + 1)
        # TODO: cycle through cuelist
        DMXSender.fade(*dmx, effects=effects)
        if GUI.state:
            eel.remove_cue_from_selection(cuelist, cue_number)
            eel.add_cue_to_selection(cuelist, cue_number + 1)
        return

    @classmethod
    def start_timecode(self, cuelist, cue_number=0):
        # Identify all cues with timecode
        ## {timing: cue_number}
        # NOTE: dict used to look for latest cue only
        timecode_cues = {
            cue.timing: cue_number
            for cue_number, cue in enumerate(Show.cuelists[cuelist].cues)
            if isinstance(cue.timing, (float, int))
        }
        # Sort all timecodes
        timecode_list = [item for item in timecode_cues.items()]
        timecode_list.sort(key=lambda cue: cue[0])
        print(timecode_list)
        # Extract timings and cues
        timings = [timing for timing, *_ in timecode_list]
        cues = [cue for _, cue in timecode_list]

        def run_timecode(cuelist, cue_number):
            current_timing = Show.cuelists[cuelist].cues[cue_number].timing
            start = time.time() - current_timing
            # TODO: [TIMECODE] how to handle run_timecode if started on a manual cue
            start_index = cues.index(cue_number)
            for i in range(len(timings[start_index:])):
                while (time.time() - start) < timings[start_index:][i]:
                    pass
                self.play_cue(cuelist, cues[start_index:][i])

        run_timecode(cuelist, cue_number)
        return

    def update_active(self, cuelist, cue_number):
        self.active_cuelists[cuelist] = cue_number
        return

    @classmethod
    def new_cuelist(self, name, cuelist=False):
        '''
        Create new cuelist if cuelist does not yet exist

        Args:
            name (str): name of cuelist
            cuelist (Cuelist): provided cuelist
        '''
        if name not in Show.cuelists:
            Show.cuelists[name] = cuelist or Cuelist(name=name)
            print(f'new_cuelist [+]: {name} cuelist created')
        else:
            print(f'new_cuelist [-]: {name} already exists')
        return

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

    # TODO: [CLEAN] what does this decorator do?
    # @property
    # def cues(self):
    #     return self.cues

    def add_cue(self, cue, position=None):
        # TODO: [REFACTOR] refactor from record
        if position is None: 
            self.cues.append(cue)
        else:
            self.cues.insert(position, cue)
        print(f'[+] add_cue: cue added to cue list')
        return self.cues

    def delete_cue(self, cue_position):
        self.cues = self.cues[:cue_position] + self.cues[cue_position + 1:]
        return self.cues

    def rearrange_cue(self, old_position, new_position):
        return self.cues

    def update_state(self):
        # TODO: [EFFECT] store effect into state somehow
        self.cues = list(map(self.calculate_state), self.cues)
        return

    def calculate_state(cue):
        state = [None] * 256
        cue.state = state
        for channel, value, *_ in [dmx for command in cue.commands.values() for dmx in command]:
            state[channel] = value
        return cue

    def js_cuelist(self):
        return [i.js_cue() for i in self.cues]


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

    def __init__(self, name=False, desc='', timing='manual', commands={}, effects={}):
        # TODO
        self.name = name  # TODO: config
        self.desc = desc
        self.commands = commands
        # f'{instruction} {value}': Programmer.commands_lib[]
        self.timing = timing
        self.effects = effects
        self.state = []
        return

    def update_commands(self):
        pass

    def edit_commands(self):
        pass

    def js_cue(self):
        return {
            'name': self.name,
            'desc': self.desc,
            'commands': self.commands,
            'timing': self.timing,
            'state': self.state
        }


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
        'startcl': ('meta', Programmer.activate_cuelist_mode),
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

    @classmethod
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
            parse_assignment(names, values)
            if 'rgb' in values or 'hsl' in values or 'pos' in values:
                parse_assignment(values)

        # If line is programming
            # Separate into commands
        token_list = []
        # eg. [@20, pars, si 100, sc 'red blue', in 2, # name, / description]
        token_builder = []  # temporary array to build the above commands
        keywords = list(self.commands_lib.keys()) + \
            list(self.aliases.keys()) + \
            list(Palettes.palettes['groups'].keys()) + \
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
            'fade_time': default.programmer_fade_time if Programmer.FADE_MODE else 0
        }  # temp programmer before updating
        selection_builder = []
        command_list = []
        for token in token_list:
            if token[0][0] == '@':  # TIMING
                programmer_builder['timing'] = int(token[0][1:])
            elif (start := token[0]) == '#':  # NAME
                programmer_builder['name'] = ' '.join(token[1:])
            elif start == '/':  # DESCRIPTION
                programmer_builder['description'] = ' '.join(token[1:])
            elif default.is_number(start):  # FIXTURE NUMBER
                selection_builder.append(start)
            elif start in Palettes.palettes['groups']:  # GROUP NAME
                selection_builder.append(start)
            elif start == 'in':  # FADE TIME
                programmer_builder['fade_time'] = int(token[1])
            elif start in self.aliases:
                alias_parser(token)
            else:
                command_list.append(token)
        # If no commands
        if len(command_list) == 0 and GUI.state:
            # TODO: Do I need to update programmer selection?
            eel.refresh_selection(Programmer.select(selection_builder))
        # Run commands
        # If cuelist_mode, save commands to cuelist and don't run
        # If not cuelist_mode, save commands to programmer and run
        if VERBOSE: print(f'parse: {command_list=}')
        for action, *values in command_list:
            command_type, command_function, *other = self.commands_lib[action]
            value = ' '.join(values)
            if command_type == 'program':
                if Programmer.CUELIST_MODE:  # if importing
                    # ALT: use classes
                    command = ' '.join(selection_builder + [action] + values)
                    fade_arguments = command_function(
                        selection=Programmer.select(selection_builder),
                        value=value,
                        fade_time=programmer_builder['fade_time'],
                        curve=programmer_builder['curve']
                    )
                    programmer_builder['commands'][command] = fade_arguments
                else:  # if live
                    # Run command
                    command_function(
                        selection=Programmer.select(selection_builder),
                        value=value,
                        fade_time=programmer_builder['fade_time'],
                        curve=programmer_builder['curve']
                    )
                    # TODO: commands run one after another if in the same line. take out arguments and run them together like in cue mode basically
                    # Update programmer
                    instruction = ' '.join(selection_builder + [action])
                    if instruction in Programmer.programmer['commands']:
                        del Programmer.programmer['commands'][instruction]
                    Programmer.programmer['commands'][instruction] = value
                    # ALT [TODO]: convert this to an update?
                    for fixture in Programmer.select(selection_builder):
                        parameter = other[0]
                        if isinstance(value, str) and value.isnumeric():
                            value = int(value)
                        if fixture not in Programmer.programmer:
                            Programmer.programmer[fixture] = {}
                        if parameter not in Programmer.programmer[fixture]:
                            Programmer.programmer[fixture][parameter] = {}
                        elif instruction in Programmer.programmer[fixture][parameter]:
                            del Programmer.programmer[fixture][parameter][instruction]
                        Programmer.programmer[fixture][parameter][instruction] = value
            elif command_type == 'meta':
                command_function(*values)
        # Run commands
        if GUI.state and Programmer.programmer:
            eel.refresh_programmer(Programmer.js_programmer())
        return

    def parse_file(self, file):
        # TODO: [REMAKE]
        with open(file) as f:
            while line := f.readline():
                self.parse(line)
        return

Palettes.load('groups', 'colours', 'positions')  # TODO: change to config

# EXPOSED FUNCTIONS


@eel.expose
def get_palette():
    return Palettes.palettes


@eel.expose
def get_cuelists():
    return {name: cuelist.js_cuelist() for name, cuelist in Show.cuelists.items()}


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
def read_line(line):
    CMD.parse(line)


@eel.expose
def play_cue(cuelist, cue_number=False, source='back'):
    Show.play_cue(cuelist, cue_number, source)
    return

@eel.expose
def record_programmer_to_cuelist(programmer):
    Programmer.record_programmer(programmer)
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

def et(value, parameters={'form': 'sine', 'length': math.pi}):
    '''
    Outputs values of effects for 5 seconds
    '''
    Hz = 40
    demo = [Programmer.effect(value, time=i / Hz, start=0, parameters=parameters) for i in range(5 * Hz)]
    for i in enumerate(demo): print(i)
    return demo


def rl(line):
    CMD.parse(line)
    return


def d(values):
    DMXSender.client.write(f'DMX {values}')
    return

# for i in range(255):
#     d(f'2 50 15 {i}')
#     time.sleep(0.01)

# for i in range(255):
#     d(f'2 {i}')


def bye():
    try:
        DMXSender.sender.join()
        GUI.join()
    finally:
        exit()


Patching.import_fixture_type('trimmer par')
Patching.import_fixture_type('led bar (14)')
Patching.patch_fixtures('trimmer par', 101, 2, 1)
Patching.patch_fixtures('led bar (14)', 201, 1, 200)
showcase = Cuelist()
showcase.add_cue(
    Cue(
        name='beat',
        desc='pars flash',
        timing=0.0,
        commands={
            'pars on': [[1, 128, 0, 'linear'], [9, 128, 0, 'linear']],
        },
        effects={1: {'form': 'sine', 'size': 100, 'length': 1}}
    )
)
showcase.add_cue(
    Cue(
        name='beat',
        desc='pars flash',
        timing=1.0,
        commands={
            'pars off': [[1, 0, 0, 'linear'], [9, 0, 0, 'linear']],
        }
    )
)
showcase.add_cue(
    Cue(
        name='beat',
        desc='pars flash',
        timing=2.0,
        commands={
            'pars on': [[1, 255, 0, 'linear'], [9, 255, 0, 'linear']],
        }
    )
)
showcase.add_cue(
    Cue(
        name='beat',
        desc='pars flash',
        timing=3.0,
        commands={
             'pars off': [[1, 128, 0, 'linear']]
        }
    )
)
Show.new_cuelist('showcase', cuelist=showcase)

if __name__ == '__main__':
    if args.connect: DMXSender.connect()
    if args.gui: GUI.start()
    import cProfile
    import pstats
    with cProfile.Profile() as pr:
        Programmer.start_mouse_tracker(x_channel=1, y_channel=2)
        pass
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()

__________OLDCODE___________ = None
# OLD CODE


# palette groups for multiple parameters using function arguments (colour=), stored in
# do i want fixture IDs? How is group behaviour meant to work? What happens if I change the fixture numbers later? Should the group refer to the same fixture numbers or the same fixures


def parse_assignment(type, values):
    assignment_lib = {
        'rgb': 'colour',
        'hsl': 'colour',
        'pos': 'position',
        'position': 'position',
        'select': 'group',
        'effect': 'effect'
    }
    

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


# def in_fade():
#     if channel in effectsLib:
#         modifier = effect(channel, size, )
#         return original_value + modifier
