#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Authors:
#   Nicklas Lindgren <nili@lysator.liu.se>
#
# Copyright 2006 Nicklas Lindgren
#
# Released under GNU GPL, read the file 'COPYING' for more information

START_FULLSCREEN_LARGE_SCREEN = False
START_FULLSCREEN_SMALL_SCREEN = True
HWSURFACE = True
SOUND = True
MIXER_PRE_INIT = True
WRONG_SAMPLE_RATE_FACTOR = 1
#WRONG_SAMPLE_RATE_FACTOR = 48000/44100.0

######################################################################

ENEMY_AMOUNT_SCALE = 1.0
GRACE_TIME_SCALE = 1.0

def enemies(amt):
    return int(round(amt * ENEMY_AMOUNT_SCALE))

def grace_time(t):
    return t * GRACE_TIME_SCALE

######################################################################

VERSION = 0.2

import os.path, math, time, pickle, sys, gzip
import random as random_module
from itertools import chain
import pygame

try:
    import psyco
    psyco.full()
except:
    print 'Psyco finns inte.'

######################################################################

TARGET_FPS = 30
def seconds(sec):
    return int(sec * TARGET_FPS)
def hertz(hz):
    return float(TARGET_FPS) / hz
def pixels_per_second(pixels):
    return float(pixels) / TARGET_FPS

######################################################################

if MIXER_PRE_INIT:
    SAMPLE_RATE = 44100
    BUFFER_SIZE = 1024
    pygame.mixer.pre_init(SAMPLE_RATE, 0, 1, BUFFER_SIZE)
else:
    SAMPLE_RATE = 22050
    BUFFER_SIZE = 1024
EXPECTED_MUSIC_DELAY = BUFFER_SIZE * 1000.0 / SAMPLE_RATE * 2 / WRONG_SAMPLE_RATE_FACTOR
#EXPECTED_MUSIC_DELAY = 0

pygame.init()
if pygame.mixer.get_init():
    pygame.mixer.set_reserved(1)
    priority_channel = pygame.mixer.Channel(0)
else:
    SOUND = False
    print 'Ljudet funkar inte!'

######################################################################

flags = 0
if max(pygame.display.list_modes()) <= (1024, 768):
    start_fullscreen = START_FULLSCREEN_SMALL_SCREEN
else:
    start_fullscreen = START_FULLSCREEN_LARGE_SCREEN

if start_fullscreen:
    flags |= pygame.FULLSCREEN
if HWSURFACE and start_fullscreen:
    flags |= pygame.HWSURFACE | pygame.DOUBLEBUF

WIDTH, HEIGHT = (1024, 768)
screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
pygame.mouse.set_visible(False)

######################################################################

files = {}

def index_directory(none, directory, filenames):
    if directory.count(".svn") == 0:
        for f in filenames:
            files[f] = os.path.join(directory, f)

os.path.walk('data', index_directory, None)

######################################################################

def make_font(name, size):
    return pygame.font.Font(files[name + '.ttf'], size)

tiny_font, small_font, font, caption_font = (make_font('Titania-Regular', size) for size in (20, 32, 36, 48))

######################################################################

class Button(object):
    def __init__(self):
        self.reset()
    def reset(self):
        self.state = False
        self.last_push_frame = -1000
        self.triggered = False
    def set(self, state):
        self.state = state
        if state:
            self.last_push_frame = level.frames
            self.triggered = True
    def maybe_set(self, state):
        if state != self.state:
            self.set(state)
    def get_triggered(self):
        if self.triggered:
            self.triggered = False
            return True
        else:
            return False
    def __call__(self):
        return self.state

class Axis(object):
    THRESHOLD = 0.66
    def __init__(self, button_low, button_high):
        self.button_low = button_low
        self.button_high = button_high
    def set(self, value):
        if value < -self.THRESHOLD:
            self.button_low.maybe_set(True)
            self.button_high.maybe_set(False)
        elif value > self.THRESHOLD:
            self.button_low.maybe_set(False)
            self.button_high.maybe_set(True)
        else:
            self.button_low.maybe_set(False)
            self.button_high.maybe_set(False)

move_up = Button()
move_down = Button()
move_left = Button()
move_right = Button()
fire_up = Button()
fire_down = Button()
fire_left = Button()
fire_right = Button()
start = Button()

beat_start = Button()
bar_start = Button()
even_bar_start = Button()
all_buttons = [move_up, move_down, move_left, move_right, fire_up, fire_down, fire_left, fire_right, start, beat_start, bar_start, even_bar_start]

move_y = Axis(move_up, move_down)
move_x = Axis(move_left, move_right)
fire_y = Axis(fire_up, fire_down)
fire_x = Axis(fire_left, fire_right)

class Joystick(object):
    def __init__(self, joy):
        self.joystick = joy
        self.name = joy.get_name()
        joy.init()
        if joystick_maps.has_key(self.name):
            self.bindings = joystick_maps[self.name]
        elif joy.get_numaxes() < 2:
            print 'För få axlar (%d st) på joystick: %s' % (joy.get_numaxes(), self.name)
            joy.quit()
        elif joy.get_numbuttons() < 4:
            print 'För få knappar (%d st) på joystick: %s' % (joy.get_numbuttons(), self.name)
            joy.quit()
        else:
            print 'Känner inte igen joystick: %s' % self.name
            joy.quit()

joystick_maps = { 'HID 0b43:0003': { 'name': 'EMS Dualshooter',
                                     'axes': { 0: move_x,
                                               1: move_y,
                                               5: fire_x,
                                               2: fire_y },
                                     'buttons': { 0: fire_up,
                                                  16: fire_up,
                                                  1: fire_right,
                                                  17: fire_right,
                                                  2: fire_down,
                                                  18: fire_down,
                                                  3: fire_left,
                                                  19: fire_left,
                                                  9: start,
                                                  25: start,
                                                  12: move_up,
                                                  28: move_up,
                                                  13: move_right,
                                                  29: move_right,
                                                  14: move_down,
                                                  30: move_down,
                                                  15: move_left,
                                                  31: move_left } },
                  'HID 6666:0667': { 'name': 'BOOM PSX+N64 converter',
                                     'axes': { 0: move_x,
                                               1: move_y,
                                               2: fire_x,
                                               3: fire_y },
                                     'buttons': { 0: fire_up,
                                                  1: fire_right,
                                                  2: fire_down,
                                                  3: fire_left,
                                                  11: start,
                                                  12: move_up,
                                                  13: move_right,
                                                  14: move_down,
                                                  15: move_left } },
                  '4 axis 16 button joystick': { 'name': 'Idiotiska windowsjoysticknamn... *mummel*',
                                     'axes': { 0: move_x,
                                               1: move_y,
                                               2: fire_x,
                                               3: fire_y },
                                     'buttons': { 0: fire_up,
                                                  1: fire_right,
                                                  2: fire_down,
                                                  3: fire_left,
                                                  11: start,
                                                  12: move_up,
                                                  13: move_right,
                                                  14: move_down,
                                                  15: move_left } } }

joysticks = [Joystick(pygame.joystick.Joystick(i)) for i in xrange(pygame.joystick.get_count())]

reverse_keymap = {}
for key in (k for k in dir(pygame) if k[0:2] == 'K_'):
    code = getattr(pygame, key)
    reverse_keymap[code] = 'pygame.' + key

