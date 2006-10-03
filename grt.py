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

VERSION = 0.1
WIDTH, HEIGHT = (1024, 768)
MAX_FPS = 45
FLAGS = 0 #pygame.FULLSCREEN
SOUND = True

pygame.init()
if not pygame.mixer.get_init():
    SOUND = False
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.DOUBLEBUF | FLAGS)
pygame.mouse.set_visible(False)

def make_font(name, size):
    return pygame.font.Font(os.path.join('data', name + '.ttf'), size)

small_font, font, caption_font = (make_font('Titania-Regular', size) for size in (32, 36, 48))

def seconds(sec):
    return int(sec * MAX_FPS)

######################################################################

class Button(object):
    def __init__(self):
        self.state = False
        self.last_push_time = -1000
    def set(self, state):
        self.state = state
        if state:
            self.last_push_time = pygame.time.get_ticks()
    def __call__(self):
        return self.state

move_up = Button()
move_down = Button()
move_left = Button()
move_right = Button()
fire_up = Button()
fire_down = Button()
fire_left = Button()
fire_right = Button()

keymap = {'move_keys': 'E S D F'}


keymap_alts = [{ pygame.K_e: move_up,
                 pygame.K_d: move_down,
                 pygame.K_s: move_left,
                 pygame.K_f: move_right,
                 pygame.K_i: fire_up,
                 pygame.K_k: fire_down,
                 pygame.K_j: fire_left,
                 pygame.K_l: fire_right,
                 'fire_keys': 'I J K L',
                 'move_keys': 'E S D F' },
               { pygame.K_KP8: move_up,
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
                 'fire_keys': 'R D F G',
                 'move_keys': 'piltangenterna' }]

######################################################################

image_names = ['grass',
               'dark',
               'player',
               'bullet',
               'spark',
               'bigspark',
               'wisp',
               'fairy',
               'machine',
               'pickup',
               'eights',
               'target',
               'bomb']

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

def play_sound(name):
    if SOUND:
        sounds[name].play()

######################################################################

songs = { 'sparrow': "GibIt - Please, Don't Eat The Sparrow",
          'solitude': 'GibIt - Solitude of a Shapeless Outcast',
          'perfect': 'GibIt - "Perfect"' }

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
    def draw(self):
        if self.visible and not self.remove:
            screen.blit(self.image,
                        (self.x - self.x_offset, self.y - self.y_offset),
                        (self.frame_width * self.frame, 0, self.frame_width, self.frame_width))
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

    def initialize(self):
        self.set_image(images['player'])
    def reset(self):
        self.score = 0
        self.machines_remaining = 3
        self.respawn_delay = seconds(2)
        self.invulnerability_delay = 0
        self.fire_delay = 0
        self.bomb_delay = 0
        self.remove = True
        self.continuous_fire = False
    def respawn(self):
        self.machines_remaining -= 1
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.fire_delay = 0
        self.remove = False
        self.invulnerability_delay = seconds(3)
        self.maybe_spawn()
        self.bomb_delay = 0
        self.bomb()
    def hittable(self):
        return self.invulnerability_delay == 0 and not self.remove
    def update(self):
        if self.invulnerability_delay:
            self.invulnerability_delay -= 1
        self.visible = self.invulnerability_delay % 2 == 0
        if self.fire_delay:
            self.fire_delay -= 1
        else:
            self.continuous_fire = False
        if self.bomb_delay:
            self.bomb_delay -= 1
    def bomb(self):
        if self.bomb_delay == 0:
            play_sound('boohm')
            bullet = BombBlast()
            bullet.move(self)
            bullet.owner = self
            bullet.spawn()
            self.bomb_delay = self.BOMB_DELAY

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
    def explode(self):
        play_sound('boom')
        spray = RotatingSpray()
        spray.move(self)
        spray.spawn()
        self.remove = True
        self.respawn_delay = seconds(1)
        if self.machines_remaining == 0:
            stop_music()
            level.game_over = True
    def score_text(self):
        return "%010d" % self.score

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
        self.life = 12 + 1
        self.perish = False
    def update(self):
        self.decrease_life()
        self.frame = 4 - self.life/ 3
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
    def explode(self, bullet):
        self.remove = True
        bullet.owner.score += self.value
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

class RotatingSpray(Sprite):
    SPARK_SPEED = 18
    MAX_LIFE = 9
    def initialize(self):
        self.life = self.MAX_LIFE
        self.visible = False
        self.direction = random.random() * math.pi * 2
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
            self.wave = 0
            self.sprites = players[:]
            self.new_wave()
        else:
            self.pause = not self.pause
            if SOUND:
                if self.pause:
                    pygame.mixer.music.pause()
                else:
                    pygame.mixer.music.unpause()
    def new_wave(self):
        self.wave += 1
        if not self.game_over:
            self.captions = [c for c in self.captions if c.special]
        self.delayed_captions = {}
        self.wave_frames = 0
        if self.wave > 1 and not self.game_over:
            caption = Caption(u"Våg %d" % self.wave)
            caption.center_at(HEIGHT - 200)
            caption.displace_x = WIDTH * [-1, 1][self.wave % 2]
            caption.spawn()

        if self.wave > 0:
            play_sound('blippiblipp')

        if self.wave == -4:
            caption = Caption(u"grt %s" % VERSION)
            caption.center_at(200)
            caption.displace_x = -WIDTH
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
            self.few_enemies = 3
            self.few_enemies_delay = seconds(8.5)
        elif self.wave == 1:
            caption = Caption(u"Nu börjar vi på riktigt!")
            players[0].machines_remaining = 2
            if players[0].remove:
                players[0].machines_remaining += 1
            caption.displace_y = -HEIGHT
            self.delayed_captions[seconds(0.5)] = [caption]
            self.few_enemies = 5
            self.few_enemies_delay = seconds(1.5)
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(17)]
        elif self.wave == 2:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(50)]
        elif self.wave == 3:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(60)]
        elif self.wave == 4:
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(70)]
        elif self.wave == 5:
            self.few_enemies = 0
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(80)]
        elif self.wave > 5:
            self.few_enemies = 100
            self.few_enemies_delay = seconds(3.5)
            self.sprites += [Wisp(ProtoGrunt) for s in xrange(self.wave * 3)]
    def update(self):
        if self.game_over:
            self.game_over_time += 1
            if self.game_over_time == seconds(2.0):
                play_sound('gong')
            if self.game_over_time == seconds(3.5):
                caption = Caption(u"Tryck 1 för att starta om")
                caption.life = seconds(15)
                caption.spawn()
        self.wave_frames += 1
        enemies = [s for s in level.sprites if isinstance(s, Enemy)]

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
    for player in hittable_players:
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


def redraw():
    screen.blit(images['grass'], (0,0))
    for sprite in level.sprites:
        sprite.draw()
    if level.game_over or level.pause:
        screen.blit(images['dark'], (0,0))
    for caption in level.captions:
        caption.draw()
    if players[0].y < HEIGHT - 64 or players[0].remove:
        text = font.render(players[0].score_text(), True, (0,0,0))
        y = HEIGHT - text.get_height() - 2
        screen.blit(text, (2, y + 2))
        text = font.render(players[0].score_text(), True, (255,255,255))
        screen.blit(text, (0, y))
        x = text.get_width() + 8
        for i in xrange(players[0].machines_remaining):
            screen.blit(images['machine'], (x + i*34, HEIGHT - 40))
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
            elif event.key in [pygame.K_1, pygame.K_p]:
                level.restart_or_pause()
            elif len(keymap) <= 1:
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

    clock.tick(MAX_FPS)
