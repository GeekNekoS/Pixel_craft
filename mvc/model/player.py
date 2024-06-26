from config import player_sprites
from typing import List, Tuple
from settings import debug
import pygame
import random


pygame.mixer.init()
footstep_sounds = [
    pygame.mixer.Sound('assets/sounds/footsteps/footstep_1.wav'),
    pygame.mixer.Sound('assets/sounds/footsteps/footstep_2.wav'),
    pygame.mixer.Sound('assets/sounds/footsteps/footstep_3.wav')
]


class PlayerSounds:
    def __init__(self, footstep_speed: float = 0.3):
        """Инициализирует звуки игрока, включая звуки шагов."""
        # Загрузка звуковых файлов
        self.footstep_sounds = footstep_sounds

        # Скорость воспроизведения звуков ходьбы
        self.footstep_speed = footstep_speed
        self.footstep_timer = 0  # Таймер для отслеживания времени между звуками
        self.next_footstep_time = 0  # Время до следующего звука
        self.set_footstep_volume(0.3)  # Начальная громкость звуков шагов

    def update(self, dt: float) -> None:
        """Обновляет состояние звуков игрока."""
        self.footstep_timer += dt

    def play_footstep(self) -> None:
        """Воспроизводит звук шага игрока."""
        # Проверяем, прошло ли достаточно времени для воспроизведения следующего звука
        if self.footstep_timer >= self.next_footstep_time:
            # Воспроизводим случайный звук шага
            footstep_sound = random.choice(self.footstep_sounds)
            footstep_sound.play()

            # Сбрасываем таймер
            self.footstep_timer = 0

            # Устанавливаем время до следующего звука
            self.next_footstep_time = self.footstep_speed

    def set_footstep_volume(self, volume: float) -> None:
        """Устанавливает громкость звуков шагов."""
        for sound in self.footstep_sounds:
            sound.set_volume(volume)


class Player(pygame.sprite.Sprite):
    def __init__(self, start_pos: Tuple[int, int], player_sounds: PlayerSounds):
        """Инициализирует игрока с заданной позицией и звуками."""
        super().__init__()
        # Загрузка спрайтов для всех направлений
        self.sprites = {
            'left': [pygame.image.load(f'{player_sprites}left_{i}.png').convert_alpha() for i in range(1, 5)],
            'right': [pygame.image.load(f'{player_sprites}right_{i}.png').convert_alpha() for i in range(1, 5)],
            'up': [pygame.image.load(f'{player_sprites}up_{i}.png').convert_alpha() for i in range(1, 5)],
            'down': [pygame.image.load(f'{player_sprites}down_{i}.png').convert_alpha() for i in range(1, 5)]
        }
        self.direction = 'down'
        self.current_sprites = self.sprites[self.direction]
        self.current_frame = 0
        self.image = self.current_sprites[self.current_frame]
        self.rect = self.image.get_rect(topleft=start_pos)
        self.movement_speed = 150
        self.animation_speed = 0.25
        self.animation_counter = 0

        # Установка хитбокса
        hitbox_width = self.rect.width // 2
        hitbox_height = self.rect.height // 2
        self.hitbox = pygame.Rect(
            self.rect.x + (self.rect.width - hitbox_width) // 2,
            self.rect.y + (self.rect.height - hitbox_height) // 2,
            hitbox_width,
            hitbox_height
        )

        self.player_sounds = player_sounds  # Сохраняем экземпляр класса PlayerSounds
        self.is_moving = False  # Инициализируем флаг движения

    def update(self, keys: List[int], dt: float, trees: List[Tuple[int, pygame.Rect]]) -> None:
        """Обновляет состояние игрока на основе ввода клавиш, времени и препятствий."""
        self.player_sounds.update(dt)  # Обновляем таймер звуков игрока
        self.move(keys, dt, trees)
        if self.is_moving:
            self.animate(dt)
            self.player_sounds.play_footstep()  # Воспроизводим звуки ходьбы

    def animate(self, dt: float) -> None:
        """Обновляет анимацию игрока."""
        self.animation_counter += dt
        if self.animation_counter >= self.animation_speed:
            self.animation_counter = 0
            self.current_frame = (self.current_frame + 1) % len(self.current_sprites)
            self.image = self.current_sprites[self.current_frame]

    def move(self, keys: List[int], dt: float, trees: List[Tuple[int, pygame.Rect]]) -> None:
        """Обрабатывает движение игрока в зависимости от нажатых клавиш."""
        dx, dy = 0, 0
        moving = False

        if keys[pygame.K_a]:  # Лево
            dx -= self.movement_speed * dt
            self.direction = 'left'
            self.current_sprites = self.sprites['left']
            moving = True
        elif keys[pygame.K_d]:  # Право
            dx += self.movement_speed * dt
            self.direction = 'right'
            self.current_sprites = self.sprites['right']
            moving = True
        elif keys[pygame.K_w]:  # Вверх
            dy -= self.movement_speed * dt
            self.direction = 'up'
            self.current_sprites = self.sprites['up']
            moving = True
        elif keys[pygame.K_s]:  # Вниз
            dy += self.movement_speed * dt
            self.direction = 'down'
            self.current_sprites = self.sprites['down']
            moving = True

        if moving:
            new_rect = self.rect.move(dx, dy)
            new_hitbox = self.hitbox.move(dx, dy)

            # Проверка на столкновения с деревьями
            if all(not tree[1].colliderect(new_hitbox) for tree in trees):
                self.rect = new_rect
                self.hitbox = new_hitbox
                self.is_moving = True  # Устанавливаем флаг движения
            else:
                # Если есть столкновение, персонаж не должен двигаться
                self.is_moving = False
        else:
            # Если не нажата ни одна клавиша для движения, анимация должна остановиться
            self.is_moving = False
            self.current_frame = 0  # Сброс текущего кадра

        self.animate(dt)  # Всегда обновляем анимацию

        self.update_hitbox()

    def draw(self, screen: pygame.Surface, camera_x: int, camera_y: int) -> None:
        """Отображает игрока на экране."""
        # Смещаем координаты отображения на основе камеры
        draw_rect = self.rect.move(-camera_x, -camera_y)
        draw_hitbox = self.hitbox.move(-camera_x, -camera_y)

        # Отрисовываем спрайт и хитбокс
        screen.blit(self.image, draw_rect)
        if debug:
            pygame.draw.rect(screen, (255, 0, 0), draw_hitbox, 1)  # Отрисовка хитбокса красной линией

    def update_hitbox(self) -> None:
        """Обновляет положение хитбокса игрока."""
        hitbox_width = self.rect.width // 2
        hitbox_height = self.rect.height // 2
        self.hitbox = pygame.Rect(
            self.rect.x + (self.rect.width - hitbox_width) // 2,
            self.rect.y + self.rect.height - hitbox_height,
            hitbox_width,
            hitbox_height
        )