keymap_alts = [{ 'name': 'MAME-bindingar för Robotron',
                 pygame.K_e: move_up,
                 pygame.K_d: move_down,
                 pygame.K_s: move_left,
                 pygame.K_f: move_right,
                 pygame.K_i: fire_up,
                 pygame.K_k: fire_down,
                 pygame.K_j: fire_left,
                 pygame.K_l: fire_right,
                 pygame.K_1: start,
                 pygame.K_p: start,
                 pygame.K_PAUSE: start,
                 'fire_keys': 'I J K L',
                 'move_keys': 'E S D F' },
               { 'name': 'MAME-bindningar för spelare 1 och 2',
                 pygame.K_KP8: move_up,
                 pygame.K_KP2: move_down,
                 pygame.K_KP4: move_left,
                 pygame.K_KP6: move_right,
                 pygame.K_UP: move_up,
                 pygame.K_DOWN: move_down,
                 pygame.K_LEFT: move_left,
                 pygame.K_RIGHT: move_right,
                 pygame.K_r: fire_up,
                 pygame.K_f: fire_down,
                 pygame.K_d: fire_left,
                 pygame.K_g: fire_right,
                 pygame.K_1: start,
                 pygame.K_p: start,
                 pygame.K_PAUSE: start,
                 'fire_keys': 'R D F G',
                 'move_keys': 'piltangenterna' },
               { 'name': 'Egilbindningar',
                 pygame.K_i: move_up,
                 pygame.K_o: move_down,
                 pygame.K_j: move_left,
                 246: move_right,
                 pygame.K_e: fire_up,
                 pygame.K_w: fire_down,
                 pygame.K_a: fire_left,
                 pygame.K_f: fire_right,
                 pygame.K_1: start,
                 pygame.K_p: start,
                 pygame.K_PAUSE: start,
                 'fire_keys': 'A W E F',
                 'move_keys': u'J I O Ö' },]

keymap = keymap_alts[0]

keymap_select_map = {}

class DuplicateKey(Exception):
    pass

for cur_keymap in keymap_alts:
    for key in cur_keymap.keys():
        try:
            cmp_keymap_alts = keymap_alts[:]
            cmp_keymap_alts.remove(cur_keymap)
            if not key in chain((k.keys for k in keymap_alts)):
                keymap_select_map[key] = cur_keymap
        except DuplicateKey:
            pass

######################################################################

def source_code():
    src = file(sys.argv[0], 'r')
    result = src.read()
    src.close()
    return result

class DemoRecorder(object):
    FORMAT = '%Y-%m-%d %H.%M.%S.grtdemo'
    def __init__(self, buttons):
        self.recording = False
        self.playing = False
        self.freeze = False
        self.buttons = buttons
    def play(self, filename):
        self.playing = True
        f = gzip.open(filename, 'r')
        source = pickle.load(f)
        if source != source_code():
            print 'Varning: Demot kan vara inkompatibelt med den här versionen!'
        self.frames = pickle.load(f)
        f.close()
        self.frame = 1
        random.setstate(self.frames[0])
    def record(self):
        self.recording = True
        self.filename = time.strftime(self.FORMAT)
        self.state = [False for f in self.buttons]
        self.frames = [random.getstate()]
    def stop(self):
        if self.recording:
            f = gzip.open(self.filename, 'w')
            pickle.dump(source_code(), f)
            pickle.dump(self.frames, f)
            f.close()
            self.recording = False
        if self.playing:
            self.playing = False
            music.stop()
            self.freeze = True
    def advance_frame(self):
        if self.recording:
            state = [(b.state, b.triggered) for b in self.buttons]
            self.frames.append(state)
        elif self.playing:
            if self.frame >= len(self.frames):
                self.stop()
            else:
                state = self.frames[self.frame]
                for s, b in zip(state, self.buttons):
                    b.set(s[0])
                self.frame += 1

######################################################################

image_names = ['grass',
               'living_grass',
               'dark',
               'death',
               'nili_gulmohar',
               'player',
               'bullet',
               'ball',
               'spark',
               'bigspark',
               'mega_spark',
               'wisp',
               'fairy',
               'red_fairy',
               'proto_hulk',
               'proto_sphereoid',
               'machine',
               'pickup',
               'eights',
               'target',
               'bomb',
               'aura',
               'cat',
               'turtle',
               'snail',
               'esdf',
               'ijkl']

images = {}

for name in image_names:
    surf = pygame.image.load(files[name + '.png'])
    images[name] = surf.convert_alpha()

######################################################################

sound_names = ['poof',
               'whap',
               'boom',
               'snare',
               'boohm',
               'blippiblipp',
               'gong']

sounds = {}

if SOUND:
    for name in sound_names:
        sounds[name] = pygame.mixer.Sound(files[name + '.wav'])

def play_sound(name, priority = False, really_high_priority = True):
    if SOUND:
        if priority:
            if really_high_priority or not priority_channel.get_busy():
                priority_channel.play(sounds[name])
        else:
            sounds[name].play()

######################################################################

END_MUSIC_EVENT = pygame.USEREVENT

class Music(object):
    class Song(object):
        def __init__(self, name, bpm, bpb, intro_delay_bars = 0, intro_delay_s = 0):
            self.name = name
            self.bpm = bpm
            self.bpb = bpb
            self.intro_delay_bars = intro_delay_bars
            self.intro_delay_ticks = intro_delay_s * 1000
        def play(self):
            pygame.mixer.music.stop()
            pygame.mixer.music.load(files[self.name + '.ogg'])
            pygame.mixer.music.play(0)
            pygame.mixer.music.set_endevent(END_MUSIC_EVENT)
        def bars(self, ticks):
            return (ticks - self.intro_delay_ticks - EXPECTED_MUSIC_DELAY) / 60000.0 * WRONG_SAMPLE_RATE_FACTOR * self.bpm / self.bpb - self.intro_delay_bars
        def beats(self, ticks):
            return (ticks - self.intro_delay_ticks - EXPECTED_MUSIC_DELAY) / 60000.0 * self.bpm - (self.intro_delay_bars * self.bpb)

    songs = { 'sparrow': Song("GibIt - Please, Don't Eat The Sparrow", 151, 4, 0, 0.27),
              'solitude': Song('GibIt - Solitude of a Shapeless Outcast', 154, 4, 0, 0.0533),
              'perfect': Song("GibIt - 'Perfect'", 106, 4, 1/8.0, 0.0275) }

    def __init__(self):
        self.current_song = None
        self.playlist = self.songs.values()
        self.stopped = True
        random.shuffle(self.playlist)
    def next(self):
        if not self.stopped:
            self.play()
    def play(self, song = None):
        if not song:
            #song = random.choice(self.songs.values())
            song = self.playlist[0]
        else:
            song = self.songs[song]
        self.playlist.remove(song)
        self.playlist.append(song)
        self.current_song = song
        self.song_start_ticks = pygame.time.get_ticks()
        self.stopped = False
        if SOUND:
            song.play()
            songname = Caption(song.name, small_font)
            w = songname.image.get_width()
            x = WIDTH - w - 4
            songname.target_x = x
            songname.target_y = HEIGHT - 40
            songname.displace_x = w + 40
            songname.special = True
            songname.life = seconds(7.5)
            songname.beat_displace = 2
            songname.spawn()
            notes = Caption(images['eights'])
            notes.special = True
            notes.target_x = x - 40
            notes.displace_x = w + 40
            notes.target_y = HEIGHT - 40
            notes.life = seconds(7.5)
            notes.beat_displace = 12
            notes.spawn()

    def stop(self):
        self.current_song = None
        self.stopped = True
        if SOUND:
            pygame.mixer.music.fadeout(7000)
    def pause(self):
        self.pause_ticks = pygame.time.get_ticks()
        if SOUND:
            pygame.mixer.music.pause()
    def unpause(self):
        now = pygame.time.get_ticks()
        self.song_start_ticks += now - self.pause_ticks
        if SOUND:
            pygame.mixer.music.unpause()
    def bars(self):
        if self.current_song:
            now = pygame.time.get_ticks()
            return self.current_song.bars(now - self.song_start_ticks)
        else:
            return 0
    def beats(self):
        if self.current_song:
            now = pygame.time.get_ticks()
            return self.current_song.beats(now - self.song_start_ticks)
        else:
            return 0


######################################################################

