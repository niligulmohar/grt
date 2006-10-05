#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pygame
import os.path, random, math
from itertools import chain

try:
    import psyco
    psyco.full()
except:
    pass

VERSION = 0.2
WIDTH, HEIGHT = (1024, 768)
MAX_FPS = 45
FLAGS = 0 #pygame.FULLSCREEN
SOUND = True

pygame.init()
if not pygame.mixer.get_init():
    SOUND = False
else:
    pygame.mixer.set_reserved(1)
    priority_channel = pygame.mixer.Channel(0)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | FLAGS)
pygame.mouse.set_visible(False)

def make_font(name, size):
    return pygame.font.Font(os.path.join('data', name + '.ttf'), size)

tiny_font, small_font, font, caption_font = (make_font('Titania-Regular', size) for size in (20, 32, 36, 48))

def seconds(sec):
    return int(sec * MAX_FPS)

######################################################################

class Button(object):
    def __init__(self):
        self.state = False
        self.last_push_time = -1000
        self.triggered = False
    def set(self, state):
        self.state = state
        if state:
            self.last_push_time = pygame.time.get_ticks()
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

move_y = Axis(move_up, move_down)
move_x = Axis(move_left, move_right)
fire_y = Axis(fire_up, fire_down)
fire_x = Axis(fire_left, fire_right)

class Joystick(object):
    def __init__(self, joy):
        self.joystick = joy
        self.name = joy.get_name()
        if joystick_maps.has_key(self.name):
            joy.init()
            self.bindings = joystick_maps[self.name]
        else:
            print 'Unrecognized joystick: %s' % self.name

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

keymap = { 'undecided_keymap': True,
           pygame.K_1: start,
           pygame.K_p: start,
           pygame.K_PAUSE: start,
           'fire_keys': 'I J K L',
           'move_keys': 'E S D F' }


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
                 'move_keys': 'piltangenterna' }]

######################################################################

image_names = ['grass',
               'dark',
               'nili_gulmohar',
               'player',
               'bullet',
               'spark',
               'bigspark',
               'wisp',
               'fairy',
               'proto_hulk',
               'machine',
               'pickup',
               'eights',
               'target',
               'bomb',
               'aura',
               'enemy_placeholder']

images = {}

for name in image_names:
    surf = pygame.image.load(os.path.join('data', name + '.png'))
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
        sounds[name] = pygame.mixer.Sound(os.path.join('data', name + '.wav'))

def play_sound(name, priority = False, really_high_priority = True):
    if SOUND:
        if priority:
            if really_high_priority or not priority_channel.get_busy():
                priority_channel.play(sounds[name])
        else:
            sounds[name].play()

######################################################################

songs = { 'sparrow': "GibIt - Please, Don't Eat The Sparrow",
          'solitude': 'GibIt - Solitude of a Shapeless Outcast',
          'perfect': "GibIt - 'Perfect'" }

def play_music(song):
    if SOUND:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(os.path.join('data', song + '.ogg'))
        pygame.mixer.music.play(-1)
        songname = Caption(song, small_font)
        w = songname.image.get_width()
        x = WIDTH - w - 4
        songname.target_x = x
        songname.target_y = HEIGHT - 40
        songname.displace_x = w + 40
        songname.special = True
        songname.life = seconds(7.5)
        songname.spawn()
        notes = Caption(images['eights'])
        notes.special = True
        notes.target_x = x - 40
        notes.displace_x = w + 40
        notes.target_y = HEIGHT - 40
        notes.life = seconds(7.5)
        notes.spawn()

def stop_music():
    if SOUND:
        pygame.mixer.music.fadeout(2000)

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
    def square_distance(self, ref):
        return (self.x - ref.x) ** 2 + (self.y - ref.y) ** 2
    def distance(self, ref):
        return math.sqrt(self.square_distance(ref))
    def vector_to(self, ref):
        x = ref.x - self.x
        y = ref.y - self.y
        return (x, y)
    def direction_to(self, ref):
        x, y = self.vector_to(ref)
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

