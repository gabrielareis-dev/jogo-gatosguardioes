"""Gatos Guardiões - um pequeno jogo 2D de tiro feito em Pygame.

Controles: WASD/setas para mover, mouse para mirar, clique ou espaço para atirar.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
import pygame


# Tamanho lógico do jogo; a tela pode ser redimensionada sem mudar as coordenadas internas.
WIDTH, HEIGHT = 1000, 640
FPS = 60
# Cada valor é a pontuação necessária para concluir uma fase.
LEVEL_GOALS = (500, 1000, 1500, 2000, 2500)
CAT_RADIUS = 28
PLAYING, MENU, WON, LOST = "playing", "menu", "won", "lost"

COLORS = {
    "ink": (28, 35, 56), "night": (26, 38, 67), "sky": (55, 73, 111),
    "cream": (255, 243, 218), "gold": (255, 198, 89), "pink": (249, 145, 165),
    "mint": (126, 218, 190), "lilac": (185, 168, 244), "white": (255, 255, 255),
}


def asset_path(*parts):
    """Localiza os assets ao executar o script ou o executável portátil."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).resolve().parent
    else:
        base = Path(__file__).resolve().parent
    return base.joinpath(*parts)


def load_background(name):
    image = pygame.image.load(str(asset_path("assets", "backgrounds", name))).convert()
    scale = max(WIDTH / image.get_width(), HEIGHT / image.get_height())
    size = (round(image.get_width() * scale), round(image.get_height() * scale))
    image = pygame.transform.smoothscale(image, size)
    crop = pygame.Rect(0, 0, WIDTH, HEIGHT)
    crop.center = image.get_rect().center
    return image.subsurface(crop).copy()


def rounded_text(surface, font, text, color, center, shadow=(0, 0, 0), offset=2):
    if shadow:
        shade = font.render(text, True, shadow)
        surface.blit(shade, shade.get_rect(center=(center[0], center[1] + offset)))
    label = font.render(text, True, color)
    surface.blit(label, label.get_rect(center=center))


