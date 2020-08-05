import sys
import time
import random
import copy
import pickle

from .core import *
from .. import graphic as mg

from mahjong.hand_calculating.hand import HandCalculator
from mahjong.meld import Meld
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.tile import TilesConverter
from mahjong.constants import EAST, SOUTH, WEST, NORTH

# ゲーム
class Game():
    def __init__(self, hai_set, players, start_point):
        seed = time.time()
        random.seed(seed)
        print("seed = {}".format(seed))

        self.calculator = HandCalculator() 

        self.hai_set = hai_set
        self.players = players
        self.player_num = len(self.players)
        self.start_point = start_point

        self.game_reader = GameReader(self.hai_set, self.player_num, self.start_point)

        for i, player in enumerate(self.players):
            player.setup(self.game_reader, i, self.start_point)

        self.bakaze = 0  # 場風
        self.kyoku = 0   # 局
        self.honba = 0   # 本場
        self.kyotaku = 0 # 供託

        # 番
        self.turn = 0
        self.cur_player = self.players[self.turn]

        # 牌山
        self.yama = Yama(self.hai_set)
        self.dora_hais = [self.yama.doras[0]]
        self.uradora_hais = [self.yama.uradoras[0]]
        self.doras = [self.dora_kind(self.dora_hais[0])]
        self.uradoras = [self.dora_kind(self.uradora_hais[0])]

    # ゲーム開始
    def start(self):
        while self.bakaze <= 1:
            renchan, ryukyoku = self.start_kyoku()
            self.next_kyoku(renchan, ryukyoku)
    
    # 局開始
    def start_kyoku(self):
        # コンソール表示
        print("{} {}本場 供託{}".format(self.kyoku_name(), self.honba, self.kyotaku))

        # 配牌
        for player in self.players:
            self.haipai(player)

        while self.yama.remain > 0:
            # ツモ
            self.tsumo_pop(self.cur_player)

            # コンソール表示
            print("{} ({}) [残り{}]".format(self.cur_player.name, self.cur_player.point, self.yama.remain))
            self.cur_player.tehai.show()

            # ツモ判定
            if self.check_tsumo(self.cur_player) and self.on_tsumo(self.cur_player):
                self.tsumo(self.cur_player)
                return self.jikaze(self.cur_player) == 0, False

            cont = False

            # 暗槓
            for cur_hais in self.check_ankan(self.cur_player):
                if self.on_ankan(self.cur_player, cur_hais):
                    self.ankan(self.cur_player, cur_hais)
                    cont = True
                    break

            if cont:
                continue

            # 加槓
            for cur_hai in self.check_kakan(self.cur_player):
                if self.on_kakan(self.cur_player, cur_hai):
                    # 槍槓判定
                    for player in self.players:
                        # 自身は判定しない
                        if player == self.cur_player:
                            continue

                        if self.check_ron(player, cur_hai, self.cur_player) and self.on_ron(player, cur_hai.hai, self.cur_player):
                            self.ron(player, cur_hai, self.cur_player, True)

                            ron = True
                            if self.jikaze(player) == 0:
                                renchan = True

                    if ron:
                        return renchan, False

                    self.kakan(self.cur_player, cur_hai)
                    cont = True
                    break

            if cont:
                continue

            while True:
                # 打牌
                if self.cur_player.richi:
                    index = -1
                else:
                    index = self.on_dahai(self.cur_player)

                check_hai = self.dahai(self.cur_player, index)

                # 立直
                if not self.cur_player.richi and not self.cur_player.furo and self.cur_player.tehai.shanten() == 0:
                    if self.on_richi(self.cur_player):
                        self.richi(self.cur_player)

                ron = False
                renchan = False
                minkan = False
                furo = False

                # ロン判定
                for player in self.players:
                    # 自身は判定しない
                    if player == self.cur_player:
                        continue

                    if self.check_ron(player, check_hai.hai, self.cur_player) and self.on_ron(player, check_hai.hai, self.cur_player):
                        self.ron(player, check_hai, self.cur_player)

                        ron = True
                        if self.jikaze(player) == 0:
                            renchan = True

                if ron:
                    return renchan, False

                # 副露判定
                for player in self.players:
                    # 自身は判定しない
                    if player == self.cur_player:
                        continue

                    # 明槓
                    for cur_hais in self.check_minkan(player, check_hai.hai):
                        if self.on_minkan(player, cur_hais, check_hai.hai, self.cur_player):
                            self.minkan(player, cur_hais, check_hai, self.cur_player)
                            minkan = True
                            break

                    if minkan:
                        break

                    # ポン
                    for cur_hais in self.check_pon(player, check_hai.hai):
                        if self.on_pon(player, cur_hais, check_hai.hai, self.cur_player):
                            self.pon(player, cur_hais, check_hai, self.cur_player)
                            furo = True
                            break

                    if furo:
                        break

                    # チー
                    if self.player_num >= 4 and self.cur_player.relative(player) == 1:
                        for cur_hais in self.check_chi(player, check_hai.hai):
                            if self.on_chi(player, cur_hais, check_hai.hai, self.cur_player):
                                self.chi(player, cur_hais, check_hai, self.cur_player)
                                furo = True
                                break

                    if furo:
                        break

                if minkan or not furo:
                    break

            if not minkan:
                self.next_player()

        self.ryukyoku()
        return self.players[self.kyoku].tehai.shanten() == 0, True

    # 次の局へ
    def next_kyoku(self, renchan, ryukyoku):
        # 局を更新
        if not renchan:
            self.kyoku += 1
            if self.kyoku >= self.player_num:
                self.kyoku = 0
                self.bakaze += 1

        # 本場
        if renchan or ryukyoku:
            self.honba += 1
        else:
            self.honba = 0

        # 供託
        if ryukyoku:
            for player in self.players:
                if player.richi:
                    self.kyotaku += 1
        else:
            self.kyotaku = 0

        # リセット
        self.change_player(self.kyoku)
        self.yama = Yama(self.hai_set)
        self.dora_hais = [self.yama.doras[0]]
        self.uradora_hais = [self.yama.uradoras[0]]
        self.doras = [self.dora_kind(self.dora_hais[0])]
        self.uradoras = [self.dora_kind(self.uradora_hais[0])]

        for player in self.players:
            player.reset()

        self.update_game_reader()

    # 次のプレイヤーへ
    def next_player(self):
        self.change_player((self.turn + 1) % self.player_num)

    # プレイヤーのツモ順を変更
    def change_player(self, chicha):
        self.turn = chicha
        self.cur_player = self.players[self.turn]
        self.update_game_reader()

    # ドラ追加
    def add_dora(self):
        self.yama.add_dora()
        self.dora_hais.append(self.yama.doras[-1])
        self.uradora_hais.append(self.yama.uradoras[-1])
        self.doras.append(self.dora_kind(self.dora_hais[-1]))
        self.uradoras.append(self.dora_kind(self.uradora_hais[-1]))
        self.update_game_reader()

    # ゲームリーダーを更新
    def update_game_reader(self, open_players = [], uradora = False):
        self.game_reader.bakaze = self.bakaze
        self.game_reader.kyoku = self.kyoku
        self.game_reader.honba = self.honba
        self.game_reader.kyotaku = self.kyotaku

        self.game_reader.turn = self.turn
        self.game_reader.cur_player = self.game_reader.players[self.game_reader.turn]

        self.game_reader.yama_remain = self.yama.remain
        self.game_reader.dora_hais = self.dora_hais
        self.game_reader.doras = self.doras

        if uradora:
            self.game_reader.uradora_hais = self.uradora_hais
            self.game_reader.uradoras = self.uradoras
        else:
            self.game_reader.uradora_hais = None
            self.game_reader.uradoras = None

        for i in range(self.player_num):
            player = self.game_reader.players[i]
            player_org = self.players[i]

            player.name = player_org.name
            player.point = player_org.point

            if player_org in open_players:
                player.tehai.hais = player_org.tehai.hais
                player.tehai.tsumo_hai = player_org.tehai.tsumo_hai
            else:
                player.tehai.hais = None
                player.tehai.tsumo_hai = None

            player.tehai.furos = player_org.tehai.furos
            player.tehai.hai_num = player_org.tehai.hai_num
            player.tehai.exist_tsumo_hai = player_org.tehai.tsumo_hai is not None
            player.kawa = player_org.kawa
            player.richi = player_org.richi
            player.furo = player_org.furo
            player.ippatsu = player_org.ippatsu

    # 役
    def yaku(self, player, is_tsumo, agari_hai=None, chankan=False):
        # 手牌
        tile_strs = [""] * 4
        win_tile_strs = [""] * 4

        for hai in player.tehai.hais:
            tile_strs[hai.kind] += "r" if hai.red else str(hai.num)

        for furo in player.tehai.furos:
            for hai in furo.hais:
                tile_strs[hai.kind] += "r" if hai.red else str(hai.num)

            if furo.kind == FuroKind.ANKAN or furo.kind == FuroKind.MINKAN or furo.kind == FuroKind.KAKAN:
                tile_strs[furo.hais[0].kind] = tile_strs[furo.hais[0].kind][:-1]

        if is_tsumo:
            hai = player.tehai.tsumo_hai
            tile_strs[hai.kind] += "r" if hai.red else str(hai.num)
            win_tile_strs[hai.kind] += "r" if hai.red else str(hai.num)
        else:
            tile_strs[agari_hai.kind] += "r" if agari_hai.red else str(agari_hai.num)
            win_tile_strs[agari_hai.kind] += "r" if agari_hai.red else str(agari_hai.num)

        tiles = TilesConverter.string_to_136_array(tile_strs[0], tile_strs[1], tile_strs[2], tile_strs[3], True)
        win_tile = TilesConverter.string_to_136_array(win_tile_strs[0], win_tile_strs[1], win_tile_strs[2], win_tile_strs[3], True)[0]

        # 副露
        FURO_MELD = {
            FuroKind.PON: Meld.PON,
            FuroKind.CHI: Meld.CHI,
            FuroKind.ANKAN: Meld.KAN,
            FuroKind.MINKAN: Meld.KAN,
            FuroKind.KAKAN: Meld.CHANKAN
        }

        melds = []

        for furo in player.tehai.furos:
            furo_strs = [""] * 4

            for hai in furo.hais:
                furo_strs[hai.kind] += "r" if hai.red else str(hai.num)

            meld_tiles = TilesConverter.string_to_136_array(furo_strs[0], furo_strs[1], furo_strs[2], furo_strs[3], True)
            melds.append(Meld(FURO_MELD[furo.kind], meld_tiles, furo.kind != FuroKind.ANKAN))

        # ドラ
        dora_indicators = []

        for hai in self.dora_hais:
            dora_strs = [""] * 4
            dora_strs[hai.kind] += "r" if hai.red else str(hai.num)

            dora_tile = TilesConverter.string_to_136_array(dora_strs[0], dora_strs[1], dora_strs[2], dora_strs[3], True)[0]
            dora_indicators.append(dora_tile)

        if player.richi:
            for hai in self.uradora_hais:
                dora_strs = [""] * 4
                dora_strs[hai.kind] += "r" if hai.red else str(hai.num)

                dora_tile = TilesConverter.string_to_136_array(dora_strs[0], dora_strs[1], dora_strs[2], dora_strs[3], True)[0]
                dora_indicators.append(dora_tile)

        # 設定
        KAZE_WIND = [EAST, SOUTH, WEST, NORTH]

        config = HandConfig(
            is_tsumo=is_tsumo,
            is_riichi=player.richi,
            is_ippatsu=player.ippatsu,
            is_rinshan=player.rinshan,
            is_chankan=chankan,
            is_haitei=agari_hai is None and self.yama.remain == 0,
            is_houtei=agari_hai is not None and self.yama.remain == 0,
            is_daburu_riichi=len(player.kawa.hais) > 0 and player.kawa.hais[0].richi,
            is_tenhou=agari_hai is None and self.jikaze(player) == 0 and len(player.kawa.hais) == 0,
            is_renhou=agari_hai is not None and len(player.kawa.hais) == 0,
            is_chiihou=agari_hai is None and self.jikaze(player) != 0 and len(player.kawa.hais) == 0,
            player_wind=KAZE_WIND[self.jikaze(player)],
            round_wind=KAZE_WIND[self.bakaze],
            options=OptionalRules(has_aka_dora=True)
        )

        return self.calculator.estimate_hand_value(tiles, win_tile, melds, dora_indicators, config)

    # ドラ表示牌に対応するドラ
    def dora_kind(self, hai):
        # 数牌
        if hai.kind <= 2:
            next_num = hai.num

            while True:
                next_num += 1
                if (next_num > 9):
                    next_num = 1

                if Hai(hai.kind, next_num) in self.hai_set or Hai(hai.kind, next_num, True) in self.hai_set:
                    return (hai.kind, next_num)

        # 東南西北
        elif 1 <= hai.num <= 4:
            next_num = hai.num + 1
            if (next_num > 4):
                next_num = 1

            return (hai.kind, next_num)

        # 白發中
        elif 5 <= hai.num <= 7:
            next_num = hai.num + 1
            if (next_num > 7):
                next_num = 5

            return (hai.kind, next_num)

    # 局を表す文字列
    def kyoku_name(self):
        KAZE_NAME = ["東", "南", "西", "北"]
        return "{}{}局".format(KAZE_NAME[self.bakaze], self.kyoku + 1)

    # 自風
    def jikaze(self, player):
        return (player.chicha - self.kyoku) % self.player_num

    # 配牌
    def haipai(self, player):
        player.tehai.append([self.yama.pop() for i in range(13)])
        player.tehai.sort()
        self.update_game_reader()

    # ツモ
    def tsumo_pop(self, player):
        player.tehai.tsumo(self.yama.pop())
        self.update_game_reader()

    # 打牌
    def dahai(self, player, index):
        tsumogiri = (index == -1 or index == player.tehai.hai_num - 1)
        player.kawa.append(player.tehai.pop(index), tsumogiri)
        player.tehai.sort()

        player.ippatsu = False
        player.rinshan = False

        self.update_game_reader()
        return player.kawa.hais[-1]

    # リーチ
    def richi(self, player):
        player.richi = True
        player.ippatsu = True
        player.kawa.hais[-1].richi = True
        self.update_game_reader()

    # ツモ
    def tsumo(self, player):
        yaku = self.yaku(player, True)

        # 点数移動
        for cur_player in self.players:
            if cur_player == player:
                continue

            change_point = yaku.cost["main" if self.jikaze(cur_player) == 0 else "additional"] + self.honba * 100
            player.point += change_point
            cur_player.point -= change_point

            # リーチ棒
            if cur_player.richi:
                player.point += 1000
                cur_player.point -= 1000

        # 供託
        player.point += self.kyotaku * 1000

        # 表示
        print("{}：ツモ".format(player.name))
        print(yaku.yaku)
        print("{}翻 {}符".format(yaku.han, yaku.fu))

        self.update_game_reader([player], player.richi)

    # ロン
    def ron(self, player, target, whose, chankan = False):
        if chankan:
            hai = target
        else:
            hai = target.hai
            target.hoju = True

        player.tehai.tsumo(hai)
        yaku = self.yaku(player, False, hai, chankan)

        # 点数移動
        change_point = yaku.cost["main"] + self.honba * 300
        player.point += change_point
        whose.point -= change_point

        # リーチ棒
        for cur_player in self.players:
            if cur_player != player and cur_player.richi:
                player.point += 1000
                cur_player.point -= 1000

        # 供託
        player.point += self.kyotaku * 1000

        # 表示
        print("{}→{}：ロン".format(whose.name, player.name))
        print(yaku.yaku)
        print("{}翻 {}符".format(yaku.han, yaku.fu))

        self.update_game_reader([player], player.richi)

    # 暗槓
    def ankan(self, player, hais):
        player.tehai.ankan(hais)
        player.rinshan = True

        self.add_dora()

        for player in self.players:
            player.ippatsu = False

        self.update_game_reader()

    # 加槓
    def kakan(self, player, hai):
        player.tehai.kakan(hai)
        player.rinshan = True

        self.add_dora()

        for player in self.players:
            player.ippatsu = False

        self.update_game_reader()

    # 明槓
    def minkan(self, player, hais, target, whose):
        player.tehai.minkan(hais, target.hai, player.relative(whose))
        player.furo = True
        player.rinshan = True
        target.furo = True

        self.change_player(player.chicha)
        self.add_dora()

        for player in self.players:
            player.ippatsu = False

        self.update_game_reader()

    # ポン
    def pon(self, player, hais, target, whose):
        player.tehai.pon(hais, target.hai, player.relative(whose))
        player.furo = True
        target.furo = True

        self.change_player(player.chicha)

        for player in self.players:
            player.ippatsu = False

        self.update_game_reader()

    # チー
    def chi(self, player, hais, target, whose):
        player.tehai.chi(hais, target.hai, player.relative(whose))
        player.furo = True
        target.furo = True

        self.change_player(player.chicha)

        for player in self.players:
            player.ippatsu = False

        self.update_game_reader()

    # 流局
    def ryukyoku(self):
        open_players = []

        tenpai_cnt = 0

        for player in self.players:
            if player.tehai.shanten() == 0:
                tenpai_cnt += 1

        for player in self.players:
            # 点数移動
            if tenpai_cnt != 0 and tenpai_cnt != self.player_num:
                if player.tehai.shanten() == 0:
                    player.point += int(3000 / tenpai_cnt)
                else:
                    player.point -= int(3000 / (self.player_num - tenpai_cnt))

            # 供託
            if player.richi:
                player.point -= 1000

            if player.tehai.shanten() == 0:
                print("{}：テンパイ".format(player.name))
                open_players.append(player)
            else:
                print("{}：ノーテン".format(player.name))

        self.update_game_reader(open_players)

    # ツモチェック
    def check_tsumo(self, player):
        if player.tehai.shanten() != -1:
            return False

        yaku = self.yaku(player, True)
        return yaku.cost is not None

    # ロンチェック
    def check_ron(self, player, target, whose):
        player.tehai.tsumo(target)
        cur_shanten = player.tehai.shanten()
        player.tehai.pop()

        if cur_shanten != -1:
            return False

        yaku = self.yaku(player, False, target)
        return yaku.cost is not None

    # 暗槓チェック
    def check_ankan(self, player):
        return player.tehai.ankan_able()

    # 加槓チェック
    def check_kakan(self, player):
        return player.tehai.kakan_able()

    # 明槓チェック
    def check_minkan(self, player, target):
        if player.richi:
            return []

        return player.tehai.minkan_able(target)

    # ポンチェック
    def check_pon(self, player, target):
        if player.richi:
            return []

        return player.tehai.pon_able(target)

    # チーチェック
    def check_chi(self, player, target):
        if player.richi:
            return []

        return player.tehai.chi_able(target)

    # 選択
    def on_dahai(self, player):
        return player.on_dahai()

    # 立直するか
    def on_richi(self, player):
        return player.on_richi()

    # ツモ和了するか
    def on_tsumo(self, player):
        return player.on_tsumo()

    # ロン和了するか
    def on_ron(self, player, target, whose):
        return player.on_ron(target, whose.chicha)

    # 暗槓するか
    def on_ankan(self, player, target):
        return player.on_ankan(target)

    # 明槓するか
    def on_minkan(self, player, hais, target, whose):
        return player.on_minkan(hais, target, whose.chicha)

    # 加槓するか
    def on_kakan(self, player, target):
        return player.on_kakan(target)

    # ポンするか
    def on_pon(self, player, hais, target, whose):
        return player.on_pon(hais, target, whose.chicha)

    # チーするか
    def on_chi(self, player, hais, target, whose):
        return player.on_chi(hais, target, whose.chicha)

# 山
class Yama():
    def __init__(self, hai_set):
        self.hais = hai_set[:]
        random.shuffle(self.hais)
        self.remain = len(self.hais) - 14
        self.doras = []
        self.uradoras = []
        self.add_dora()

    # 取り出し
    def pop(self):
        self.remain -= 1
        return self.hais.pop()

    # ドラを増やす
    def add_dora(self):
        self.doras.append(self.hais[len(self.doras) * 2])
        self.uradoras.append(self.hais[len(self.uradoras) * 2 + 1])