def big_spark_spray(ref, amount, speed0, speed1, pos = None):
    if not pos:
        pos = ref
    for i in xrange(amount):
        for n in (-1.0, 1.0):
            spark = BigSpark()
            spark.move(pos)
            spark.delta_x = (-n*ref.delta_y + (random.random()-0.5) * speed0) * speed1
            spark.delta_y = (n*ref.delta_x + (random.random()-0.5) * speed0) * speed1
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
    SPEED = 5
    BULLET_SPEED = 24
    X_MARGIN = 10
    Y_MARGIN = 23
    FIRE_DELAY = 4
    BOMB_DELAY = seconds(2)
    INVULNERABILITY_DELAY = seconds(3)

    def initialize(self):
        self.set_image(images['player'])
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
            self.bombs = 1
            self.bomb()
        self.bombs = 0
        self.charge = 0
        level.reset_cat_score()
    def hittable(self):
        return self.invulnerability_delay == 0 and not self.remove
    def update(self):
        if self.invulnerability_delay:
            self.invulnerability_delay -= 1
        #self.visible = self.invulnerability_delay % 2 == 0
        if self.fire_delay:
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
        if self.bomb_delay == 0 and self.bombs > 0:
            play_sound('boohm', True)
            bullet = BombBlast()
            bullet.move(self)
            bullet.owner = self
            bullet.spawn()
            self.bombs -= 1
            self.charge = 0
            self.bomb_delay = self.BOMB_DELAY
            self.invulnerability_delay = self.INVULNERABILITY_DELAY

    def fire(self, dx_param, dy_param):
        if not self.fire_delay:
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
            big_spark_spray(bullet, 3, self.BULLET_SPEED, 0.3)
    def add_score(self, score, bonus = True):
        if bonus:
            self.last_score = int(score * (1 + self.bombs/2.0 + self.charge/2.5))
            if not (self.bomb_delay or self.remove):
                self.charge += score / 3000.0
        else:
            self.last_score = score
        self.score += self.last_score
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
        self.charge = 0
        self.bombs = 0
        self.bomb_delay = 0
        self.remove = True
        self.respawn_delay = seconds(1)
        if self.machines_remaining == 0:
            stop_music()
            level.game_over = True
    def bomb_delay_fraction(self):
        return float(self.bomb_delay) / self.BOMB_DELAY
    def draw(self):
        if self.invulnerability_delay > 16:
            self.draw_image(images['aura'], self.invulnerability_delay % 2)
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
        if self.remove:
            self.owner.subtract_charge(0.005)
        if random.randrange(8) == 0:
            spark = Spark()
            spark.move(self)
            spark.spawn()

class GoodBullet(Bullet):
    pass

class BadBullet(Bullet):
    pass

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
        self.frame = 4 - int(math.ceil(self.life/ 3.0))
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

class Enemy(Sprite):
    def initialize(self):
        self.set_image(images['fairy'])
        self.random_position()
        self.square_radius = 16 ** 2
        self.value = 0
        self.hittable = True
        self.crashable = True
        self.destructible = True
    def explode(self, bullet):
        self.remove = True
        bullet.owner.add_score(self.value)
        score = Caption(bullet.owner.last_score_text(), tiny_font)
        score.center_at(self)
        score.life = seconds(1)
        score.spawn()
        big_spark_spray(bullet, 20, 32, 0.5, self)
        play_sound('snare')

