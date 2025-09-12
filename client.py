from pygame import *
import socket
import json
from threading import Thread
from Menu_for_pin import Menu

menu = Menu()
menu.mainloop()

name = menu.name or "Player"
host = str(menu.host).strip() or "localhost"
try:
    port = int(menu.port)
except:
    print("❌ Порт введений неправильно")
    exit()
chosen_color = menu.color if menu.color else (255, 0, 255)

WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

buffer = ""
game_state = {}
game_over = False
winner = None
you_winner = None

# --- Підключення ---
def connect_to_server():
    global buffer, game_state, client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print("Host:", repr(host))
    print("Port:", repr(port))
    client.connect((host, port))

    my_id = int(client.recv(16).decode().strip())

    player_info = {"name": name, "color": chosen_color}
    msg = {"type": "player_info", "data": player_info}
    client.sendall((json.dumps(msg) + "\n").encode())

    return my_id

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            if not data:
                break
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# --- Шрифти ---
font_win = font.Font(None, 72)
font_main = font.Font(None, 36)
font_write = font.Font(None, 20)

# --- Картинки та звуки ---
bg = transform.scale(image.load('images/bg_pin.jpg'), (WIDTH, HEIGHT))
win_img = transform.scale(image.load('images/13588.jpg'), (WIDTH, HEIGHT))
lose_img = transform.scale(image.load('images/game-lose.jpg'), (WIDTH, HEIGHT))
wall_collide = mixer.Sound('images/click-menu-app-147357.mp3')
plat_collide = mixer.Sound('images/click-game-menu-147356.mp3')
win_sound = mixer.Sound('images/new-level-142995.mp3')
lose_sound = mixer.Sound('images/error-08-206492.mp3')

# --- Запускаємо ---
my_id = connect_to_server()
Thread(target=receive, daemon=True).start()

default_color = (255, 0, 255)
play = play1 = 0

while True:
    for e in event.get():
        if e.type == QUIT:
            exit()

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.fill((0, 0, 0))
        countdown_text = font.Font(None, 72).render(
            str(game_state["countdown"]), True, (255, 255, 255)
        )
        screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
        display.update()
        continue

    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(win_img, (0, 0))

        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)

        if you_winner:
            text = "Ти переміг!"
            if play == 0:
                win_sound.play()
                play += 1
        else:
            text = "Пощастить наступним разом!"
            screen.blit(lose_img, (0, 0))
            if play1 == 0:
                lose_sound.play()
                play1 += 1

        win_text = font_win.render(text, True, (255,200,89))
        screen.blit(win_text, win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        restart_text = font_win.render('К - рестарт', True, (255, 215, 0))
        screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120)))

        display.update()
        continue

    if game_state:
        screen.blit(bg, (0, 0))
        players = game_state.get("players", {})

        # Ліва платформа
        color1 = tuple(players.get("0", {}).get("color", default_color))
        name1 = players.get("0", {}).get("name", "Player 1")
        draw.rect(screen, color1, (20, game_state['paddles']['0'], 20, 100))
        screen.blit(font_write.render(name1, True, (255, 255, 255)), (20, game_state['paddles']['0'] - 20))

        # Права платформа
        color2 = tuple(players.get("1", {}).get("color", default_color))
        name2 = players.get("1", {}).get("name", "Player 2")
        draw.rect(screen, color2, (WIDTH - 40, game_state['paddles']['1'], 20, 100))
        screen.blit(font_write.render(name2, True, (255, 255, 255)), (WIDTH - 70, game_state['paddles']['1'] - 20))

        # М'яч
        draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)

        score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
        screen.blit(score_text, (WIDTH // 2 - 25, 40))
        screen.blit(font_write.render(name1, True, (255, 255, 255)), (WIDTH // 2 +30, 20))
        screen.blit(font_write.render(name2, True, (255, 255, 255)), (WIDTH // 2 -100,20))
        if game_state['sound_event'] == 'wall_hit':
            wall_collide.play()
        elif game_state['sound_event'] == 'platform_hit':
            plat_collide.play()

    else:
        waiting_text = font_main.render("Очікування гравців...", True, (255, 255, 255))
        screen.blit(waiting_text, (WIDTH // 2 - 100, HEIGHT // 2))

    display.update()
    clock.tick(60)

    # --- Керування ---
    keys = key.get_pressed()
    if keys[K_w]:
        client.sendall((json.dumps("UP") + "\n").encode())
    elif keys[K_s]:
        client.sendall((json.dumps("DOWN") + "\n").encode())

    if game_state and ("winner" in game_state and game_state["winner"] is not None):
        if keys[K_k]:
            game_over = True
            try:
                client.close()
            except:
                pass
            winner = None
            you_winner = None
            game_over = False
