from .. import system as mj

# 多田AI
class TadaAi(mj.Player):
    # 選択
    def on_dahai(self):
        return 13

    # ツモ和了
    def on_tsumo(self):
        return True

    # ロン和了
    def on_ron(self, target, whose):
        return True

    # 立直
    def on_richi(self):
        return True

    # 暗槓
    def on_ankan(self, target):
        return False

    # 明槓
    def on_minkan(self, hais, target, whose):
        return False

    # 加槓
    def on_kakan(self, target):
        return False

    # ポン
    def on_pon(self, hais, target, whose):
        return False

    # チー
    def on_chi(self, hais, target, whose):
        return False