class ProtoGrunt(Enemy):
    SPEED = 2.5
    FAST_SPEED = 2.5 * 1.5
    FAST_DISTANCE = 200 ** 2
    PHASE_CYCLE = 10
    def initialize(self):
        Enemy.initialize(self)
        self.direction = random.random() * 2 * math.pi
        self.delta_direction = random.random() * 0.02
        self.idle_speed = random.random() * self.SPEED
        self.facing_right = 0
        self.phase = random.randrange(self.PHASE_CYCLE)
        self.set_follow_delay()
        if level.wave > 0:
            self.value = 100
        else:
            self.value = 0
    def set_follow_delay(self):
        self.follow_delay = random.randrange(seconds(3)) + seconds(1)
    def update(self):
        player = self.nearest_player()
        if self.follow_delay:
            self.follow_delay -= 1
        if player and not self.follow_delay:
            dx, dy = self.direction_to(player)
            if self.square_distance(player) < self.FAST_DISTANCE:
                speed = self.FAST_SPEED
            else:
                speed = self.SPEED
            self.x += dx * speed
            self.facing_right = dx > 0
            self.y += dy * speed
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
        self.phase += 1
        self.phase %= self.PHASE_CYCLE
        self.frame = (self.phase / 5) % 2 + (self.facing_right and 2 or 0)
class ProtoHulk(ProtoGrunt):
    PHASE_CYCLE = seconds(2)
    def initialize(self):
        ProtoGrunt.initialize(self)
        self.set_image(images['proto_hulk'])
        self.destructible = False
    def update(self):
        self.direction += self.delta_direction
        if random.randrange(20) == 0:
            self.delta_direction *= -1
        x = math.cos(self.direction)
        self.x += x * self.idle_speed
        self.facing_right = x > 0
        self.y += math.sin(self.direction) * self.idle_speed
        if self.clamp_position():
            self.direction += math.pi / 2
        self.phase += 1
        self.phase %= self.PHASE_CYCLE
        self.frame = (self.phase > seconds(1.7) and 1 or 0) + (self.facing_right and 2 or 0)
    def explode(self, bullet):
        pass
class RotatingSpray(Sprite):
    SPARK_SPEED = 18
    MAX_LIFE = 9
    def initialize(self):
        self.life = self.MAX_LIFE
        self.visible = False
        self.direction = random.uniform(0, math.pi * 2)
    def update(self):
        self.direction += 1.1
        for i in xrange(11):
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
    X_MARGIN = 48
    Y_MARGIN = 48
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
        self.life = 250 + random.randrange(25)
        self.preview_time = seconds(1)
        self.visible = False
        self.enemy_class = enemy_class
        if enemy_class in [Cat, ProtoHulk]:
            self.hittable = False
        if level.wave > 0:
            self.value = 50
        else:
            self.value = 0
    def update(self):
        if not self.visible:
            if random.randrange(10) == 0:
                self.visible = True
        self.frame = ((self.life / 3) + self.frame_phase) % 4
        self.phase0 += self.delta_phase0
        self.phase1 += self.delta_phase1
        self.x = self.target_x + self.life * 3.0 * math.sin(self.phase0)
        self.y = self.target_y + self.life * 3.0 * math.sin(self.phase1)
        if random.randrange(13) == 0:
            spark = Spark()
            spark.move(self)
            spark.spawn()
        self.decrease_life()
        if self.life == 0:
            enemy = self.enemy_class()
            enemy.move(self)
            enemy.spawn()
            play_sound('poof')
            big_spark_sphere(self, 5, 7)
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
    def mandatory(self):
        return True
    def pickup_by(self, player):
        self.remove = True
        big_spark_sphere(self, 7, 7)
        play_sound('whap')

class Cat(Pickup):
    SPEED = 2
    def initialize(self):
        self.set_image(images['enemy_placeholder'])
        self.square_radius = 32 ** 2
        self.direction = random.uniform(0, math.pi * 2)
        self.delta_direction = random.uniform(-0.01, 0.01)
        self.speed = random.uniform(self.SPEED / 2, self.SPEED)
        self.will_escape = False
    def update(self):
        if random.randrange(16) == 0:
            self.delta_direction *= -1
        if self.will_escape:
            speed = self.SPEED * 1.8
        else:
            speed = self.speed
            self.direction += self.delta_direction
        self.x += math.cos(self.direction) * speed
        self.y += math.sin(self.direction) * speed
        if self.will_escape:
            self.cull()
        else:
            if self.clamp_position():
                self.direction -= math.pi / 2
    def mandatory(self):
        return False
    def pickup_by(self, player):
        Pickup.pickup_by(self, player)
        player.add_score(level.cat_score, False)
        score = Caption(player.last_score_text(), tiny_font)
        score.center_at(player)
        score.life = seconds(1.5)
        score.spawn()
        if level.cat_score < 5000:
            level.cat_score += 1000

