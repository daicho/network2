from .. import system as mj

# イーソー君
class Isokun(mj.Player):
    # 選択
    def on_dahai(self):
        return 13

    # ツモ和了するか
    def on_tsumo(self):
        return True

    # ロン和了するか
    def on_ron(self, target, whose):
        return True

    # 立直するか
    def on_richi(self):
        return True

    # 暗槓するか
    def on_ankan(self, target):
        return False

    # 明槓するか
    def on_minkan(self, hais, target, whose):
        return False

    # 加槓するか
    def on_kakan(self, target):
        return False

    # ポンするか
    def on_pon(self, hais, target, whose):
        return False

    # チーするか
    def on_chi(self, hais, target, whose):
        return False
