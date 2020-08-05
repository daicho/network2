import os
import sys
import time
import glob
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np
import cv2
from .. import system as mj

# 麻雀牌のサイズ
MJHAI_WIDTH = 30
MJHAI_HEIGHT = 38
SCREEN_SIZE = 12 * MJHAI_HEIGHT + 7 * MJHAI_WIDTH

# フォントファイル
THIS_PATH = os.path.dirname(os.path.abspath(__file__))
FONT_FILE = THIS_PATH + "/font/YuGothB.ttc"

KAZE_NAME = ["東", "南", "西", "北"]

# 画像ファイル読み込み
hai_img = {}
mjhai_files = glob.glob(THIS_PATH + "/mjhai/*.png") # ファイル一覧を取得

for mjhai_file in mjhai_files:
    img_key, ext = os.path.splitext(os.path.basename(mjhai_file)) # ファイル名を抽出
    hai_img[img_key] = Image.open(mjhai_file)

t100_img = Image.open(THIS_PATH + "/image/100.png")
t1000_img = Image.open(THIS_PATH + "/image/1000.png")
remain_img = Image.open(THIS_PATH + "/image/remain.png")

# Pillow→OpenCV変換
def pil2cv(image):
    new_image = np.array(image)
    if new_image.shape[2] == 3: # カラー
        new_image = new_image[:, :, ::-1]
    elif new_image.shape[2] == 4: # 透過
        new_image = new_image[:, :, [2, 1, 0, 3]]
    return new_image

# 横向きの画像を生成
def draw_side(img):
    w, h = img.size
    create_img = Image.new("RGBA", (h, h))

    rotate_img = img.rotate(90, expand=True)
    create_img.paste(rotate_img, (0, h - w))

    return create_img

# 単色を合成した画像を生成
def draw_mix(img, color):
    create_img = Image.new("RGB", img.size)
    mix_img = Image.new("RGBA", img.size, color)

    create_img.paste(img)
    create_img.paste(mix_img, (0, 0), mix_img)
    return create_img

# 手牌の画像を生成
def draw_tehai(tehai, back=False):
    create_img = Image.new("RGBA", (14 * MJHAI_WIDTH + 4 * MJHAI_HEIGHT, 2 * MJHAI_HEIGHT))
    img_draw = ImageDraw.Draw(create_img)
    img_draw.font = ImageFont.truetype(FONT_FILE, 12)

    x = 0
    for i, hai in enumerate(tehai.hais):
        # 番号
        if not back:
            w, h = img_draw.textsize(str(i))
            img_draw.text(
                (x + (MJHAI_WIDTH - w) / 2, MJHAI_HEIGHT - h - 4),
                str(i)
            )

        # 麻雀牌
        mjhai_draw = hai_img["back" if back else hai.name]
        create_img.paste(mjhai_draw, (x, MJHAI_HEIGHT))
        x += MJHAI_WIDTH

    if tehai.tsumo_hai is not None:
        # ツモった牌は離す
        x += int(MJHAI_WIDTH / 4)

        # 番号
        if not back:
            w, h = img_draw.textsize(str(i + 1))
            img_draw.text(
                (x + (MJHAI_WIDTH - w) / 2, MJHAI_HEIGHT - h - 4),
                str(i + 1)
            )

        # 麻雀牌
        mjhai_draw = hai_img["back" if back else tehai.tsumo_hai.name]

        create_img.paste(mjhai_draw, (x, MJHAI_HEIGHT))
        x += MJHAI_HEIGHT

    # 副露
    x = create_img.size[0]
    for furo in tehai.furos:
        for i, hai in enumerate(furo.hais):
            # 麻雀牌
            if furo.kind == mj.FuroKind.ANKAN and (i == 0 or i == 3):
                mjhai_draw = hai_img["back"]
            else:
                mjhai_draw = hai_img[hai.name]

            if furo.kind == mj.FuroKind.KAKAN and i == 3:
                # 加槓
                create_img.paste(
                    draw_side(mjhai_draw),
                    (x + (3 - furo.direct) * MJHAI_WIDTH, MJHAI_HEIGHT - MJHAI_WIDTH)
                )
            else:
                # 他家からの牌は横にする
                if furo.kind != mj.FuroKind.ANKAN and furo.direct == i + 1:
                    create_img.paste(draw_side(mjhai_draw), (x - MJHAI_HEIGHT, MJHAI_HEIGHT))
                    x -= MJHAI_HEIGHT
                else:
                    create_img.paste(mjhai_draw, (x - MJHAI_WIDTH, MJHAI_HEIGHT))
                    x -= MJHAI_WIDTH

    return create_img

