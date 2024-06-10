from typing import Any
from settings import *
from timer import Timer
from math import sin, atan2, degrees
from random import randint

class Sprite(pygame.sprite.Sprite):
	def __init__(self, pos, surf, groups):
		super().__init__(groups)
		self.image = surf
		self.rect = self.image.get_frect(topleft = pos)

class Fire(Sprite):
	def __init__(self, surf, pos, direction, groups, player):
		super().__init__(pos, surf, groups)
		self.player = player
		self.timer = Timer(100, autostart=True, func=self.kill)
		self.y_offset = pygame.Vector2(0,10)
		self.direction = direction

	def rotate_fire(self):
		angle = degrees(atan2(self.direction.x, self.direction.y)) - 90
		self.image = pygame.transform.rotozoom(self.image, angle, 1)

	def update(self, _):
		self.timer.update()

		self.rotate_fire()

class AnimatedSprite(Sprite):
	def __init__(self, frames, pos, groups):
		self.frames, self.frame_index, self.animation_speed = frames, 0, 10
		super().__init__(pos, self.frames[self.frame_index], groups)

	def animate(self, dt):
		self.frame_index += self.animation_speed * dt
		self.image = self.frames[int(self.frame_index) % len(self.frames)]

class Player(AnimatedSprite):
	def __init__(self, pos, groups, collision_sprites, frames, create_bullet):
		super().__init__(frames, pos, groups)
		self.flip = False
		self.create_bullet = create_bullet

		# Movimiento y colisiones
		self.direction = pygame.Vector2()
		self.collision_sprites = collision_sprites
		self.speed = 400
		self.gravity = 50
		self.on_floor = False
		self.jump_count = 0

		# Para la direccion de las balas
		self.player_direction = pygame.Vector2(1,0)

		# Timer
		self.shoot_timer = Timer(500)

	def input(self):
		keys = pygame.key.get_pressed()
		keys_jump = pygame.key.get_just_pressed()
		self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
		if keys_jump[pygame.K_SPACE]:
			if self.on_floor:
				self.direction.y = -20
			elif self.jump_count > 0:
				self.direction.y = -15
				self.jump_count -= 1

		if pygame.mouse.get_pressed()[0] and not self.shoot_timer:
			self.get_direction()

			self.create_bullet(self.rect.center, self.player_direction)
			self.shoot_timer.activate()

	def get_direction(self):
		mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
		player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
		self.player_direction = (mouse_pos - player_pos).normalize()

	def move(self, dt):
		# Movimiento horizontal
		self.rect.x += self.direction.x * self.speed * dt
		self.collision("horizontal")

		# Movimiento vertical
		self.direction.y += self.gravity * dt
		self.rect.y += self.direction.y
		self.collision("vertical")

	def collision(self, direction):
		for sprite in self.collision_sprites:
			if sprite.rect.colliderect(self.rect):
				if direction == "horizontal":
					if self.direction.x > 0:
						self.rect.right = sprite.rect.left
					if self.direction.x < 0:
						self.rect.left = sprite.rect.right
				if direction == "vertical":
					if self.direction.y > 0:
						self.rect.bottom = sprite.rect.top
					if self.direction.y < 0:
						self.rect.top = sprite.rect.bottom
					self.direction.y = 0

	def check_floor(self):
		bottom_rect = pygame.FRect((0,0), (self.rect.width, 2)).move_to(midtop = self.rect.midbottom)
		if bottom_rect.collidelist([sprite.rect for sprite in self.collision_sprites]) >= 0:
			self.on_floor = True
			self.jump_count = 1
		else:
			self.on_floor = False

	def animate(self, dt):
		if self.direction.x:
			self.frame_index += self.animation_speed * dt
			self.flip = self.direction.x < 0
		else:
			self.frame_index = 0

		if not self.on_floor:
			self.frame_index = 1

		self.image = self.frames[int(self.frame_index) % len(self.frames)]
		self.image = pygame.transform.flip(self.image, self.flip, False)

	def update(self, dt):
		self.shoot_timer.update()
		self.check_floor()
		self.input()
		self.move(dt)
		self.animate(dt)