class Caption(Sprite):
    def initialize(self, text, font = caption_font):
        self.special = False
        if isinstance(text, pygame.Surface):
            self.image = text
            self.shadow = None
        else:
            self.image = font.render(text, True, (255,255,255))
            self.shadow = font.render(text, True, (0,0,0))
        self.life = seconds(3)
        self.center_at(HEIGHT / 2)
        self.displace_x = 0
        self.displace_y = 0
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
        pass
    def restart(self, skip_tutorial = False):
        self.skipped_tutorial = skip_tutorial
        self.sprites = []
        self.captions = []
        if skip_tutorial:
            self.wave = 0
            play_music(random.choice(songs.values()))
        else:
            self.wave = -5
            play_music(songs['sparrow'])
        self.delayed_captions = {}
        self.wave_frames = 0
        self.min_wave_time = 0
        self.few_enemies = 0
        self.few_enemies_delay = seconds(10)
        self.cat_score = 1000
        self.game_over = False
        self.game_over_time = 0
        self.pause = False
        for player in players:
            player.reset()
        #play_music(random.choice(['solitude', 'perfect']))
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
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.unpause()
                    pygame.mixer.music.unpause()
    def spawn_cats(self, n):
        for i in xrange(n):
            wisp = Wisp(Cat)
            wisp.hittable = False
            wisp.spawn()
    def reset_cat_score(self):
        self.cat_score = 1000
    def new_wave(self):
        self.reset_cat_score()
        for cat in (c for c in self.sprites if isinstance(c, Cat)):
            cat.will_escape = True
        if self.wave < 1 and not self.game_over:
            self.captions = [c for c in self.captions if c.special]
        self.wave += 1
        self.delayed_captions = {}
        self.wave_frames = 0
        if self.wave > 1 and not self.game_over:
            caption = Caption(u"Våg %d" % self.wave)
            caption.center_at(HEIGHT - 200)
            caption.displace_x = WIDTH * [-1, 1][self.wave % 2]
            caption.spawn()

        if self.wave > 0:
            play_sound('blippiblipp', True, False)

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
            self.sprites += [Wisp(ProtoGrunt) for n in xrange(3)]
            caption = Caption(u"Nu vet du allt du behöver")
            self.delayed_captions[seconds(2)] = [caption]
            self.delayed_captions[seconds(0.5)] = [caption]
            self.few_enemies = 0
            #self.few_enemies_delay = seconds(8.5)
        elif self.wave == 1:
            players[0].machines_remaining = 2
            if players[0].remove:
                players[0].machines_remaining += 1
            if not self.skipped_tutorial:
                caption = Caption(u"Nu börjar allvaret!")
                caption.displace_y = -HEIGHT
                self.delayed_captions[seconds(0.5)] = [caption]
            self.few_enemies = 5
            self.few_enemies_delay = seconds(1.5)
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(17)]
            self.sprites += [Wisp(ProtoHulk) for s in xrange(1)]
            self.spawn_cats(3)
        elif self.wave == 2:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(50)]
            self.spawn_cats(4)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(2)]
        elif self.wave == 3:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(60)]
            self.spawn_cats(5)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(2)]
        elif self.wave == 4:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(70)]
            self.spawn_cats(6)
            self.sprites += [Wisp(ProtoHulk) for s in xrange(2)]
        elif self.wave == 5:
            self.few_enemies = 0
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(80)]
            self.spawn_cats(7)
        elif self.wave > 5:
            self.few_enemies = 100
            self.few_enemies_delay = seconds(3.5)
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(self.wave * 3)]
            self.spawn_cats(1)
    def update(self):
        if self.game_over:
            self.game_over_time += 1
            if self.game_over_time == seconds(2.0):
                #play_sound('gong')
                pass
            if self.game_over_time == seconds(3.5):
                caption = Caption(u"Tryck 1 för att starta om")
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
            mandatory_pickups = [p for p in level.sprites if isinstance(p, Pickup) and p.mandatory()]

            if total_enemies == 0 and len(mandatory_pickups) == 0:
                level.new_wave()
            elif self.few_enemies and total_enemies <= self.few_enemies:
                if self.few_enemies_delay:
                    self.few_enemies_delay -= 1
                else:
                    level.new_wave()
    def cull_sprites(self):
        self.sprites = [s for s in self.sprites if not s.remove]
        self.captions = [s for s in self.captions if not s.remove]
    def random_position(self):
        if random.randrange(2):
            x = (random.expovariate(2) * [0.5, -0.5][random.randrange(2)] + 0.5) * WIDTH
            y = (random.expovariate(2) * [0.5, -0.5][random.randrange(2)] + 0.5) * HEIGHT
        else:
            x = (1 / (1+random.expovariate(2)) * [0.5, -0.5][random.randrange(2)] + 0.5) * WIDTH
            y = (1 / (1+random.expovariate(2)) * [0.5, -0.5][random.randrange(2)] + 0.5) * HEIGHT
        return (x, y)