class Sprite(object):
    X_MARGIN = 16
    Y_MARGIN = 16
    def __init__(self, *args):
        self.x = 0
        self.y = 0
        self.visible = True
        self.remove = False
        self.square_radius = 0
        self.initialize(*args)
    def spawn(self):
        level.sprites.append(self)
    def maybe_spawn(self):
        if level.sprites.count(self) == 0:
            self.spawn()
    def initialize(self):
        pass
    def set_image(self, image):
        self.x_offset = image.get_height() / 2
        self.y_offset = image.get_height() / 2
        self.image = image
        self.frame_width = image.get_height()
        self.frame = 0
    def move(self, ref):
        self.x = ref.x
        self.y = ref.y
    def square_distance(self, ref, offset = (0, 0)):
        return (self.x - (ref.x + offset[0])) ** 2 + (self.y - (ref.y + offset[1])) ** 2
    def distance(self, ref, offset = (0, 0)):
        return math.sqrt(self.square_distance(ref, offset))
    def vector_to(self, ref, offset = (0, 0)):
        x = (ref.x + offset[0]) - self.x
        y = (ref.y + offset[1]) - self.y
        return (x, y)
    def direction_to(self, ref, offset = (0, 0)):
        x, y = self.vector_to(ref, offset)
        dist = self.distance(ref)
        return (x / dist, y / dist)
    def touches(self, ref):
        return self.square_distance(ref) < self.square_radius + ref.square_radius
    def clamp_position(self):
        clamped = False
        if self.x < self.X_MARGIN:
            self.x = self.X_MARGIN
            clamped = True
        if self.x > WIDTH - self.X_MARGIN:
            self.x = WIDTH - self.X_MARGIN
            clamped = True
        if self.y < self.Y_MARGIN:
            self.y = self.Y_MARGIN
            clamped = True
        if self.y > HEIGHT - self.Y_MARGIN:
            self.y = HEIGHT - self.Y_MARGIN
            clamped = True
        return clamped
    def cull(self):
        if self.x + self.x_offset < 0:
            self.remove = True
        elif self.x - self.x_offset > WIDTH:
            self.remove = True
        elif self.y + self.y_offset < 0:
            self.remove = True
        elif self.y - self.y_offset > HEIGHT:
            self.remove = True
    def update(self):
        pass
    def draw_image(self, image, frame):
        screen.blit(image,
                    (self.x - self.x_offset, self.y - self.y_offset),
                    (self.frame_width * frame, 0, self.frame_width, self.frame_width))
    def draw(self):
        if self.visible and not self.remove:
            self.draw_image(self.image, self.frame)
    def decrease_life(self):
        self.life -= 1
        if self.life == 0:
            self.remove = True
    def random_position(self):
        self.x, self.y = level.random_position()
        self.clamp_position()
    def nearest_player(self):
        living_players = [p for p in players if p.hittable()]
        if len(living_players):
            return living_players[0]
        else:
            return None

ORTHOGONAL_FACTOR = 1.0
ORIGINAL_FACTOR = 0.3
def big_spark_spray(ref, amount, speed0, speed1, pos = None):
    if not pos:
        pos = ref
    for i in xrange(amount):
        for n in (-ORTHOGONAL_FACTOR, ORTHOGONAL_FACTOR):
            spark = BigSpark()
            spark.move(pos)
            r0 = random.expovariate(0.7) * speed1 / 3
            r1 = random.expovariate(0.7) * speed1 / 3
            spark.delta_x = (-n*ref.delta_y * r0 + ORIGINAL_FACTOR * ref.delta_x * r1)
            spark.delta_y = (n*ref.delta_x * r0 + ORIGINAL_FACTOR * ref.delta_y * r1)
            spark.spawn()

def big_spark_shock(ref, amount, pos):
    x, y = ref.vector_to(pos)
    spd = 27 / pos.distance(ref)
    for i in xrange(amount * 2):
        spark = BigSpark()
        spark.move(pos)
        a = random.uniform(0, math.pi * 2)
        s = random.expovariate(2) * 27
        spark.delta_x = math.cos(a) * s + x * spd
        spark.delta_y = math.sin(a) * s + y * spd
        spark.life += seconds(0.3)
        spark.spawn()

def big_spark_sphere(ref, amount, speed):
    for i in xrange(amount):
        spark = BigSpark()
        spark.move(ref)
        direction = random.random() * 2 * math.pi
        spark.life += int(math.sqrt(amount))
        rnd = (random.random() ** 0.9) * 1.3
        spark.delta_x = math.cos(direction) * speed * rnd
        spark.delta_y = math.sin(direction) * speed * rnd
        spark.spawn()

class Player(Sprite):
    SPEED = pixels_per_second(225)
    BULLET_SPEED = pixels_per_second(1080)
    X_MARGIN = 10
    Y_MARGIN = 23
    FIRE_DELAY = hertz(11)
    BOMB_DELAY = seconds(2)
    INVULNERABILITY_DELAY = seconds(3)

    def initialize(self):
        self.set_image(images['player'])
        self.invulnerability_delay = 0
        self.machines_remaining = 0
        self.score = 0
        self.bombs = 0
        self.bomb_delay = 0
        self.charge = 0
    def reset(self):
        self.score = 0
        self.last_score = 0
        self.machines_remaining = 3
        self.respawn_delay = seconds(2)
        self.invulnerability_delay = 0
        self.fire_delay = 0
        self.bomb_delay = 0
        self.bombs = 0
        self.charge = 0
        self.remove = True
        self.continuous_fire = False
    def respawn(self):
        self.machines_remaining -= 1
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.fire_delay = 0
        self.remove = False
        self.invulnerability_delay = self.INVULNERABILITY_DELAY
        self.maybe_spawn()
        self.bomb_delay = 0
        if self.machines_remaining < 2:
            self.bombs = 2
            self.bomb()
        self.bombs = 1
        self.charge = 0
        level.player_respawn()
    def hittable(self):
        return self.invulnerability_delay == 0 and not self.remove
    def update(self):
        if self.invulnerability_delay:
            self.invulnerability_delay -= 1
        if self.fire_delay > 0:
            self.fire_delay -= 1
        else:
            self.continuous_fire = False
        if self.bomb_delay:
            self.bomb_delay -= 1

        while self.charge > 1:
            self.charge -= 1
            self.bombs += 1
            play_sound('gong', True)
        self.subtract_charge(0.001 * ((self.bombs + 1) ** 1.1))
    def bomb(self):
        if self.bomb_delay <= 0 and self.bombs > 0:
            play_sound('boohm', True)
            bullet = BombBlast()
            bullet.move(self)
            bullet.owner = self
            bullet.spawn()
            if level.freeze_time:
                self.bombs -= 2
            else:
                self.bombs -= 1
            level.freeze_time = 0
            self.charge = 0
            self.bomb_delay = self.BOMB_DELAY
            self.invulnerability_delay = self.INVULNERABILITY_DELAY

    def fire(self, dx_param, dy_param):
        if self.fire_delay <= 0:
            if self.continuous_fire:
                diff = abs((self.old_fire_x + self.old_fire_y) - (dx_param + dy_param))
            if self.continuous_fire and diff == 1:
                dx = (self.old_fire_x + dx_param) / 3.0
                dy = (self.old_fire_y + dy_param) / 3.0
            else:
                dx = dx_param
                dy = dy_param
            self.old_fire_x = dx
            self.old_fire_y = dy
            scale_factor = math.sqrt(dx ** 2 + dy ** 2)
            dx /= scale_factor
            dy /= scale_factor
            self.continuous_fire = True
            bullet = GoodBullet()
            bullet.move(self)
            bullet.delta_x = dx * self.BULLET_SPEED + (random.random()-0.5)
            bullet.delta_y = dy * self.BULLET_SPEED + (random.random()-0.5)
            bullet.x += bullet.delta_x
            bullet.y += bullet.delta_y
            bullet.owner = self
            if dy == 0:
                bullet.frame = 0
            elif dx == 0:
                bullet.frame = 2
            elif (dx > 0) == (dy > 0):
                bullet.frame = 3
            else:
                bullet.frame = 1
            bullet.spawn()
            self.fire_delay = self.FIRE_DELAY
            big_spark_spray(bullet, 2, self.BULLET_SPEED, 0.3)
    def add_score(self, score, bonus = True):
        bomb_bonus = max(1, (1 + self.bombs)/2.0)
        if bonus:
            if self.bombs:
                self.last_score = int(score * (bomb_bonus + self.charge/2.5))
            else:
                self.last_score = score
        else:
            self.last_score = int(score * bomb_bonus)
        self.score += self.last_score
        if not (self.bomb_delay or self.remove):
            if bonus:
                self.charge += score / 3000.0
            else:
                self.charge += math.log(score) / 30.0
    def score_text(self):
        return '%010d' % self.score
    def last_score_text(self):
        if self.last_score:
            return '%d' % self.last_score
        else:
            return ''
    def subtract_charge(self, charge):
        self.charge = max(0, self.charge - charge)
    def explode(self):
        play_sound('boom', True)
        spray = RotatingSpray()
        spray.move(self)
        spray.spawn()
        for n in xrange(256):
            spark = MegaSpark()
            spark.move(self)
            spark.spawn()
        self.charge = 0
        self.bombs = 0
        self.bomb_delay = 0
        self.remove = True
        self.respawn_delay = seconds(1)
        if self.machines_remaining == 0:
            music.stop()
            level.game_over = True
    def bomb_delay_fraction(self):
        return float(self.bomb_delay) / self.BOMB_DELAY
    def draw(self):
        if self.invulnerability_delay > 16:
            self.draw_image(images['aura'], [0,1,2,1][(self.invulnerability_delay % 16)/4])
        elif self.invulnerability_delay > 0:
            self.draw_image(images['aura'], 8 - self.invulnerability_delay / 2)
        Sprite.draw(self)