class Button:
    def __init__(self, rect, label, color):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.color = color

    def draw(self, surface, font, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        rect = self.rect.copy()
        if hovered:
            rect.y -= 2
        pygame.draw.rect(surface, (12, 19, 37), self.rect.move(0, 5), border_radius=18)
        face = tuple(min(255, channel + (20 if hovered else 0)) for channel in self.color)
        pygame.draw.rect(surface, face, rect, border_radius=18)
        pygame.draw.rect(surface, (255, 255, 255, 90), rect, width=2, border_radius=18)
        label = font.render(self.label, True, COLORS["ink"])
        surface.blit(label, label.get_rect(center=rect.center))


class Cat:
    def __init__(self, sprite):
        self.sprite = pygame.transform.smoothscale(sprite, (120, 96))
        self.pos = pygame.Vector2(175, HEIGHT - 125)
        self.speed = 300
        self.cooldown = 0
        self.invulnerable = 0
        self.wave = 1
        self.max_health = 3
        self.health = self.max_health

    def upgrade(self, wave):
        if wave <= self.wave:
            return
        extra_health = wave - self.wave
        self.wave = wave
        self.max_health = 3 + (wave - 1)
        self.health = min(self.max_health, self.health + extra_health)

    def take_damage(self):
        if self.invulnerable > 0:
            return False
        self.health = max(0, self.health - 1)
        self.invulnerable = 1.0
        return True

    def update(self, dt, keys):
        direction = pygame.Vector2(
            float(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - float(keys[pygame.K_a] or keys[pygame.K_LEFT]),
            float(keys[pygame.K_s] or keys[pygame.K_DOWN]) - float(keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if direction.length_squared():
            self.pos += direction.normalize() * self.speed * dt
        self.pos.x = max(58, min(WIDTH - 58, self.pos.x))
        self.pos.y = max(112, min(HEIGHT - 60, self.pos.y))
        self.cooldown = max(0, self.cooldown - dt)
        self.invulnerable = max(0, self.invulnerable - dt)

    def draw(self, surface, aim):
        direction = pygame.Vector2(aim) - self.pos
        if not direction.length_squared():
            direction = pygame.Vector2(1, 0)
        angle = math.degrees(math.atan2(-direction.y, direction.x))
        sprite = pygame.transform.rotate(self.sprite, angle)
        sprite_rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        flickering = self.invulnerable and int(self.invulnerable * 12) % 2
        if not flickering:
            surface.blit(sprite, sprite_rect)

        bar_width, bar_height = 72, 7
        bar_x = round(self.pos.x) - bar_width // 2
        bar_y = sprite_rect.top - 14
        ratio = self.health / self.max_health
        fill_color = (111, 220, 150) if ratio > .6 else (255, 183, 86) if ratio > .3 else (239, 83, 91)
        pygame.draw.rect(surface, (22, 19, 28), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), border_radius=3)
        pygame.draw.rect(surface, fill_color, (bar_x, bar_y, round(bar_width * ratio), bar_height), border_radius=3)

    def muzzle_position(self, aim):
        direction = pygame.Vector2(aim) - self.pos
        if not direction.length_squared():
            direction = pygame.Vector2(1, 0)
        return self.pos + direction.normalize() * 52


class Rat:
    def __init__(self, wave, sprites, giant=False):
        start_y = HEIGHT - 145 + random.randint(-18, 18) if giant else random.randint(140, HEIGHT - 75)
        self.pos = pygame.Vector2(WIDTH + 60, start_y)
        self.phase = random.random() * math.tau
        self.wave = min(max(1, wave), 5)
        self.giant = giant
        source_sprite = sprites[self.wave]
        width = (142 + (self.wave - 1) * 5) if giant else (100 + (self.wave - 1) * 4)
        height = round(width * source_sprite.get_height() / source_sprite.get_width())
        self.sprite = pygame.transform.smoothscale(source_sprite, (width, height))
        common_speeds = {
            1: (70, 95), 2: (85, 110), 3: (100, 125),
            4: (115, 140), 5: (130, 155),
        }
        giant_speeds = {
            1: (45, 60), 2: (50, 65), 3: (55, 70),
            4: (60, 75), 5: (65, 80),
        }
        common_health = {1: 1, 2: 2, 3: 5, 4: 8, 5: 12}
        speed_range = giant_speeds[self.wave] if giant else common_speeds[self.wave]
        self.speed = random.uniform(*speed_range)
        self.max_health = common_health[self.wave] + (2 if giant else 0)
        self.health = self.max_health
        self.radius = (38 + self.wave) if giant else (27 + self.wave)
        self.points = 250 if giant else 100

    def update(self, dt, elapsed, target_pos):
        direction = pygame.Vector2(target_pos) - self.pos
        if direction.length_squared():
            self.pos += direction.normalize() * self.speed * dt
        bob = 4 if self.giant else 10
        self.pos.y += math.sin(elapsed * 4.0 + self.phase) * bob * dt

    def draw(self, surface, elapsed, wave=None, target_pos=None):
        sprite = self.sprite
        if target_pos is not None and target_pos.x > self.pos.x:
            sprite = pygame.transform.flip(sprite, True, False)
        sprite_rect = sprite.get_rect(center=(round(self.pos.x), round(self.pos.y)))
        surface.blit(sprite, sprite_rect)

        bar_width, bar_height = (62 if self.giant else 48), 6
        bar_x = round(self.pos.x) - bar_width // 2
        bar_y = sprite_rect.top - bar_height - 5
        ratio = self.health / self.max_health
        fill_color = (111, 220, 150) if ratio > .6 else (255, 183, 86) if ratio > .3 else (239, 83, 91)
        pygame.draw.rect(surface, (22, 19, 28), (bar_x - 1, bar_y - 1, bar_width + 2, bar_height + 2), border_radius=3)
        pygame.draw.rect(surface, fill_color, (bar_x, bar_y, round(bar_width * ratio), bar_height), border_radius=3)


class Yarn:
    def __init__(self, start, destination, damage, sprite):
        self.pos = pygame.Vector2(start)
        direction = pygame.Vector2(destination) - self.pos
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        self.velocity = direction.normalize() * 650
        self.life = 1.2
        self.damage = damage
        self.sprite = pygame.transform.smoothscale(sprite, (26, 26))
        self.angle = random.random() * 360

    def update(self, dt):
        self.pos += self.velocity * dt
        self.life -= dt
        self.angle = (self.angle + 540 * dt) % 360

    def draw(self, surface, elapsed):
        sprite = pygame.transform.rotate(self.sprite, self.angle)
        surface.blit(sprite, sprite.get_rect(center=(round(self.pos.x), round(self.pos.y))))


class Game:
    def __init__(self):
        pygame.init()
        self.sounds = {}
        self.music_level = None
        # Se o dispositivo de áudio não estiver disponível, o jogo continua sem som.
        try:
            pygame.mixer.init()
        except (pygame.error, OSError):
            pass
        if pygame.mixer.get_init():
            for name in ("shoot", "hit", "lose", "win"):
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(asset_path("assets", "sounds", f"{name}.wav")))
                except (pygame.error, OSError):
                    # Um arquivo de áudio ausente não desativa os demais.
                    continue
            if "shoot" in self.sounds:
                self.sounds["shoot"].set_volume(0.35)
        self.music_ready = pygame.mixer.get_init() is not None
        pygame.display.set_caption("Gatos Guardiões | Miaus contra Morce-ratos")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        self.canvas = pygame.Surface((WIDTH, HEIGHT))
        street_background = load_background("game_background.jpg")
        self.backgrounds = {wave: street_background for wave in range(1, 6)}
        self.cat_sprite = pygame.image.load(str(asset_path("assets", "sprites", "cat_guardian.png"))).convert_alpha()
        self.rat_sprites = {
            1: pygame.image.load(str(asset_path("assets", "sprites", "morce_rat_level1.png"))).convert_alpha(),
            2: pygame.image.load(str(asset_path("assets", "sprites", "morce_rat_level2.png"))).convert_alpha(),
            3: pygame.image.load(str(asset_path("assets", "sprites", "morce_rat_level3.png"))).convert_alpha(),
            4: pygame.image.load(str(asset_path("assets", "sprites", "morce_rat_level45.png"))).convert_alpha(),
            5: pygame.image.load(str(asset_path("assets", "sprites", "morce_rat_level45.png"))).convert_alpha(),
        }
        self.yarn_sprite = pygame.image.load(str(asset_path("assets", "sprites", "yarn_red.png"))).convert_alpha()
        self.hud_cat_portrait = pygame.transform.smoothscale(self.cat_sprite, (72, 58))
        self.hud_yarn_icon = pygame.transform.smoothscale(self.yarn_sprite, (18, 18))
        self.clock = pygame.time.Clock()
        self.font_small = pygame.font.Font(None, 24)
        self.font_hud = pygame.font.Font(None, 20)
        self.font = pygame.font.Font(None, 30)
        self.font_big = pygame.font.Font(None, 64)
        self.font_title = pygame.font.Font(None, 76)
        self.state = MENU
        self.paused = False
        self.stars = [(random.randrange(WIDTH), random.randrange(30, HEIGHT - 170), random.choice((1, 1, 2))) for _ in range(90)]
        self.start_button = Button((WIDTH // 2 - 135, 420, 270, 62), "COMEÇAR A JOGAR", COLORS["gold"])
        self.reset()
        self.state = MENU
        self.sync_music()

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def sync_music(self):
        # Só recarrega a música quando a pontuação muda a fase atual.
        if not self.music_ready:
            return
        level = min(self.wave, len(LEVEL_GOALS))
        if self.music_level != level:
            try:
                pygame.mixer.music.load(str(asset_path("assets", "music", f"level{level}.wav")))
                pygame.mixer.music.set_volume(0.65)
                pygame.mixer.music.play(-1)
                self.music_level = level
            except (pygame.error, OSError):
                self.music_ready = False

    def reset(self):
        # Prepara uma partida nova, zerando pontuação, inimigos e projéteis.
        self.cat = Cat(self.cat_sprite)
        self.rats = []
        self.yarn = []
        self.score = 0
        self.elapsed = 0
        self.spawn_timer = .8
        self.wave = 1
        # Força o carregamento da faixa da fase 1 ao iniciar ou reiniciar.
        self.music_level = None
        self.level_message_timer = 0
        self.state = PLAYING
        self.paused = False
        self.start_button.rect = pygame.Rect(WIDTH // 2 - 135, 420, 270, 62)
        self.start_button.label = "COMEÇAR A JOGAR"

    def draw_background(self):
        background = self.backgrounds[1 if self.wave <= 2 else 3]
        self.canvas.blit(background, (0, 0))

    def aim_position(self):
        # Converte o mouse da janela redimensionável para as coordenadas do canvas lógico.
        pos = pygame.mouse.get_pos()
        sw, sh = self.screen.get_size()
        return (pos[0] * WIDTH / max(1, sw), pos[1] * HEIGHT / max(1, sh))

    def fire(self):
        # O intervalo impede que um clique ou tecla gere disparos contínuos muito rápidos.
        if self.cat.cooldown <= 0 and self.state == PLAYING:
            aim = self.aim_position()
            self.yarn.append(Yarn(self.cat.muzzle_position(aim), aim, self.wave, self.yarn_sprite))
            self.cat.cooldown = .22
            self.play_sound("shoot")

    def set_wave(self, wave):
        if wave == self.wave:
            return
        self.wave = wave
        self.cat.upgrade(wave)
        self.level_message_timer = 3.5
        self.sync_music()

    def update(self, dt):
        if self.state != PLAYING:
            return
        # dt representa o tempo do quadro, mantendo movimento e animações consistentes.
        self.elapsed += dt
        self.level_message_timer = max(0, self.level_message_timer - dt)
        keys = pygame.key.get_pressed()
        self.cat.update(dt, keys)
        # Cada 500 pontos avança uma fase, até a meta final de vitória.
        self.set_wave(min(1 + self.score // 500, len(LEVEL_GOALS)))
        self.sync_music()
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            giant_chance = .13 + (self.wave - 1) * .035
            self.rats.append(Rat(self.wave, self.rat_sprites, giant=random.random() < giant_chance))
            # As primeiras fases dão tempo para aprender; depois os inimigos chegam mais rápido.
            spawn_intervals = {1: 1.45, 2: 1.30, 3: 1.15, 4: 1.0, 5: .85}
            self.spawn_timer = spawn_intervals[self.wave] * random.uniform(.9, 1.1)
        for rat in self.rats:
            rat.update(dt, self.elapsed, self.cat.pos)
            if rat.pos.distance_to(self.cat.pos) < CAT_RADIUS + rat.radius - 5:
                if self.cat.take_damage() and self.cat.health <= 0:
                    self.state = LOST
                    self.play_sound("lose")
                    if self.music_ready:
                        pygame.mixer.music.stop()
                    break
        if self.state != PLAYING:
            return
        for ball in self.yarn:
            ball.update(dt)
        for ball in self.yarn[:]:
            hit = next((rat for rat in self.rats if ball.pos.distance_to(rat.pos) < rat.radius + 10), None)
            if hit:
                self.yarn.remove(ball)
                hit.health = max(0, hit.health - ball.damage)
                self.play_sound("hit")
                if hit.health <= 0:
                    self.rats.remove(hit)
                    self.score += hit.points
                    # Atualiza imediatamente a fase e a trilha ao cruzar uma meta.
                    new_wave = min(1 + self.score // 500, len(LEVEL_GOALS))
                    if new_wave != self.wave:
                        self.set_wave(new_wave)
                    if self.score >= LEVEL_GOALS[-1]:
                        # A última meta encerra a partida com vitória.
                        self.state = WON
                        self.play_sound("win")
                        if self.music_ready:
                            pygame.mixer.music.stop()
            elif ball.life <= 0 or not (-30 < ball.pos.x < WIDTH + 30 and -30 < ball.pos.y < HEIGHT + 30):
                self.yarn.remove(ball)

    def draw_hud(self):
        # Três cartões separam status do gato, pontuação e progresso da fase.
        cards = (
            (pygame.Rect(18, 14, 300, 86), (249, 145, 165)),
            (pygame.Rect(328, 14, 210, 86), COLORS["gold"]),
            (pygame.Rect(548, 14, 434, 86), COLORS["mint"]),
        )
        for rect, accent in cards:
            pygame.draw.rect(self.canvas, (8, 12, 27), rect.move(0, 4), border_radius=16)
            pygame.draw.rect(self.canvas, (20, 29, 51), rect, border_radius=16)
            pygame.draw.rect(self.canvas, (74, 91, 126), rect, width=2, border_radius=16)
            pygame.draw.line(self.canvas, accent, (rect.x + 15, rect.y + 2),
                             (rect.right - 15, rect.y + 2), 3)

        # Retrato do protagonista e barra de vida.
        portrait_frame = pygame.Rect(28, 23, 74, 68)
        pygame.draw.rect(self.canvas, (38, 48, 74), portrait_frame, border_radius=13)
        portrait_rect = self.hud_cat_portrait.get_rect(center=portrait_frame.center)
        self.canvas.blit(self.hud_cat_portrait, portrait_rect)
        pygame.draw.rect(self.canvas, (132, 151, 191), portrait_frame, width=2, border_radius=13)
        self.canvas.blit(self.font_hud.render("GATO GUARDIÃO", True, COLORS["cream"]), (112, 23))
        health_text = f"VIDA {self.cat.health}/{self.cat.max_health}"
        health_color = (255, 148, 157) if self.cat.health <= 2 else COLORS["white"]
        self.canvas.blit(self.font_hud.render(health_text, True, health_color), (112, 47))
        health_bar = pygame.Rect(112, 73, 188, 9)
        pygame.draw.rect(self.canvas, (49, 57, 81), health_bar, border_radius=5)
        health_fill = health_bar.copy()
        health_fill.width = round(health_bar.width * self.cat.health / self.cat.max_health)
        if health_fill.width:
            bar_color = (244, 93, 112) if self.cat.health <= 2 else (126, 218, 190)
            pygame.draw.rect(self.canvas, bar_color, health_fill, border_radius=5)

        # Pontuação, fase atual e dano das bolas de lã.
        self.canvas.blit(self.font_hud.render("PONTOS", True, (184, 196, 220)), (344, 23))
        self.canvas.blit(self.font.render(f"{self.score:04d}", True, COLORS["gold"]), (344, 44))
        phase_badge = pygame.Rect(454, 22, 72, 25)
        pygame.draw.rect(self.canvas, (76, 65, 83), phase_badge, border_radius=9)
        phase_text = self.font_hud.render(f"FASE {self.wave}", True, COLORS["white"])
        self.canvas.blit(phase_text, phase_text.get_rect(center=phase_badge.center))
        self.canvas.blit(self.hud_yarn_icon, (452, 58))
        self.canvas.blit(self.font_hud.render(f"DANO x{self.wave}", True, COLORS["pink"]), (473, 58))

        # Progresso até a meta da fase atual.
        goal = LEVEL_GOALS[self.wave - 1]
        previous_goal = LEVEL_GOALS[self.wave - 2] if self.wave > 1 else 0
        required = max(1, goal - previous_goal)
        progress = max(0, min(1, (self.score - previous_goal) / required))
        self.canvas.blit(self.font_hud.render(f"PROGRESSO DA FASE {self.wave}", True, COLORS["cream"]), (568, 22))
        goal_text = self.font_hud.render(f"META {goal} PONTOS", True, (216, 221, 238))
        self.canvas.blit(goal_text, (962 - goal_text.get_width(), 22))
        progress_bar = pygame.Rect(568, 50, 394, 10)
        pygame.draw.rect(self.canvas, (49, 57, 81), progress_bar, border_radius=5)
        progress_fill = progress_bar.copy()
        progress_fill.width = round(progress_bar.width * progress)
        if progress_fill.width:
            pygame.draw.rect(self.canvas, COLORS["mint"], progress_fill, border_radius=5)
        self.canvas.blit(self.font_hud.render(f"{self.score - previous_goal} / {required} PONTOS", True,
                                               (190, 201, 222)), (568, 69))
        percent = self.font_hud.render(f"{round(progress * 100)}%", True, COLORS["mint"])
        self.canvas.blit(percent, (962 - percent.get_width(), 69))

    def draw_menu(self, mouse):
        # O menu mostra os controles antes da partida começar.
        self.draw_background()
        # Cartão do menu
        card = pygame.Rect(WIDTH // 2 - 255, 120, 510, 420)
        pygame.draw.rect(self.canvas, (22, 31, 56), card.move(0, 8), border_radius=28)
        pygame.draw.rect(self.canvas, (39, 51, 81), card, border_radius=28)
        pygame.draw.rect(self.canvas, (100, 117, 157), card, width=2, border_radius=28)
        rounded_text(self.canvas, self.font_title, "MIAUS CONTRA", COLORS["cream"], (WIDTH // 2, 190), COLORS["ink"])
        rounded_text(self.canvas, self.font_title, "MORCE-RATOS", COLORS["gold"], (WIDTH // 2, 252), COLORS["ink"])
        rounded_text(self.canvas, self.font, "Defenda a vizinhança com bolas de lã!", COLORS["white"], (WIDTH // 2, 306), None)
        rounded_text(self.canvas, self.font_small, "WASD / SETAS: mover  •  MOUSE: mirar", (210, 222, 242), (WIDTH // 2, 354), None)
        rounded_text(self.canvas, self.font_small, "CLIQUE / ESPAÇO: atirar", (210, 222, 242), (WIDTH // 2, 379), None)
        rounded_text(self.canvas, self.font_small, "Metas: 500, 1.000, 1.500, 2.000 e 2.500 pontos", (210, 222, 242), (WIDTH // 2, 404), None)
        self.start_button.label = "CONTINUAR JOGANDO" if self.paused else "COMEÇAR A JOGAR"
        self.start_button.rect = pygame.Rect(WIDTH // 2 - 135, 420, 270, 62)
        self.start_button.draw(self.canvas, self.font, mouse)
        rounded_text(self.canvas, self.font_small, "Derrota quando a vida do gato chega a zero.", (193, 198, 218), (WIDTH // 2, 507), None)
        self.present()

    def draw_end(self, mouse):
        self.draw_background()
        self.draw_hud()
        self.cat.draw(self.canvas, self.aim_position())
        for rat in self.rats:
            rat.draw(self.canvas, self.elapsed, self.wave, self.cat.pos)
        title = "VITÓRIA!" if self.state == WON else "FIM DE JOGO"
        subtitle = "A vizinhança está a salvo!" if self.state == WON else "A vida do gato acabou!"
        color = COLORS["mint"] if self.state == WON else COLORS["pink"]
        panel = pygame.Rect(WIDTH // 2 - 220, HEIGHT // 2 - 120, 440, 255)
        pygame.draw.rect(self.canvas, (16, 24, 44), panel, border_radius=25)
        pygame.draw.rect(self.canvas, (92, 110, 149), panel, width=2, border_radius=25)
        rounded_text(self.canvas, self.font_big, title, color, (WIDTH // 2, HEIGHT // 2 - 62), COLORS["ink"])
        rounded_text(self.canvas, self.font, subtitle, COLORS["cream"], (WIDTH // 2, HEIGHT // 2 - 17), None)
        rounded_text(self.canvas, self.font, f"Pontuação: {self.score}", COLORS["gold"], (WIDTH // 2, HEIGHT // 2 + 23), None)
        self.start_button.rect = pygame.Rect(WIDTH // 2 - 115, HEIGHT // 2 + 54, 230, 54)
        self.start_button.label = "REINICIAR"
        self.start_button.draw(self.canvas, self.font, mouse)
        self.present()

    def present(self):
        sw, sh = self.screen.get_size()
        scaled = pygame.transform.smoothscale(self.canvas, (sw, sh))
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def draw_game(self):
        self.draw_background()
        self.draw_hud()
        aim = self.aim_position()
        self.cat.draw(self.canvas, aim)
        for rat in self.rats:
            rat.draw(self.canvas, self.elapsed, self.wave, self.cat.pos)
        for ball in self.yarn:
            ball.draw(self.canvas, self.elapsed)
        if self.level_message_timer > 0:
            self.draw_level_message()
        self.present()

    def draw_level_message(self):
        """Mostra por alguns segundos a parabenização pela nova fase."""
        panel = pygame.Surface((560, 118), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 18, 35, 225), (0, 0, 560, 118), border_radius=22)
        phase_colors = {2: COLORS["gold"], 3: COLORS["pink"], 4: COLORS["mint"], 5: (230, 91, 112)}
        border = phase_colors.get(self.wave, COLORS["gold"])
        pygame.draw.rect(panel, (*border, 230), (0, 0, 560, 118), width=3, border_radius=22)
        self.canvas.blit(panel, panel.get_rect(center=(WIDTH // 2, 205)))
        rounded_text(self.canvas, self.font_big, "PARABÉNS!", border, (WIDTH // 2, 184), COLORS["ink"])
        message = f"Fase {self.wave - 1} concluída! Você chegou à fase {self.wave}."
        rounded_text(self.canvas, self.font_small, message, COLORS["cream"], (WIDTH // 2, 228), None)

    def run(self):
        # Loop principal: recebe eventos, atualiza a partida e desenha a tela atual.
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000, .04)
            mouse = self.aim_position()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(event.size, pygame.RESIZABLE)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == PLAYING:
                            self.state = MENU
                            self.paused = True
                            if self.music_ready:
                                pygame.mixer.music.pause()
                        else:
                            running = False
                    elif event.key == pygame.K_SPACE and self.state == PLAYING:
                        self.fire()
                    elif event.key == pygame.K_RETURN and self.state in (MENU, WON, LOST):
                        self.reset()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == PLAYING:
                        self.fire()
                    elif self.start_button.rect.collidepoint(mouse):
                        if self.state == MENU and self.paused:
                            self.state = PLAYING
                            self.paused = False
                            if self.music_ready:
                                pygame.mixer.music.unpause()
                        else:
                            self.reset()
            self.update(dt)
            if self.state == MENU:
                self.draw_menu(mouse)
            elif self.state in (WON, LOST):
                self.draw_end(mouse)
            else:
                self.start_button.label = "COMEÇAR A JOGAR"
                self.draw_game()
        pygame.quit()
        return 0


if __name__ == "__main__":
    sys.exit(Game().run())
