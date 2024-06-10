from settings import *
from sprites import *
from groups import AllSprites
from support import *
from timer import Timer
from random import randint
from button import Button

class Game:
	def __init__(self):
		pygame.init()
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		pygame.display.set_caption('Platformer')
		self.clock = pygame.time.Clock()
		self.running = True
		self.score = 0

		self.menu()

	def get_font(self, size):
		return import_font(size, "data", "graphics", "font")

	def menu(self):
		menu_text_font = self.get_font(45)
		menu_info_font = pygame.font.SysFont("Comic Sans", 26)
		play_image = import_image("images", "button", "play_rect")

		while self.running:
			dt = self.clock.tick(FRAMERATE) / 1000

			self.display_surface.fill(MENU_BG_COLOR)

			menu_mouse_pos = pygame.mouse.get_pos()
			
			menu_text = menu_text_font.render("Platformer", True, "#EE8B7E")
			menu_rect = menu_text.get_rect(center=(640, 100))

			menu_info_text = menu_info_font.render("Daniel Lobo T3T2", True, "#EE8B7E")
			menu_info_rect = menu_text.get_rect(center=(WINDOW_WIDTH - 80, WINDOW_HEIGHT - 50))

			play_button = Button(image=play_image, pos=(640, 300),
									text_input="Jugar", font=menu_text_font, base_color="#d7fcd4", hovering_color="White")
			quit_button = Button(image=play_image, pos=(640, 450),
									text_input="Salir", font=menu_text_font, base_color="#d7fcd4", hovering_color="White")

			self.display_surface.blit(menu_text, menu_rect)
			self.display_surface.blit(menu_info_text, menu_info_rect)

			for button in [play_button, quit_button]:
				button.changeColor(menu_mouse_pos)
				button.update(self.display_surface)

			# draw
			pygame.display.update()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
				if event.type == pygame.MOUSEBUTTONDOWN:
					if play_button.checkForInput(menu_mouse_pos):
						self.load_game()
						self.run()
						break
					elif quit_button.checkForInput(menu_mouse_pos):
						self.running = False

		pygame.quit()

	def game_over(self):
		pygame.mouse.set_visible(True)
		menu_text_font = self.get_font(45)
		play_image = import_image("images", "button", "play_rect")
		reload_game = False

		while self.running:
			dt = self.clock.tick(FRAMERATE) / 1000

			# self.display_surface.fill(MENU_BG_COLOR)

			menu_mouse_pos = pygame.mouse.get_pos()
			
			menu_text = menu_text_font.render("Game Over", True, "#EE8B7E")
			menu_rect = menu_text.get_rect(center=(640, 100))

			play_button = Button(image=play_image, pos=(640, 300),
						text_input="Otra vez", font=menu_text_font, base_color="#d7fcd4", hovering_color="White")
			quit_button = Button(image=play_image, pos=(640, 450),
									text_input="Salir", font=menu_text_font, base_color="#d7fcd4", hovering_color="White")

			self.display_surface.blit(menu_text, menu_rect)

			for button in [play_button, quit_button]:
				button.changeColor(menu_mouse_pos)
				button.update(self.display_surface)

			# draw
			pygame.display.update()

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False
				if event.type == pygame.MOUSEBUTTONDOWN:
					if play_button.checkForInput(menu_mouse_pos):
						reload_game = True
						break
					if quit_button.checkForInput(menu_mouse_pos):
						self.running = False

			if reload_game:
				self.reload_game()
				break

	def load_game(self):
		# groups
		self.all_sprites = AllSprites()
		self.collision_sprites = pygame.sprite.Group()
		self.bullet_sprites = pygame.sprite.Group()
		self.enemy_sprites = pygame.sprite.Group()

		# load game
		self.load_assets()
		self.setup()

		# Timers
		self.bee_timer = Timer(500, func=self.create_bee, autostart=True, repeat=True)

	def reload_game(self):
		for sprite in self.enemy_sprites:
			if isinstance(sprite, Enemy):
				sprite.kill()
				sprite.destroy()
				del sprite
		self.player.kill()
		del self.player
		self.gun.kill()
		del self.gun

		self.score = 0

		self.spawn_entities()

	def create_bee(self):
		Bee(frames=self.bee_frames,
	  		pos=(self.level_width + WINDOW_WIDTH, randint(0,self.level_height)),
			groups=(self.all_sprites, self.enemy_sprites),
			speed=randint(300,500))

	def create_bullet(self, pos, direction):
		if direction == 1:
			x = pos[0] + direction.x * 34
		else:
			x = pos[0] + direction.x * 16 - self.bullet_surf.get_width()
		Bullet(self.bullet_surf, (x, pos[1]), direction, (self.all_sprites, self.bullet_sprites))
		Fire(self.fire_surf, self.gun.rect.midright, direction, self.all_sprites, self.player)
		self.audio["shoot"].play()

	def load_assets(self):
		# Graficos
		self.player_frames = import_folder("images", "player")
		self.gun_surf = import_image("images", "gun", "gun")
		self.bullet_surf = import_image("images", "gun", "bullet")
		self.crosshair_surf = import_image("images", "gun", "crosshair")
		self.fire_surf = import_image("images", "gun", "fire")
		self.bee_frames = import_folder("images", "enemies", "bee")
		self.worm_frames = import_folder("images", "enemies", "worm")
	
		# Sonidos
		self.audio = audio_importer("audio")

	def setup(self):
		self.tmx_map = load_pygame(join("data", "maps", "world.tmx"))
		self.level_width = self.tmx_map.width * TILE_SIZE
		self.level_height = self.tmx_map.height * TILE_SIZE

		for x, y, image in self.tmx_map.get_layer_by_name("Main").tiles():
			Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites, self.collision_sprites))

		for x, y, image in self.tmx_map.get_layer_by_name("Decoration").tiles():
			Sprite((x * TILE_SIZE, y * TILE_SIZE), image, (self.all_sprites))

		self.spawn_entities()
		self.audio["music"].play(loops = -1)

		self.score_font = pygame.font.SysFont("monospace", 28)

		self.crosshair = Crosshair(self.crosshair_surf, self.player, self.all_sprites)
		pygame.mouse.set_visible(False)

	
	def spawn_entities(self):
		for obj in self.tmx_map.get_layer_by_name("Entities"):
			if obj.name == "Player":
				self.player = Player((obj.x, obj.y), self.all_sprites, self.collision_sprites, self.player_frames, self.create_bullet)
				self.gun = Gun(self.gun_surf, self.player, self.all_sprites)

			if obj.name == "Worm":
				Worm(self.worm_frames, pygame.FRect(obj.x, obj.y, obj.width, obj.height), (self.all_sprites, self.enemy_sprites))


	def collision(self):
		# Balas y enemigos
		for bullet in self.bullet_sprites:
			sprite_collision = pygame.sprite.spritecollide(bullet, self.enemy_sprites, False, pygame.sprite.collide_mask)
			if sprite_collision:
				self.audio["impact"].play()
				bullet.kill()
				self.score += 100
				for sprite in sprite_collision:
					sprite.destroy()

		# Enemigos y player
		if pygame.sprite.spritecollide(self.player, self.enemy_sprites, False, pygame.sprite.collide_mask):
			self.audio["shoot"].play()
			self.game_over()
			# self.running = False

		# Caer
		if self.player.rect.top > self.level_height + 800:
			self.audio["shoot"].play()
			self.game_over()

	def run(self):
		while self.running:
			dt = self.clock.tick(FRAMERATE) / 1000

			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.running = False

			# update
			self.bee_timer.update()
			self.all_sprites.update(dt)
			self.collision()

			# draw
			self.display_surface.fill(BG_COLOR)
			self.all_sprites.draw(self.player.rect.center)
			pygame.draw.rect(self.display_surface, "Lightblue", pygame.Rect(5,10,200,30))
			score_text = self.score_font.render("Score: " + str(self.score), 1, (0,0,0))
			self.display_surface.blit(score_text, (10,10))
			pygame.display.update()

		pygame.quit()

if __name__ == '__main__':
	game = Game()
	game.run()