class Bullet(Sprite):
    def initialize(self):
        self.set_image(images['bullet'])
        self.delta_x = 0
        self.delta_y = 0
        self.square_radius = 64 ** 2
        self.radius_coefficent = 0.5
        self.owner = None
        self.perish = True
    def update(self):
        self.x += self.delta_x
        self.y += self.delta_y
        self.square_radius *= self.radius_coefficent
        self.cull()
        if self.remove and self.owner:
            self.owner.subtract_charge(0.005)
        if random.randrange(8) == 0:
            spark = Spark()
            spark.move(self)
            spark.spawn()

class GoodBullet(Bullet):
    pass

class BadBullet(Bullet):
    def initialize(self):
        Bullet.initialize(self)
        self.set_image(images['ball'])
        self.square_radius = 11 ** 2
        self.radius_coefficent = 0

class BombBlast(GoodBullet):
    SQUARE_BOMB_RADIUS = 256 ** 2
    def initialize(self):
        self.set_image(images['bomb'])
        self.square_radius = self.SQUARE_BOMB_RADIUS
        angle = random.uniform(0, math.pi * 2)
        self.delta_x = Player.BULLET_SPEED * math.cos(angle)
        self.delta_y = Player.BULLET_SPEED * math.sin(angle)
        self.life = 12
        self.perish = False
    def update(self):
        self.frame = 4 - int(math.ceil(self.life / 3.0))
        self.decrease_life()
        self.cull()

class Spark(Sprite):
    def initialize(self):
        self.set_image(images['spark'])
        self.visible = True
        self.life = 10 + random.randrange(25)
    def update(self):
        if self.visible:
            self.visible = False
        elif random.randrange(3):
            self.visible = True
        self.y += 1
        self.decrease_life()

class BigSpark(Sprite):
    def initialize(self):
        self.set_image(images['bigspark'])
        self.delta_x = 0
        self.delta_y = 0
        self.life = 5 + random.randrange(10)
    def update(self):
        self.x += self.delta_x
        self.y += self.delta_y
        self.delta_x *= 0.9
        self.delta_y *= 0.9
        self.delta_y += 0.5
        self.decrease_life()
        if self.remove:
            spark = Spark()
            spark.move(self)
            spark.spawn()

class MegaSpark(Sprite):
    PHASE_CYCLE = 12
    def initialize(self):
        self.set_image(images['mega_spark'])
        r = random.random()
        a = r * math.pi * 2
        s = (random.expovariate(1) + 0.6) * pixels_per_second(300)
        self.delta_x = math.cos(a) * s
        self.delta_y = math.sin(a) * s
        if players[0].machines_remaining == 0:
            self.life = seconds(10)
        else:
            self.life = seconds(random.uniform(1, 3))
        self.type = random.choice([0, 4])
        if players[0].machines_remaining == 1:
            self.phase = int((r * 2 + s * -0.04) * self.PHASE_CYCLE) % self.PHASE_CYCLE
        else:
            self.phase = random.randrange(self.PHASE_CYCLE)
    def update(self):
        self.x += self.delta_x
        self.y += self.delta_y
        self.phase += 1
        self.phase %= self.PHASE_CYCLE
        self.frame = self.type + [0,0,0,1,1,2,3,3,3,2,2,1][self.phase]
        self.decrease_life()

class Enemy(Sprite):
    def initialize(self):
        self.set_image(images['fairy'])
        self.random_position()
        self.square_radius = 16 ** 2
        self.birthtime = level.frames
        self.value = 0
        self.hittable = True
        self.crashable = True
        self.destructible = True
    def explode(self, bullet):
        self.remove = True
        level.enemy_destroyed
        bullet.owner.add_score(self.value, self.value < 1000)
        score = Caption(bullet.owner.last_score_text(), tiny_font)
        score.center_at(self)
        score.life = seconds(1)
        score.spawn()
        if isinstance(bullet, BombBlast):
            big_spark_shock(bullet, self.value/5, self)
        else:
            big_spark_spray(bullet, self.value/5, 10, 1, self)
        level.renew_bg_around(self)
        play_sound('snare')
        level.reset_laziness_delay()
        level.enemy_destroyed(self)
class Fairy(object):
    PHASE_CYCLE = 10
    def setup_fairy_animation(self):
        self.facing_right = 0
        self.phase = random.randrange(self.PHASE_CYCLE)
    def update_fairy_animation(self):
        self.phase += 1
        self.phase %= self.PHASE_CYCLE
        self.frame = (self.phase / 5) % 2 + (self.facing_right and 2 or 0)

class ProtoGrunt(Enemy, Fairy):
    SPEED = 2.5
    FAST_SPEED = 2.5 * 1.5
    FAST_DISTANCE = 200 ** 2
    def initialize(self):
        Enemy.initialize(self)
        self.direction = random.random() * 2 * math.pi
        self.delta_direction = random.random() * 0.02
        self.idle_speed = random.random() * self.SPEED
        self.set_follow_delay()
        a = random.uniform(0, math.pi * 2)
        self.chase_offset_x = math.cos(a) * 190
        self.chase_offset_y = math.sin(a) * 190
        self.value = 100
        self.setup_fairy_animation()
    def set_follow_delay(self):
        self.follow_delay = seconds(random.uniform(0.5, 1.5))
    def update(self):
        player = self.nearest_player()
        if self.follow_delay:
            self.follow_delay -= 1
        if player and not self.follow_delay:
            if self.square_distance(player) < self.FAST_DISTANCE:
                dx, dy = self.direction_to(player)
                speed = self.FAST_SPEED
            else:
                speed = self.SPEED
                dx, dy = self.direction_to(player, (self.chase_offset_x, self.chase_offset_y))
            self.x += dx * speed
            self.facing_right = dx > 0
            self.y += dy * speed
            self.clamp_position()
        else:
            if not self.follow_delay:
                self.set_follow_delay()
            self.direction += self.delta_direction
            if random.randrange(20) == 0:
                self.delta_direction *= -1
            x = math.cos(self.direction)
            self.x += x * self.idle_speed
            self.facing_right = x > 0
            self.y += math.sin(self.direction) * self.idle_speed
            if self.clamp_position():
                self.direction += math.pi / 2
        self.update_fairy_animation()
class ProtoHulk(ProtoGrunt):
    def initialize(self):
        ProtoGrunt.initialize(self)
        self.set_image(images['proto_hulk'])
        self.destructible = False
        self.closed_eyelids = True
        self.blink()
    def blink(self):
        self.closed_eyelids = not self.closed_eyelids
        if self.closed_eyelids:
            self.blink_time = seconds(0.5)
        else:
            self.halt_movement = False
            self.blink_time = seconds(random.uniform(1.2, 2.5))
    def update(self):
        if self.blink_time:
            self.blink_time -= 1
        else:
            self.blink()
        if not self.halt_movement:
            self.direction += self.delta_direction
            if random.randrange(20) == 0:
                self.delta_direction *= -1
            x = math.cos(self.direction)
            self.x += x * self.idle_speed
            self.facing_right = x > 0
            self.y += math.sin(self.direction) * self.idle_speed
            if self.clamp_position():
                self.direction += math.pi / 2
        self.frame = (self.closed_eyelids and 1 or 0) + (self.facing_right and 2 or 0)
    def explode(self, bullet):
        self.closed_eyelids = True
        self.halt_movement = True
        self.blink_time = seconds(1)
        if isinstance(bullet, BombBlast):
            x, y = bullet.direction_to(self)
            self.x += x
            self.y += y
        else:
            self.x += bullet.delta_x * 0.2
            self.y += bullet.delta_y * 0.2
        self.clamp_position()

