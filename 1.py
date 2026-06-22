import pygame as pg, random as r, os
from PIL import Image
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

W, H, TS, SCR_W, SCR_H = 150, 80, 40, 800, 600
pg.init(); scr = pg.display.set_mode((SCR_W, SCR_H)); clock = pg.time.Clock()

def load_img(name):
    path = f"{name}.png"
    if os.path.exists(path):
        img = Image.open(path).convert("RGBA")
        if name in ['wooden_pickaxe', 'wooden_axe']:
            w, h = img.width, img.height
            left, top, right, bottom = w, h, 0, 0
            has_pixels = False
            for y in range(h):
                for x in range(w):
                    r_c, g_c, b_c, a_c = img.getpixel((x, y))
                    if not (r_c > 240 and g_c > 240 and b_c > 240) and a_c > 0:
                        if x < left: left = x
                        if x > right: right = x
                        if y < top: top = y
                        if y > bottom: bottom = y
                        has_pixels = True
            if has_pixels and (right >= left) and (bottom >= top):
                img = img.crop((left, top, right + 1, bottom + 1))
        img = img.resize((TS, TS), Image.Resampling.LANCZOS)
        new_img = Image.new("RGBA", img.size)
        for y in range(img.height):
            for x in range(img.width):
                r_c, g_c, b_c, a_c = img.getpixel((x, y))
                if r_c > 240 and g_c > 240 and b_c > 240:
                    new_img.putpixel((x, y), (255, 255, 255, 0))
                else:
                    new_img.putpixel((x, y), (r_c, g_c, b_c, a_c))
        return pg.image.frombytes(new_img.tobytes(), new_img.size, new_img.mode)
    s = pg.Surface((TS, TS)); s.fill(r.choice([(100,100,100), (130,80,40), (50,150,50)]))
    return s

# Загружаем ВСЕ новые текстуры крафта
ITEM_NAMES = ['grass', 'dirt', 'stone', 'wood', 'leaves', 'wooden_pickaxe', 'wooden_axe', 
              'planks', 'crafting_table', 'door', 'glass_block', 'torch', 'stone_bricks']
txt = {n: load_img(n) for n in ITEM_NAMES}

# --- СЛОВАРЬ РЕЦЕПТОВ КРАФТА ---
# Что получаем: { что нужно : количество }
CRAFTING_RECIPES = {
    'planks': {'wood': 1, 'result_count': 4},
    'crafting_table': {'planks': 4, 'result_count': 1},
    'torch': {'wood': 1, 'result_count': 4},
    'stone_bricks': {'stone': 2, 'result_count': 2},
    'glass_block': {'dirt': 2, 'result_count': 1},
    'door': {'planks': 6, 'result_count': 1}
}

# --- ГЕНЕРАЦИЯ МИРА ---
world = []
gh = int(H/3)
for x in range(W):
    col = []
    current_gh = int(gh + r.randint(-1, 1))
    for y in range(H):
        if y < current_gh: col.append('air')
        elif y == current_gh: col.append('grass')
        elif y < current_gh + 6: col.append('dirt')
        else: col.append('air' if r.random() < 0.12 else 'stone')
    world.append(col)

