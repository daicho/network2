import copy
from .. import player

# 手なりAI
class Tenari(player.Player):
    def __init__(self):
        super().__init__()
        self.name = "Tenari"

    # 選択
    def on_dahai(self):
        select_index = -1
        effect_max = 0
        cur_shanten = self.tehai.shanten()

        # 残っている牌
        remain_hai = self.game.hai_set[:]

        # 自身の手牌
        for hai in self.tehai.hais:
            remain_hai.remove(hai)

        for player in self.game.players:
            # 副露
            for furo in player.tehai.furos:
                for hai in furo.hais:
                    remain_hai.remove(hai)

            # 河
            for kawa_hai in player.kawa.hais:
                if not kawa_hai.furo:
                    remain_hai.remove(kawa_hai.hai)

        # ドラ
        for dora in self.game.dora_hais:
            remain_hai.remove(dora)

        for i in range(self.tehai.hai_num):
            # 1枚ずつ切ってみる
            pop_hai = self.tehai.pop(i)

            # シャンテン数が進むなら
            if self.tehai.shanten() <= cur_shanten:
                effect_count = 0

                # 残り全ての牌をツモってみる
                for hai in remain_hai:
                    # 有効牌の数をカウント
                    self.tehai.tsumo(hai)
                    if self.tehai.shanten() < cur_shanten:
                        effect_count += 1
                    self.tehai.pop()

                # 有効牌が一番多い牌を選択
                if effect_count >= effect_max:
                    effect_max = effect_count
                    select_index = i

            self.tehai.insert(i, pop_hai)

        return select_index

    # 立直するか
    def on_richi(self):
        return True

    # ツモ和了するか
    def on_tsumo(self):
        return True

    # ロン和了するか
    def on_ron(self, target, whose):
        return True

    # 暗槓するか
    def on_ankan(self, target):
        # シャンテン数が下がらないなら暗槓
        temp_tehai = copy.deepcopy(self.tehai)
        temp_tehai.ankan(target)
        return temp_tehai.shanten() <= self.tehai.shanten()

    # 明槓するか
    def on_minkan(self, hais, target, whose):
        # 門前だったら明槓しない
        if not self.furo:
            return False

        # シャンテン数が下がらないなら明槓
        temp_tehai = copy.deepcopy(self.tehai)
        temp_tehai.minkan(hais, target, 1)
        return temp_tehai.shanten() <= self.tehai.shanten()

    # 加槓するか
    def on_kakan(self, target):
        # シャンテン数が下がらないなら加槓
        temp_tehai = copy.deepcopy(self.tehai)
        temp_tehai.kakan(target)
        return temp_tehai.shanten() <= self.tehai.shanten()

    # ポンするか
    def on_pon(self, hais, target, whose):
        # シャンテン数が進むならポン
        temp_tehai = copy.deepcopy(self.tehai)
        temp_tehai.pon(hais, target, 1)
        return temp_tehai.shanten() < self.tehai.shanten()

    # チーするか
    def on_chi(self, hais, target, whose):
        # シャンテン数が進むならチー
        temp_tehai = copy.deepcopy(self.tehai)
        temp_tehai.chi(hais, target, 1)
        return temp_tehai.shanten() < self.tehai.shanten()

# 面子手のみ
class Menzen(Tenari):
    def __init__(self):
        super().__init__()
        self.name = "AI"

    def on_minkan(self, hais, target, whose):
        return False

    def on_pon(self, hais, target, whose):
        return False

    def on_chi(self, hais, target, whose):
        return False