class SineFlyer(object):
    def proper_random_position(self):
        def random_position():
            self.phase0 = random.uniform(0, math.pi * 2)
            self.delta_phase0 = random.uniform(0.006, 0.02) * 4/3
            self.phase1 = random.uniform(0, math.pi * 2)
            self.delta_phase1 = random.uniform(0.006, 0.02)
            self.update_position()
        random_position()
        while self.distance(players[0]) < 500:
            random_position()
    def update_position(self):
        self.phase0 += self.delta_phase0
        self.phase1 += self.delta_phase1
        self.x = (math.cos(self.phase0) * 0.52 + 0.5) * WIDTH
        self.y = (math.sin(self.phase1) * 0.52 + 0.5) * HEIGHT
        self.clamp_position()

class ProtoSphereoid(Enemy, SineFlyer):
    def initialize(self):
        Enemy.initialize(self)
        self.set_image(images['proto_sphereoid'])
        self.proper_random_position()
        self.square_radius = 24 ** 2
        self.value = 1000
        self.frame = random.randrange(8)
        self.spawn_class = ProtoEnforcer
        self.spawns_remaining = 10
        self.current_spawn_delay = seconds(random.uniform(3, 5))
        self.spawn_delay = self.current_spawn_delay
        self.direction = random.choice([-1, 1])
    def update(self):
        self.update_position()
        self.frame += self.direction
        self.frame %= 8
        if self.spawn_delay > 0:
            self.spawn_delay -= 1
        else:
            spawn = self.spawn_class()
            spawn.move(self)
            spawn.phase0 = self.phase0
            spawn.phase1 = self.phase1
            spawn.spawn()
            big_spark_sphere(self, 5, 7)
            self.spawns_remaining -= 1
            if self.spawns_remaining:
                self.current_spawn_delay *= 0.8
                self.spawn_delay = self.current_spawn_delay
            else:
                big_spark_sphere(self, 20, 17)
                self.remove = True

class ProtoEnforcer(Enemy, SineFlyer, Fairy):
    def initialize(self):
        Enemy.initialize(self)
        self.set_image(images['red_fairy'])
        self.proper_random_position()
        self.value = 150
        self.setup_fairy_animation()
    def update(self):
        old_x = self.x
        self.update_position()
        self.facing_right = self.x > old_x and 2 or 0
        self.update_fairy_animation()
        if bar_start() and players[0].hittable():
            bullet = BadBullet()
            bullet.move(self)
            x, y = bullet.direction_to(players[0])
            x *= Player.SPEED / 2
            y *= Player.SPEED / 2
            bullet.delta_x, bullet.delta_y = x, y
            bullet.spawn()

class RotatingSpray(Sprite):
    SPARK_SPEED = pixels_per_second(500)
    MAX_LIFE = seconds(0.66)
    def initialize(self):
        self.life = self.MAX_LIFE
        self.visible = False
        self.direction = random.uniform(0, math.pi * 2)
    def update(self):
        self.direction -= 1.1
        for i in xrange(23):
            spark = BigSpark()
            spark.move(self)
            life_factor = (1 + self.life / float(self.MAX_LIFE))
            spark.delta_x = math.cos(self.direction + random.random()) * life_factor * self.SPARK_SPEED
            spark.delta_y = math.sin(self.direction + random.random()) * life_factor * self.SPARK_SPEED
            spark.spawn()
        if self.life == self.MAX_LIFE:
            big_spark_sphere(self, 50, self.SPARK_SPEED)
        self.decrease_life()

class Wisp(Enemy):
    X_MARGIN = 24
    Y_MARGIN = 24
    def initialize(self, enemy_class):
        Enemy.initialize(self)
        self.set_image(images['wisp'])
        self.crashable = False
        self.target_x = self.x
        self.target_y = self.y
        self.phase0 = random.random() * 2 * math.pi
        self.phase1 = random.random() * 2 * math.pi
        self.delta_phase0 = (random.random() - 0.5) * 0.05
        self.delta_phase1 = (random.random() - 0.5) * 0.05
        self.frame_phase = random.randrange(4)
        self.life = seconds(random.uniform(3.0, 4.0))
        self.visible = False
        self.enemy_class = enemy_class
        if enemy_class in [Cat, ProtoHulk]:
            self.hittable = False
        if enemy_class in [Cat]:
            self.preview_time = 0
        else:
            self.preview_time = seconds(1)
        self.value = 50
    def update(self):
        if not self.visible:
            if random.randrange(5) == 0:
                self.visible = True
        self.frame = ((self.life / 3) + self.frame_phase) % 4
        if self.life > 0:
            self.phase0 += self.delta_phase0
            self.phase1 += self.delta_phase1
            self.x = self.target_x + self.life * 3.0 * math.sin(self.phase0)
            self.y = self.target_y + self.life * 3.0 * math.sin(self.phase1)
            if random.randrange(13) == 0:
                spark = Spark()
                spark.move(self)
                spark.spawn()
        self.life -= 1
        if self.life <= 0:
            if even_bar_start():
                enemy = self.enemy_class()
                enemy.birthtime = self.birthtime
                enemy.move(self)
                enemy.spawn()
                #play_sound('poof')
                big_spark_sphere(self, 5, 7)
                self.remove = True
#         elif self.life < seconds(0.5):
#             big_spark_sphere(self, 1, 13)
    def draw(self):
        if self.life < self.preview_time:
            screen.blit(images['target'],
                        (self.target_x - 16, self.target_y - 16))
        Enemy.draw(self)


class Pickup(Sprite):
    def initialize(self):
        self.set_image(images['pickup'])
        self.square_radius = 32 ** 2
        self.mandatory_pickup = True
    def pickup_by(self, player):
        self.remove = True
        big_spark_sphere(self, 7, 7)
        play_sound('whap')

class Cat(Pickup):
    SPEED = 2
    def initialize(self):
        self.set_image(images['cat'])
        self.square_radius = 64 ** 2
        self.direction = random.uniform(0, math.pi * 2)
        self.delta_direction = random.uniform(-0.01, 0.01)
        self.facing_right = math.cos(self.direction) > 0
        self.speed = random.uniform(self.SPEED / 2, self.SPEED)
        self.wave = level.wave
        if self.wave < 0:
            self.mandatory_pickup = True
        self.will_escape = False
    def update(self):
        if random.randrange(16) == 0:
            self.delta_direction *= -1
        if self.will_escape:
            speed = self.SPEED * 1.8
        else:
            speed = self.speed
            self.direction += self.delta_direction
        dx = math.cos(self.direction) * speed
        self.x += dx
        self.facing_right = dx > 0
        self.frame = self.facing_right and 1 or 0
        self.y += math.sin(self.direction) * speed
        if self.will_escape:
            self.cull()
        else:
            if self.clamp_position():
                self.direction -= math.pi / 2
    def pickup_by(self, player):
        Pickup.pickup_by(self, player)
        player.add_score(level.cat_score[self.wave], False)
        score = Caption(player.last_score_text(), tiny_font, (0,255,0))
        score.center_at(player)
        score.life = seconds(1.5)
        score.spawn()
        if level.cat_score[self.wave] < 5000:
            level.cat_score[self.wave] += 1000