for _ in range(W // 3):
    tx = r.randint(5, W-6)
    for y in range(H):
        if world[tx][y] == 'grass':
            for h in range(1, r.randint(4, 6)): world[tx][y-h] = 'wood'
            for lx in range(tx-2, tx+3):
                for ly in range(y-6, y-3):
                    if 0 <= lx < W and 0 <= ly < H and world[lx][ly] == 'air': world[lx][ly] = 'leaves'
            break

# Расширенный инвентарь (ресурсы + новые предметы крафта)
inventory = {n: 0 for n in ITEM_NAMES if 'pickaxe' not in n and 'axe' not in n}
inventory['stone'] = 10  # Дадим немного стартовых ресурсов на тесты
inventory['wood'] = 10

# Хотбар предметов (все, что можно взять в руки и поставить)
inv_slots = ITEM_NAMES
active_slot_idx = 5 # Начинаем с кирки

spawn_tile_y = gh
for y in range(H):
    if world[y] == 'grass': spawn_tile_y = y; break

pl = pg.Rect(20*TS, (spawn_tile_y - 2)*TS, int(TS*0.8), int(TS*1.8))
vx, vy, on_g, cx, cy = 0, 0, False, 0, 0
show_craft_menu = False # Флаг открытия меню крафта

run = True
while run:
    clock.tick(60); scr.fill((135, 206, 235))
    current_item = inv_slots[active_slot_idx]

    for e in pg.event.get():
        if e.type == pg.QUIT: run = False
        
        if e.type == pg.KEYDOWN:
            # Открытие/закрытие меню крафта на E (укр/рус У)
            if e.key == pg.K_e:
                show_craft_menu = not show_craft_menu
            # Быстрый выбор слотов 1-9
            if pg.K_1 <= e.key <= pg.K_9:
                active_slot_idx = min(e.key - pg.K_1, len(inv_slots) - 1)
                
        if e.type == pg.MOUSEBUTTONDOWN:
            mx, my = pg.mouse.get_pos()
            
            # ЛОГИКА КЛИКОВ В МЕНЮ КРАФТА
            if show_craft_menu:
                if e.button == 1: # ЛКМ по кнопке крафта
                    for idx, (res_item, reqs) in enumerate(CRAFTING_RECIPES.items()):
                        btn_rect = pg.Rect(520, 80 + idx * 60, 260, 45)
                        if btn_rect.collidepoint(mx, my):
                            req_mat = list(reqs.keys())[0]
                            req_cnt = reqs[req_mat]
                            # Если ресурсов хватает — забираем их и выдаем крафт!
                            if inventory.get(req_mat, 0) >= req_cnt:
                                inventory[req_mat] -= req_cnt
                                inventory[res_item] += reqs['result_count']
                continue # Если открыто меню, мир не ломаем
                
            # ЛОГИКА СТРОЙКИ И РАЗРУШЕНИЯ МИРА
            bx, by = int((mx + cx) // TS), int((my + cy) // TS)
            if 0 <= bx < W and 0 <= by < H:
                if e.button == 1: # ЛКМ
                    target_block = world[bx][by]
                    # Кирка копает твердое, топор — дерево
                    if current_item == "wooden_pickaxe" and target_block in ['stone', 'dirt', 'grass', 'stone_bricks', 'glass_block']:
                        if target_block in inventory: inventory[target_block] += 1
                        world[bx][by] = 'air'
                    elif current_item == "wooden_axe" and target_block in ['wood', 'leaves', 'planks', 'crafting_table', 'door']:
                        if target_block in inventory: inventory[target_block] += 1
                        world[bx][by] = 'air'
                        
                if e.button == 3 and world[bx][by] == 'air': # ПКМ (Ставим любой блок из инвентаря)
                    if current_item in inventory and inventory[current_item] > 0:
                        block_rect = pg.Rect(bx*TS, by*TS, TS, TS)
                        if not pl.colliderect(block_rect) or current_item in ['wood', 'torch', 'door']:
                            world[bx][by] = current_item
                            inventory[current_item] -= 1
            
            # СКРОЛЛ ХОТБАРА СЛОТОВ
            if e.button == 4: active_slot_idx = (active_slot_idx - 1) % len(inv_slots)
            if e.button == 5: active_slot_idx = (active_slot_idx + 1) % len(inv_slots)

    # Физика ходьбы
    if not show_craft_menu:
        k = pg.key.get_pressed()
        vx = (k[pg.K_RIGHT] or k[pg.K_d]) * 5 - (k[pg.K_LEFT] or k[pg.K_a]) * 5
        if not on_g: vy = min(15, vy + 0.6)
        if (k[pg.K_SPACE] or k[pg.K_UP] or k[pg.K_w]) and on_g: vy, on_g = -13, False

        pl.x += vx
        for x in range(max(0, pl.x//TS), min(W, (pl.right//TS)+1)):
            for y in range(max(0, pl.y//TS), min(H, (pl.bottom//TS)+1)):
                if world[x][y] != 'air' and world[x][y] not in ['wood', 'torch', 'door'] and pl.colliderect(pg.Rect(x*TS, y*TS, TS, TS)):
                    pl.right = x*TS if vx > 0 else pl.left
                    if vx < 0: pl.left = (x+1)*TS
                    
        pl.y += vy; on_g = False
        for x in range(max(0, pl.x//TS), min(W, (pl.right//TS)+1)):
            for y in range(max(0, pl.y//TS), min(H, (pl.bottom//TS)+1)):
                if world[x][y] != 'air' and world[x][y] not in ['wood', 'torch', 'door'] and pl.colliderect(pg.Rect(x*TS, y*TS, TS, TS)):
                    pl.bottom = y*TS if vy > 0 else pl.top
                    if vy > 0: vy, on_g = 0, True
                    else: vy = 0

    cx += (pl.centerx - SCR_W/2 - cx) * 0.1; cy += (pl.centery - SCR_H/2 - cy) * 0.1
    cx, cy = max(0, min(cx, W*TS-SCR_W)), max(0, min(cy, H*TS-SCR_H))

    # Рендеринг блоков мира
    for x in range(max(0, int(cx//TS)), min(W, int((cx+SCR_W)//TS)+2)):
        for y in range(max(0, int(cy//TS)), min(H, int((cy+SCR_H)//TS)+2)):
            if world[x][y] != 'air': scr.blit(txt[world[x][y]], (x*TS - cx, y*TS - cy))

    pg.draw.rect(scr, (0, 207, 198), (pl.x - cx, pl.y - cy, pl.w, pl.h))
    
    # --- ОТРИСОВКА НИЖНЕГО ХОТБАРА ---
    pg.draw.rect(scr, (30, 30, 30), (10, SCR_H - 65, SCR_W - 20, 55))
    font_ui = pg.font.SysFont("Arial", 11, bold=True)
    for i, slot in enumerate(inv_slots):
        slot_x = 15 + i * 58
        if slot_x + 50 > SCR_W - 10: break
        bg_color = (220, 220, 220) if i == active_slot_idx else (80, 80, 80)
        pg.draw.rect(scr, bg_color, (slot_x, SCR_H - 60, 52, 45))
        
        scaled_icon = pg.transform.scale(txt[slot], (26, 26))
        scr.blit(scaled_icon, (slot_x + 13, SCR_H - 58))
        
        if slot in inventory:
            count_text = font_ui.render(str(inventory[slot]), True, (255, 255, 255))
            scr.blit(count_text, (slot_x + 4, SCR_H - 28))

    # --- ОТРИСОВКА КРАФТ-МЕНЮ (ПО НАЖАТИЮ 'E') ---
    if show_craft_menu:
        # Рисуем подложку меню справа экрана
        pg.draw.rect(scr, (50, 50, 50), (500, 20, 290, 500))
        pg.draw.rect(scr, (255, 255, 255), (500, 20, 290, 500), 3)
        
        title_font = pg.font.SysFont("Arial", 16, bold=True)
        scr.blit(title_font.render("РЕЦЕПТЫ КРАФТА:", True, (255, 255, 255)), (520, 35))
        
        for idx, (res_item, reqs) in enumerate(CRAFTING_RECIPES.items()):
            # Безопасно достаем название нужного материала и его количество
            req_mat = [k for k in reqs.keys() if k != 'result_count'][0]
            req_cnt = reqs[req_mat]
            res_cnt = reqs['result_count']
            
            # Цвет кнопки зависит от наличия ресурсов
            can_craft = inventory.get(req_mat, 0) >= req_cnt
            btn_color = (70, 150, 70) if can_craft else (100, 70, 70)
            
            btn_rect = pg.Rect(520, 80 + idx * 60, 250, 45)
            pg.draw.rect(scr, btn_color, btn_rect)
            pg.draw.rect(scr, (255, 255, 255), btn_rect, 1)
            
            # Иконка результата
            scr.blit(pg.transform.scale(txt[res_item], (22, 22)), (525, 91 + idx * 60))
            
            # Текст рецепта
            craft_txt = f"{res_item} x{res_cnt} (Нужно: {req_mat} x{req_cnt})"
            scr.blit(font_ui.render(craft_txt, True, (255, 255, 255)), (555, 95 + idx * 60))

    pg.display.flip()

pg.quit()
