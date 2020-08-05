from abc import ABCMeta, abstractmethod
from .core import *
from .tehai import Tehai

# プレイヤー
class Player(metaclass=ABCMeta):
    def __init__(self):
        self.name = ""
        self.reset()

    # 下家・対面・上家
    def relative(self, other):
        return (other.chicha - self.chicha) % 4

    # 初期設定
    def setup(self, game, chicha, start_point):
        self.game = game
        self.chicha = chicha
        self.point = start_point

    # 手牌・河をリセット
    def reset(self):
        self.tehai = Tehai()
        self.kawa = Kawa()
        self.richi = False
        self.furo = False
        self.ippatsu = False
        self.rinshan = False

    # 選択
    @abstractmethod
    def on_dahai(self):
        pass

    # 立直するか
    @abstractmethod
    def on_richi(self):
        pass

    # ツモ和了するか
    @abstractmethod
    def on_tsumo(self):
        pass

    # ロン和了するか
    @abstractmethod
    def on_ron(self, target, whose):
        pass

    # 暗槓するか
    @abstractmethod
    def on_ankan(self, target):
        pass

    # 明槓するか
    @abstractmethod
    def on_minkan(self, hais, target, whose):
        pass

    # 加槓するか
    @abstractmethod
    def on_kakan(self, target):
        pass

    # ポンするか
    @abstractmethod
    def on_pon(self, hais, target, whose):
        pass

    # チーするか
    @abstractmethod
    def on_chi(self, hais, target, whose):
        pass