class Caption(Sprite):
    def initialize(self, text, font = caption_font, color = (255,255,255)):
        self.special = False
        if isinstance(text, pygame.Surface):
            self.image = text
            self.shadow = None
        else:
            self.image = font.render(text, True, color)
            self.shadow = font.render(text, True, (0,0,0))
        self.life = seconds(3)
        self.center_at(HEIGHT / 2)
        self.displace_x = 0
        self.displace_y = 0
        self.beat_displace = 0
    def center_at(self, arg):
        if hasattr(arg, "x"):
            self.x = arg.x - self.image.get_width() / 2
            self.y = arg.y - self.image.get_height() / 2
        else:
            self.x = WIDTH / 2 - self.image.get_width() / 2
            self.y = arg - self.image.get_height() / 2
        self.target_x = self.x
        self.target_y = self.y
    def draw(self):
        if self.visible and not self.remove:
            if self.shadow:
                screen.blit(self.shadow, (self.x + 3, self.y + 3))
            screen.blit(self.image, (self.x, self.y))
    def update(self):
        if self.beat_displace and beat_start():
            a = extra_random.uniform(0, math.pi * 2)
            self.displace_x += math.cos(a) * self.beat_displace
            self.displace_y += math.sin(a) * self.beat_displace
        self.displace_x *= 0.92
        self.displace_y *= 0.92
        self.x = self.target_x + self.displace_x
        self.y = self.target_y + self.displace_y
        self.decrease_life()
    def spawn(self):
        level.captions.append(self)

######################################################################

class Level(object):
    def __init__(self):
        self.frames = -1
        self.sprites = []
        self.captions = []
        self.freeze_time = 0
        self.wave = 0
        self.game_over = False
        self.pause = False
        bar_start.set(False)
        even_bar_start.set(False)
        self.music_bars = -1
        beat_start.set(False)
        self.music_beats = -1
        self.max_freeze_time = seconds(1.0)
        self.bg = pygame.Surface((WIDTH, HEIGHT))
    def cull_sprites(self):
        self.sprites = [s for s in self.sprites if not s.remove]
        self.captions = [s for s in self.captions if not s.remove]
    def restart(self, skip_tutorial = False):
        self.sprites = []
        self.captions = []
        self.frames = -1
        self.freeze_time = 0
        self.game_over = False
        self.game_over_time = 0
        self.pause = False
        for player in players:
            player.reset()
    def start_frame(self):
        self.frames += 1
        new_bars = int(music.bars())
        if not demo.playing:
            bar_start.set(new_bars != self.music_bars)
            even_bar_start.set(new_bars != self.music_bars and new_bars % 2 == 0)
        self.music_bars = new_bars
        new_beats = int(music.beats())
        if not demo.playing:
            beat_start.set(new_beats != self.music_beats)
        self.music_beats = new_beats
    def update(self):
        if self.freeze_time:
            self.freeze_time -= 1
            if self.freeze_time:
                return
            else:
                players[0].explode()
    def player_respawn(self):
        pass
    def restart_or_pause(self):
        if self.game_over:
            self.restart(skip_tutorial = True)
        else:
            self.pause = not self.pause
            if SOUND:
                if self.pause:
                    pygame.mixer.pause()
                    music.pause()
                else:
                    pygame.mixer.unpause()
                    music.unpause()
    def pick_random_pattern(self):
        self.xpattern = random.randrange(4)
        self.ypattern = random.randrange(4)
    def random_position(self):
        if random.randrange(5) == 0:
            return (random.randrange(WIDTH), random.randrange(HEIGHT))
        if self.xpattern == 0:
            x = (random.expovariate(4) * [0.5, -0.5][random.randrange(2)] + 0.5) * WIDTH
        elif self.xpattern == 1:
            x = (1 / (1+random.expovariate(2)) * [0.5, -0.5][random.randrange(2)] + 0.5) * WIDTH
        elif self.xpattern == 2:
            x = random.expovariate(5) * WIDTH
        elif self.xpattern == 3:
            x = (1-random.expovariate(5)) * WIDTH

        ypattern = random.randrange(4)
        if self.ypattern == 0:
            y = (random.expovariate(4) * [0.5, -0.5][random.randrange(2)] + 0.5) * HEIGHT
        elif self.ypattern == 1:
            y = (1 / (1+random.expovariate(2)) * [0.5, -0.5][random.randrange(2)] + 0.5) * HEIGHT
        elif self.ypattern == 2:
            y = random.expovariate(3) * HEIGHT
        elif self.ypattern == 3:
            y = (1-random.expovariate(3)) * HEIGHT

        return (x, y)
    RENEW_BG_SIZE = 16
    def renew_bg_around(self, sprite):
        x = sprite.x - self.RENEW_BG_SIZE / 2
        y = sprite.y - self.RENEW_BG_SIZE / 2
        w = h = self.RENEW_BG_SIZE
        self.bg.blit(self.new_bg, (x,y), (x,y,w,h))
    def enemy_destroyed(self, enemy):
        pass
    def reset_laziness_delay(self):
        pass