class Gun(Sprite):
	def __init__(self, surf, player, groups):
		super().__init__(player.rect.center, surf, groups)
		# Conexion al jugador
		self.player = player
		self.flip = player.flip
		self.player_direction = pygame.Vector2(1,0)
		self.offset = pygame.Vector2(4,14)

		# sprite
		self.gun_surf = surf

	def get_direction(self):
		mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
		player_pos = pygame.Vector2(WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2)
		self.player_direction = (mouse_pos - player_pos).normalize()

	def rotate_gun(self):
		angle = degrees(atan2(self.player_direction.x, self.player_direction.y)) - 90
		if self.player_direction.x > 0:
			self.image = pygame.transform.rotozoom(self.gun_surf, angle, 1)
		else:
			self.image = pygame.transform.rotozoom(self.gun_surf, abs(angle), 1)
			self.image = pygame.transform.flip(self.image, False, True)

	def update(self, _):
		self.get_direction()
		self.rotate_gun()

		if self.flip != self.player.flip:
			self.offset.x *= -1
			self.image = pygame.transform.flip(self.image, True, False)
			self.flip = self.player.flip

		self.rect.center = self.player.rect.center + self.offset

class Bullet(Sprite):
	def __init__(self, surf, pos, direction, groups):
		super().__init__(pos, surf, groups)

		# Flipear la imagen
		self.image = pygame.transform.flip(self.image, direction == -1, False)

		# Movimiento
		self.direction = direction
		self.speed = 850
		self.rotate_bullet()

	def rotate_bullet(self):
		angle = degrees(atan2(self.direction.x, self.direction.y)) - 90
		self.image = pygame.transform.rotozoom(self.image, angle, 1)

	def update(self, dt):
		self.rect.x += self.direction.x * self.speed * dt
		self.rect.y += self.direction.y * self.speed * dt

class Crosshair(Sprite):
	def __init__(self, surf, player, groups):
		super().__init__((0,0), surf, groups)
		# Conexion al jugador
		self.player = player

		# sprite
		self.surf = surf

	def update(self, _):
		mouse_pos = pygame.mouse.get_pos()

		self.rect.center = (mouse_pos[0] + (self.player.rect.center[0] - WINDOW_WIDTH / 2), 
					  		mouse_pos[1] + (self.player.rect.center[1] - WINDOW_HEIGHT / 2))

class Enemy(AnimatedSprite):
	def __init__(self, frames, pos, groups):
		super().__init__(frames, pos, groups)
		self.death_timer = Timer(200, func=self.kill)
	
	def destroy(self):
		self.death_timer.activate()
		self.animation_speed = 0
		self.image = pygame.mask.from_surface(self.image).to_surface()
		self.image.set_colorkey("black")

	def update(self, dt):
		self.death_timer.update()
		if not self.death_timer:
			self.move(dt)
			self.animate(dt)
		self.constraint()

class Bee(Enemy):
	def __init__(self, frames, pos, groups, speed):
		super().__init__(frames, pos, groups)
		self.flip = False
		self.speed = speed
		self.amplitude = randint(500, 600)
		self.frequency = randint(300, 600)

	def move(self, dt):
		self.rect.x -= self.speed * dt
		self.rect.y += sin(pygame.time.get_ticks() / self.frequency) * self.amplitude * dt
	
	def constraint(self):
		if self.rect.right <= 0:
			self.kill()

class Worm(Enemy):
	def __init__(self, frames, rect, groups):
		super().__init__(frames, rect.topleft, groups)
		self.rect.bottomleft = rect.bottomleft
		self.main_rect = rect
		self.speed = randint(160, 200)
		self.direction = 1

	def move(self, dt):
		self.rect.x += self.direction * self.speed * dt

	def constraint(self):
		if not self.main_rect.contains(self.rect):
			self.direction *= -1
			self.frames = [pygame.transform.flip(surf, True, False) for surf in self.frames]