# 河の画像を生成
def draw_kawa(kawa):
    create_img = Image.new("RGBA", (5 * MJHAI_WIDTH + MJHAI_HEIGHT, 4 * MJHAI_HEIGHT))

    x = 0
    y = 0

    for kawa_hai in kawa.hais:

        paste_img = Image.new("RGB", (MJHAI_WIDTH, MJHAI_HEIGHT))
        paste_img.paste(hai_img[kawa_hai.hai.name])

        # ツモ切りは暗くする
        if kawa_hai.tsumogiri:
            paste_img = draw_mix(paste_img, (0, 0, 0, 47))

        # 鳴かれた牌は青くする
        if kawa_hai.furo:
            paste_img = draw_mix(paste_img, (0, 63, 255, 47))

        # 放銃した牌は赤くする
        if kawa_hai.hoju:
            paste_img = draw_mix(paste_img, (255, 63, 0, 47))

        # 立直宣言牌は横にする
        if kawa_hai.richi:
            already_richi = True
            create_img.paste(draw_side(paste_img), (x, y))
            x += MJHAI_HEIGHT
        else:
            create_img.paste(paste_img, (x, y))
            x += MJHAI_WIDTH

        # 6枚で改行
        if x >= 6 * MJHAI_WIDTH:
            x = 0
            y += MJHAI_HEIGHT

    return create_img

# ゲーム情報
def draw_info(game):
    size = 5 * MJHAI_WIDTH
    create_img = Image.new("RGBA", (size, size))

    # 局
    kyoku_name = "{}{}局".format(KAZE_NAME[game.bakaze], game.kyoku + 1)

    img_draw = ImageDraw.Draw(create_img)
    img_draw.font = ImageFont.truetype(FONT_FILE, 20)
    w, h = img_draw.textsize(kyoku_name)
    img_draw.text(((size - w) / 2, 0), kyoku_name)

    # 本場
    img_draw.font = ImageFont.truetype(FONT_FILE, 16)
    w, h = img_draw.textsize("×{}".format(game.honba))
    img_draw.text(
        (t100_img.size[0] + 2, MJHAI_WIDTH + (t100_img.size[1] - h) / 2),
        "×{}".format(game.honba)
    )

    create_img.paste(t100_img, (2, MJHAI_WIDTH))

    # 供託
    w, h = img_draw.textsize("×{}".format(game.kyotaku))
    img_draw.text(
        (size - w - 2, MJHAI_WIDTH + (t1000_img.size[1] - h) / 2),
        "×{}".format(game.kyotaku)
    )

    create_img.paste(t1000_img, (size - t1000_img.size[0] - w - 2, MJHAI_WIDTH))

    # 残り
    w, h = img_draw.textsize("×{:02}".format(game.yama_remain))
    img_draw.text(
        ((size + remain_img.size[0] - w) / 2, MJHAI_WIDTH + (remain_img.size[1] - h) / 2 + 20),
        "×{:02}".format(game.yama_remain)
    )

    create_img.paste(
        remain_img,
        (int((size - remain_img.size[0] - w) / 2), MJHAI_WIDTH + 20)
    )

    return create_img

# ドラ
def draw_dora(doras, uradoras):
    create_img = Image.new("RGBA", (5 * MJHAI_WIDTH, 2 * MJHAI_HEIGHT))

    for i in range(5):
        # ドラ
        if i < len(doras):
            paste_img = hai_img[doras[i].name]
        else:
            paste_img = hai_img["back"]

        create_img.paste(paste_img, (i * MJHAI_WIDTH, 0))

        # 裏ドラ
        if uradoras is not None and i < len(uradoras):
            paste_img = hai_img[uradoras[i].name]
        else:
            paste_img = hai_img["back"]

        create_img.paste(paste_img, (i * MJHAI_WIDTH, MJHAI_HEIGHT))

    return create_img