class TestLevel(Level):
    def __init__(self):
        Level.__init__(self)
    def restart(self, skip_tutorial = False):
        self.bg = pygame.Surface((WIDTH, HEIGHT))
        self.new_bg = images['living_grass']
        self.bg.blit(images['grass'], (0,0))
        self.skipped_tutorial = skip_tutorial
        if skip_tutorial:
            self.wave = 0
            music.play()
        else:
            self.wave = -5
            music.play('sparrow')
        self.music_bars = -1
        bar_start.set(False)
        even_bar_start.set(False)
        self.music_beats = -1
        beat_start.set(False)
        self.wave_message_delay = 0
        self.delayed_captions = {}
        self.wave_frames = 0
        self.min_wave_time = 0
        self.few_enemies = 0
        self.few_enemies_delay = seconds(grace_time(10))
        self.max_laziness_delay = seconds(grace_time(20))
        self.laziness_delay = self.max_laziness_delay
        self.cat_score = {}
    def spawn_cats(self, n):
        for i in xrange(n):
            wisp = Wisp(Cat)
            wisp.hittable = False
            wisp.spawn()
    def reset_cat_score(self):
        self.cat_score[self.wave] = 1000
    def keep_cat_score(self):
        self.cat_score[self.wave] = self.cat_score[self.wave - 1]
    def player_respawn(self):
        self.reset_all_cat_scores()
    def reset_all_cat_scores(self):
        for k in self.cat_score.keys():
            self.cat_score[k] = 1000
    def reset_laziness_delay(self):
        self.laziness_delay = self.max_laziness_delay
    RENEW_BG_SIZE = 16
    def renew_bg_around(self, sprite):
        x = sprite.x - self.RENEW_BG_SIZE / 2
        y = sprite.y - self.RENEW_BG_SIZE / 2
        w = h = self.RENEW_BG_SIZE
        self.bg.blit(self.new_bg, (x,y), (x,y,w,h))
    def new_wave(self):
        for cat in (c for c in self.sprites if isinstance(c, Cat)):
            cat.will_escape = True
        if self.wave < 1 and not self.game_over:
            self.captions = [c for c in self.captions if c.special]
        self.wave += 1
        self.pick_random_pattern()
        if self.wave <= 6:
            self.reset_cat_score()
        else:
            self.keep_cat_score()
        self.delayed_captions = {}
        self.wave_frames = 0
        if self.wave > 1 and not self.game_over and not self.wave_message_delay:
            caption = Caption(u"Våg %d" % self.wave)
            caption.center_at(HEIGHT - 200)
            caption.displace_x = WIDTH * [-1, 1][self.wave % 2]
            caption.spawn()
            self.wave_message_delay = seconds(7)

        #if self.wave > 0:
        #    play_sound('blippiblipp', True, False)

        if self.wave == -4:
            illustration = Caption(images['nili_gulmohar'])
            illustration.displace_y = HEIGHT
            illustration.spawn()
            caption = Caption(u"grt %s" % VERSION)
            caption.center_at(150)
            caption.displace_y = -400
            caption.spawn()
            wisp = Wisp(Pickup)
            wisp.life = seconds(7)
            wisp.target_x = WIDTH * (8.0/13)
            wisp.target_y = HEIGHT * (8.0/13)
            wisp.hittable = False
            wisp.spawn()
            caption = Caption(u"Men, gå till den gröna plutten då!")
            self.delayed_captions[seconds(22)] = [caption]
        elif self.wave == -3:
            wisp = Wisp(ProtoGrunt)
            wisp.target_x = 64
            wisp.target_y = 64
            wisp.life = seconds(12)
            wisp.hittable = False
            wisp.spawn()
            for s in [1, 16, 23]:
                self.delayed_captions[seconds(s)] = [Caption(u"Använd %s för att zappa" % keymap['fire_keys'])]
            caption = Caption(u"Glöm inte att du kan zappa diagonalt!")
            self.delayed_captions[seconds(7)] = [caption]
            caption = Caption(u"Zappa den farliga älvan!")
            caption.center_at(36)
            self.delayed_captions[seconds(13)] = [caption]
        elif self.wave == -2:
            caption = Caption(u"Rädda katterna från de sura påskäggen")
            self.delayed_captions[seconds(4)] = [caption]
            for i in xrange(3):
                wisp = Wisp(Cat)
                wisp.hittable = False
                wisp.spawn()
            self.sprites += [Wisp(ProtoHulk) for s in xrange(2)]
            caption = Caption(u"Gå till katterna och plocka upp dem")
            self.delayed_captions[seconds(9)] = [caption]
        elif self.wave == -1:
            players[0].bombs = 3
            caption0 = Caption(u"För att släppa en magisk bomb:")
            caption0.center_at(HEIGHT/2 - 30)
            caption1 = Caption(u"Skjut i alla riktningar i snabb följd")
            caption1.center_at(HEIGHT/2 + 30)
            self.delayed_captions[seconds(1)] = [caption0, caption1]
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(3)]
        elif self.wave == 0:
            self.sprites = [s for s in self.sprites if not isinstance(s, ProtoHulk)]
            self.sprites += [Wisp(ProtoGrunt) for n in xrange(5)]
            caption = Caption(u"Nu vet du allt du behöver")
            self.delayed_captions[seconds(2)] = [caption]
            self.delayed_captions[seconds(0.5)] = [caption]
            self.few_enemies = 0
            #self.few_enemies_delay = seconds(8.5)
        elif self.wave == 1:
            players[0].machines_remaining = 2
            players[0].score = 0
            players[0].bombs = 1
            if players[0].remove:
                players[0].machines_remaining += 1
            if not self.skipped_tutorial:
                caption = Caption(u"Nu börjar allvaret!")
                caption.displace_y = -HEIGHT
                self.delayed_captions[seconds(0.5)] = [caption]
            self.few_enemies = 5
            self.few_enemies_delay = seconds(grace_time(1.5))
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(17))]
            self.sprites += [Wisp(ProtoHulk) for s in xrange(enemies(1))]
            self.spawn_cats(3)
        elif self.wave == 2:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(50))]
            self.spawn_cats(4)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(enemies(2))]
            self.sprites += [ProtoSphereoid() for n in xrange(enemies(1))]
        elif self.wave == 3:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(60))]
            self.spawn_cats(5)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(enemies(2))]
            self.sprites += [ProtoSphereoid() for n in xrange(enemies(2))]
        elif self.wave == 4:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(70))]
            self.spawn_cats(6)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(enemies(2))]
            self.sprites += [ProtoSphereoid() for n in xrange(enemies(3))]
        elif self.wave == 5:
            self.few_enemies = 0
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(80))]
            self.spawn_cats(7)
            self.sprites += [ProtoSphereoid() for n in xrange(enemies(4))]
        elif self.wave > 5:
            self.max_laziness_delay = seconds(grace_time(7.5))
            self.few_enemies = 100
            self.few_enemies_delay = seconds(grace_time(3.5))
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(self.wave * 3))]
            self.sprites += [ProtoSphereoid() for n in xrange(enemies(2))]
            self.spawn_cats(2)
        self.reset_laziness_delay()
    def update(self):
        Level.update(self)
        if self.laziness_delay:
            self.laziness_delay -= 1
        if self.wave_message_delay:
            self.wave_message_delay -= 1
        if self.game_over:
            self.game_over_time += 1
            if self.game_over_time == seconds(2.0):
                #play_sound('gong')
                pass
            if self.game_over_time == seconds(3.5):
                caption = Caption(u"Tryck START för att börja om")
                caption.life = seconds(15)
                caption.spawn()
        self.wave_frames += 1
        enemies = [s for s in level.sprites if isinstance(s, Enemy) and s.destructible]

        if self.delayed_captions.has_key(self.wave_frames):
            for c in self.delayed_captions[self.wave_frames]:
                c.spawn()

        if self.wave == -4:
            if (self.wave_frames - seconds(4)) % seconds(7) == 0:
                caption = Caption(u"Använd %s för att gå omkring" % keymap['move_keys'])
                caption.spawn()

        if self.wave_frames > self.min_wave_time:
            total_enemies = len(enemies)
            mandatory_pickups = [p for p in level.sprites if hasattr(p, 'mandatory_pickup')]

            if len(mandatory_pickups) == 0:
                if self.laziness_delay <= 0:
                    if bar_start():
                        level.new_wave()
                if total_enemies == 0:
                    if bar_start():
                        level.new_wave()
                elif self.few_enemies and total_enemies <= self.few_enemies:
                    if self.few_enemies_delay:
                        self.few_enemies_delay -= 1
                    elif bar_start():
                        level.new_wave()

    def restart_or_pause(self):
        if self.game_over:
            self.restart(skip_tutorial = True)
        elif self.wave < 1:
            self.skipped_tutorial = True
            self.wave = 0
            self.sprites = players[:]
            self.new_wave()
        else:
            self.pause = not self.pause
            if SOUND:
                if self.pause:
                    pygame.mixer.pause()
                    music.pause()
                else:
                    pygame.mixer.unpause()
                    music.unpause()

class DynamicDifficultyLevel(Level):
    def __init__(self):
        Level.__init__(self)
        self.new_bg = images['living_grass']
    def restart(self, skip_tutorial = False):
        Level.restart(self)
        self.bg.blit(images['grass'], (0,0))
        self.sample_interval = seconds(8)
        self.target_enemy_lifespan = seconds(8)
        self.sample_time = 0
        self.defeated_enemies = 0
        self.defeated_enemy_life_time = 0
        self.average_enemy_lifespan = 0
        self.fairies_per_wave = 1
        music.play()
        for player in players:
            player.reset()
        self.wave = 0
        self.new_wave()
    def new_wave(self):
        self.wave += 1
        self.target_enemy_lifespan += seconds(0.1)
        msg = u"avgl: %0.1f; target: %0.1f; n: %d" % (self.average_enemy_lifespan,
                                                      self.target_enemy_lifespan,
                                                      self.fairies_per_wave)
        print msg
        caption = Caption(msg)
        caption.center_at(HEIGHT - 200)
        caption.displace_x = WIDTH * [-1, 1][self.wave % 2]
        caption.spawn()
        self.pick_random_pattern()
        self.sprites += [Wisp(ProtoGrunt) for s in xrange(enemies(self.fairies_per_wave))]
        self.sample_time = self.sample_interval
    def perform_difficulty_sampling(self):
        remaining_enemies = [s for s in self.sprites if isinstance(s, Enemy)]
        enemies = self.defeated_enemies + len(remaining_enemies)
        lifespan = self.defeated_enemy_life_time + sum([self.age(e.birthtime) for e in remaining_enemies])

        self.average_enemy_lifespan = float(lifespan) / enemies
        diff_factor = float(self.average_enemy_lifespan) / self.target_enemy_lifespan
        self.fairies_per_wave = round(self.fairies_per_wave / diff_factor) + 1
        self.defeated_enemies = 0
        self.defeated_enemy_life_time = 0
        self.new_wave()
    def update(self):
        Level.update(self)
        if not self.game_over:
            if self.sample_time:
                self.sample_time -= 1
            else:
                self.perform_difficulty_sampling()
            enemies = [e for e in self.sprites if isinstance(e, Enemy)]
            if len(enemies) == 0:
                self.perform_difficulty_sampling()

    def age(self, birth):
        return min(self.frames - birth, self.target_enemy_lifespan * 2)
    def enemy_destroyed(self, enemy):
        self.defeated_enemies += 1
        self.defeated_enemy_life_time += self.age(enemy.birthtime)

######################################################################