players = [Player()]
level = Level()
level.restart()
#level.sprites += players

######################################################################

def update():
    if not players[0].remove:
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
        if x or y:
            players[0].fire(x, y)

        t = pygame.time.get_ticks()
        if not len([b for b in [fire_up, fire_down, fire_left, fire_right] if t - b.last_push_time > 350]):
            players[0].bomb()

    level.update()

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
    for enemy in [e for e in enemies if e.crashable]:
        for player in hittable_players:
            if player.touches(enemy):
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
            player.respawn_delay -= 1
            if player.respawn_delay == 0:
                player.respawn()

BAR_MARGIN = 5
BAR_WIDTH = 8
def draw_bars(number, max, charge, discharge):
    if discharge:
        color = (255,0,0)
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
    screen.blit(images['grass'], (0,0))
    for sprite in level.sprites:
        sprite.draw()
    if level.game_over or level.pause:
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
    max_bombs = max(players[0].bombs + 1, 4)
    if players[0].bomb_delay > 0:
        draw_bars(players[0].bombs, max_bombs, players[0].bomb_delay_fraction(), True)
    else:
        draw_bars(players[0].bombs, max_bombs, min(1, players[0].charge), False)
    #draw_bars(2, 4, 0.3, False)
    pygame.display.update()

######################################################################

running = True
clock = pygame.time.Clock()

while running:
    if not level.pause:
        update()
    redraw()

    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_RETURN and event.mod:
                pygame.display.toggle_fullscreen()
            elif keymap.has_key('undecided_keymap'):
                for alt in keymap_alts:
                    if alt.has_key(event.key):
                        keymap = alt
                        keymap[event.key].set(True)
                        break
            else:
                if keymap.has_key(event.key):
                    keymap[event.key].set(True)
        elif event.type == pygame.KEYUP:
            if keymap.has_key(event.key):
                keymap[event.key].set(False)
        elif event.type == pygame.JOYBUTTONDOWN:
            buttons = joysticks[event.joy].bindings['buttons']
            if buttons.has_key(event.button):
                buttons[event.button].set(True)
            else:
                print 'unbound button %d on %s' % (event.button, joysticks[event.joy].name)
        elif event.type == pygame.JOYBUTTONUP:
            buttons = joysticks[event.joy].bindings['buttons']
            if buttons.has_key(event.button):
                buttons[event.button].set(False)
        elif event.type == pygame.JOYAXISMOTION:
            axes = joysticks[event.joy].bindings['axes']
            if axes.has_key(event.axis):
                axes[event.axis].set(event.value)
            else:
                print 'unbound axis %d on %s' % (event.axis, joysticks[event.joy].name)

    if start.get_triggered():
        level.restart_or_pause()

    clock.tick(MAX_FPS)