# ゲーム画面の画像を生成
def draw_screen(game, players, view):
    create_img = Image.new("RGB", (SCREEN_SIZE, SCREEN_SIZE), "green")

    for i in range(game.player_num):
        game_player = game.players[i]
        player = None

        for cur_player in players:
            if game_player.chicha == cur_player.chicha:
                player = cur_player

        paste_img = Image.new("RGBA", (SCREEN_SIZE, SCREEN_SIZE))

        # 手牌
        if player is None:
            if game_player.tehai.hais is None:
                tehai = mj.Tehai([mj.Hai(0, 0) for j in range(game_player.tehai.hai_num - 1)], game_player.tehai.furos)
                tehai.tsumo(mj.Hai(0, 0))

                if not game_player.tehai.exist_tsumo_hai:
                    tehai.store()

                tehai_img = draw_tehai(tehai, True)
            else:
                tehai = mj.Tehai([hai for hai in game_player.tehai.hais], game_player.tehai.furos)
                tehai.tsumo(game_player.tehai.tsumo_hai)
                tehai_img = draw_tehai(tehai)
        else:
            tehai_img = draw_tehai(player.tehai)

        paste_img.paste(
            tehai_img,
            (SCREEN_SIZE - tehai_img.size[0], 7 * MJHAI_WIDTH + 10 * MJHAI_HEIGHT),
            tehai_img
        )

        # 河
        kawa_img = draw_kawa(game_player.kawa)
        paste_img.paste(
            kawa_img,
            (6 * MJHAI_HEIGHT + int(0.5 * MJHAI_WIDTH), 7 * MJHAI_WIDTH + 6 * MJHAI_HEIGHT),
            kawa_img
        )

        # 自風&点数
        img_draw = ImageDraw.Draw(paste_img)
        img_draw.font = ImageFont.truetype(FONT_FILE, 16)
        jikaze = game_player.chicha - game.kyoku % game.player_num
        w, h = img_draw.textsize("[{}] {}".format(KAZE_NAME[jikaze], game_player.point))

        img_draw.text(
            ((SCREEN_SIZE - w) / 2, 6.5 * MJHAI_WIDTH + 6 * MJHAI_HEIGHT - h / 2),
            "[{}] {}".format(KAZE_NAME[jikaze], game_player.point),
            (255, 255, 0)
        )

        # 番
        if game_player == game.cur_player:
            x = (SCREEN_SIZE - w) / 2 - 16
            y = 6.5 * MJHAI_WIDTH + 6 * MJHAI_HEIGHT - 5
            img_draw.rectangle((x, y, x + 10, y + 10), (255, 255, 127), (0, 0, 0))

        # プレイヤー名&シャンテン数
        draw_str = game_player.name
        if player is not None:
            draw_str += " [{}ST]".format(player.tehai.shanten())

        w, h = img_draw.textsize(draw_str)
        img_draw.text(
            (SCREEN_SIZE - tehai_img.size[0], SCREEN_SIZE - tehai_img.size[1]),
            draw_str,
        )

        # 回転&合成
        rotate_img = paste_img.rotate((game_player.chicha - view.chicha) * 90)
        create_img.paste(rotate_img, (0, 0), rotate_img)

    # ゲーム情報
    info_img = draw_info(game)
    create_img.paste(
        info_img,
        (6 * MJHAI_HEIGHT + MJHAI_WIDTH, 6 * MJHAI_HEIGHT + MJHAI_WIDTH),
        info_img
    )

    # ドラ
    dora_img = draw_dora(game.dora_hais, game.uradora_hais)
    create_img.paste(
        dora_img,
        (6 * MJHAI_HEIGHT + MJHAI_WIDTH, 4 * MJHAI_HEIGHT + 6 * MJHAI_WIDTH),
        dora_img
    )

    return create_img

class Screen():
    def __init__(self, game, players, view=None, title=""):
        self.game = game
        self.players = players
        self.view = view
        self.title = title

        # ウィンドウ名
        self.win_name = self.title
        if view is not None:
            self.win_name += " [" + view.name + "]"

    # 画面描画
    def draw(self):
        cur_view = self.game.cur_player if self.view is None else self.view
        img = pil2cv(draw_screen(self.game, self.players, cur_view))
        cv2.imshow(self.win_name, img)

        if cv2.waitKey(1) & 0xff == ord("q"):
            sys.exit()