def update():
    if not players[0].remove:
        if not level.freeze_time:
            if move_up() and not move_down():
                players[0].y -= players[0].SPEED
            elif move_down() and not move_up():
                players[0].y += players[0].SPEED
            if move_left() and not move_right():
                players[0].x -= players[0].SPEED
            elif move_right() and not move_left():
                players[0].x += players[0].SPEED
            players[0].clamp_position()

        x = y = 0
        if fire_up() and not fire_down():
            y = -1
        elif fire_down() and not fire_up():
            y = 1
        if fire_left() and not fire_right():
            x = -1
        elif fire_right() and not fire_left():
            x = 1
        if (x or y) and not level.freeze_time:
            players[0].fire(x, y)

        t = level.frames
        if not len([b for b in [fire_up, fire_down, fire_left, fire_right] if t - b.last_push_frame > seconds(0.35)]):
            players[0].bomb()

    level.update()

    if level.freeze_time:
        return

    for foo in chain(level.sprites, level.captions):
        foo.update()

    level.cull_sprites()

    good_bullets = [s for s in level.sprites if isinstance(s, GoodBullet)]
    enemies = [s for s in level.sprites if isinstance(s, Enemy)]

    for enemy in [e for e in enemies if e.hittable]:
        for bullet in good_bullets:
            if bullet.touches(enemy):
                if bullet.perish:
                    bullet.remove = True
                    good_bullets.remove(bullet)
                enemy.explode(bullet)

    hittable_players = [p for p in players if p.hittable()]
    hazards = [e for e in enemies if e.crashable] + [s for s in level.sprites if isinstance(s, BadBullet)]
    for hazard in hazards:
        for player in hittable_players:
            if player.touches(hazard):
                if player.bombs >= 2 and not player.bomb_delay:
                    level.freeze_time = level.max_freeze_time
                    play_sound('blippiblipp', True)
                else:
                    player.explode()
                hittable_players.remove(player)
                break

    pickups = [p for p in level.sprites if isinstance(p, Pickup)]
    living_players = [p for p in players if not p.remove]
    for player in living_players:
        for pickup in pickups:
            if player.touches(pickup):
                pickup.pickup_by(player)
                pickups.remove(pickup)
                continue

    for player in [p for p in players if p.machines_remaining]:
        if player.respawn_delay:
            if player.respawn_delay == 1:
                if bar_start():
                    player.respawn_delay = 0
                    player.respawn()
            else:
                player.respawn_delay -= 1

BAR_MARGIN = 5
BAR_WIDTH = 8
def draw_bars(number, max, charge, discharge):
    if discharge:
        color = (255,0,0)
    elif number < 2:
        color = (255,255,0)
    else:
        color = (255,255,255)
    bar_width = WIDTH / max
    for n in xrange(number):
        screen.fill((0,0,0), (n*bar_width + BAR_MARGIN + 2, BAR_MARGIN + 2, bar_width - (BAR_MARGIN + 2), BAR_WIDTH))
        screen.fill(color, (n*bar_width + BAR_MARGIN, BAR_MARGIN, bar_width - (BAR_MARGIN + 2), BAR_WIDTH))
    if charge:
        charge_width = int(bar_width * charge - (BAR_MARGIN + 2))
        charge_x = (bar_width - charge_width) / 2
        screen.fill((0,0,0), (number*bar_width + (BAR_MARGIN + 2) + charge_x, (BAR_MARGIN + 2), charge_width, BAR_WIDTH))
        screen.fill(color, (number*bar_width + BAR_MARGIN + charge_x, BAR_MARGIN, charge_width, BAR_WIDTH))

def redraw():
    screen.blit(level.bg, (0,0))
    for sprite in level.sprites:
        sprite.draw()
    if level.freeze_time:
        fraction = level.freeze_time / float(level.max_freeze_time)
        x = players[0].x
        y = players[0].y
        x0 = players[0].x * (1 - fraction)
        x1 = x + (WIDTH - x) * fraction
        y0 = players[0].y * (1 - fraction)
        y1 = y + (HEIGHT - y) * fraction
        w = x1-x0
        h = y1-y0
        screen.blit(images['death'], (x0,y0), (x0, y0, w, h))
    if level.game_over or level.pause or demo.freeze:
        screen.blit(images['dark'], (0,0))
    for caption in level.captions:
        caption.draw()
    if players[0].y < HEIGHT - 64 or players[0].x > WIDTH / 3 or players[0].remove:
        shadow = font.render(players[0].score_text(), True, (0,0,0))
        y = HEIGHT - shadow.get_height() - 2
        screen.blit(shadow, (2, y + 2))
        text = font.render(players[0].score_text(), True, (255,255,255))
        screen.blit(text, (0, y))
        x = text.get_width() + 8
        for i in xrange(players[0].machines_remaining):
            screen.blit(images['machine'], (x + i*34, HEIGHT - 40))
    #bars = tiny_font.render('%d' % int(music.bars()), True, (255,0,0))
    #screen.blit(bars, (WIDTH - bars.get_width(), HEIGHT - bars.get_height()))

    max_bombs = max(players[0].bombs + 1, 4)
    if players[0].bomb_delay > 0:
        draw_bars(players[0].bombs, max_bombs, players[0].bomb_delay_fraction(), True)
    else:
        draw_bars(players[0].bombs, max_bombs, min(1, players[0].charge), False)
    #draw_bars(2, 4, 0.3, False)

    fps = clock.get_fps()
    if fps < TARGET_FPS * 0.8:
        color = (255,0,0)
        image = images['snail']
        fps_font = small_font
    elif fps < TARGET_FPS * 0.95:
        color = (255,255,0)
        image = images['turtle']
        fps_font = small_font
    else:
        color = (128,128,128)
        image = None
        fps_font = tiny_font
    text = '%d fps' % fps
    fps_shadow = fps_font.render(text, True, (0,0,0))
    fps_text = fps_font.render(text, True, color)
    w = fps_shadow.get_width()
    screen.blit(fps_shadow, (WIDTH - w, 2))
    screen.blit(fps_text, (WIDTH - w - 2, 0))
    if image:
        screen.blit(image, (WIDTH - w - 64, -16))

    pygame.display.update()

######################################################################

random = random_module.Random()
extra_random = random_module.Random()

######################################################################

running = True
first_frame = True
clock = pygame.time.Clock()

demo = DemoRecorder(all_buttons)
if len(sys.argv) > 1:
    demo.play(sys.argv[1])
else:
    demo.record()

music = Music()
players = [Player()]
#level = TestLevel()
level = DynamicDifficultyLevel()
level.restart()

while running:
    level.start_frame()
    demo.advance_frame()
    if not level.pause and not demo.freeze:
        update()
    redraw()

    if first_frame:
        for event in pygame.event.get():
            pass
        first_frame = False
    else:
        for event in pygame.event.get():
            if event.type == END_MUSIC_EVENT:
                music.next()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RETURN and event.mod:
                    pygame.display.toggle_fullscreen()
            if not demo.playing and not demo.freeze:
                if event.type == pygame.KEYDOWN:
                    if keymap.has_key(event.key):
                            keymap[event.key].set(True)
                    elif keymap_select_map.has_key(event.key):
                        keymap = keymap_select_map[event.key]
                        print 'Magiskt keymapbyte till: %s' % keymap['name']
                        keymap[event.key].set(True)
                    else:
                        if reverse_keymap.has_key(event.key):
                            name = reverse_keymap[event.key]
                        else:
                            name = '%d' % event.key
                        print 'Obunden tangent: %s' % name
                elif event.type == pygame.KEYUP:
                    if keymap.has_key(event.key):
                        keymap[event.key].set(False)
                elif event.type == pygame.JOYBUTTONDOWN:
                    buttons = joysticks[event.joy].bindings['buttons']
                    if buttons.has_key(event.button):
                        buttons[event.button].set(True)
                    else:
                        print 'Obunden knapp %d på %s' % (event.button, joysticks[event.joy].name)
                elif event.type == pygame.JOYBUTTONUP:
                    buttons = joysticks[event.joy].bindings['buttons']
                    if buttons.has_key(event.button):
                        buttons[event.button].set(False)
                elif event.type == pygame.JOYAXISMOTION:
                    axes = joysticks[event.joy].bindings['axes']
                    if axes.has_key(event.axis):
                        axes[event.axis].set(event.value)
                    else:
                        print 'Obunden axel %d på %s' % (event.axis, joysticks[event.joy].name)
        if start.get_triggered():
            level.restart_or_pause()

    clock.tick(TARGET_FPS)

demo.stop()
pygame.quit()
