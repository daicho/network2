import time
import random
import copy
import pickle
import socket

import mjgame.system as mj
import mjgame.players as mp

# 通信する処理の種類
class EventKind():
    UPDATE   = b"upd"
    DAHAI    = b"dah"
    RICHI    = b"ric"
    TSUMO    = b"tmo"
    RON      = b"ron"
    ANKAN    = b"aka"
    MINKAN   = b"mka"
    KAKAN    = b"kka"
    PON      = b"pon"
    CHI      = b"chi"
    RESULT   = b"res"
    COMPLETE = b"com"
    OVER     = b"ovr"
    END      = b"end"

# サーバーサイド
class GameServer(mj.Game):
    def __init__(self, hai_set, players, start_point):
        super().__init__(hai_set, players, start_point)

        self.conns = {}
        self.addrs = {}

    # 接続が確率されるまで待機
    def connect(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # サーバーの設定
            s.bind(("0.0.0.0", 50005))
            s.listen(self.player_num)

            num = 1

            for i in range(self.player_num):
                player = self.players[i]

                if self.players[i].__class__.__name__ != "Human":
                    continue

                # 接続待機
                print("No. {} Player: Waiting...".format(num))
                conn, addr = s.accept()

                # リストに追加
                self.conns[i] = conn
                self.addrs[i] = addr
                
                # 名前を受信
                player_name = self.receive(player)
                player.name = player_name.decode()

                print("No. {} Player: Connected".format(num))
                print("Name: {}".format(player.name))

                num += 1

    # 受信
    def receive(self, player):
        conn = self.conns[player.chicha]
        recv_data = b""

        # データが終端に達するまで受信
        while True:
            data = conn.recv(4096)
            recv_data += data

            if recv_data[-3:] == EventKind.END:
                break

        return recv_data[:-3]

    # 選択を要求
    def request(self, player, event_kind):
        conn = self.conns[player.chicha]
        conn.sendall(event_kind + EventKind.END)
        return self.receive(player)

    # ゲームリーダーを更新
    def update_game_reader(self, open_players = [], uradora = False):
        super().update_game_reader(open_players, uradora)

        # 全てのクライアントにゲームリーダーを送信
        for i in range(self.player_num):
            player = self.players[i]

            if player.__class__.__name__ != "Human":
                continue

            send_data = pickle.dumps(self.players[i])
            self.conns[i].sendall(EventKind.UPDATE + send_data + EventKind.END)

        # 全てのクライアントから応答があるまで待機
        for i in range(self.player_num):
            player = self.players[i]

            if player.__class__.__name__ != "Human":
                continue

            self.receive(player)

    # ゲーム開始
    def start(self):
        super().start()

        # 終局
        for i in range(self.player_num):
            player = self.players[i]

            if player.__class__.__name__ != "Human":
                continue

            self.conns[i].sendall(EventKind.OVER + EventKind.END)

    # 局開始
    def start_kyoku(self):
        renchan, ryukyoku = super().start_kyoku()

        # 終局
        for i in range(self.player_num):
            player = self.players[i]

            if player.__class__.__name__ != "Human":
                continue

            self.conns[i].sendall(EventKind.RESULT + EventKind.END)

        # 全てのクライアントから応答があるまで待機
        for i in range(self.player_num):
            player = self.players[i]

            if player.__class__.__name__ != "Human":
                continue

            self.receive(player)

        return renchan, ryukyoku

    # 選択
    def on_dahai(self, player):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.DAHAI)
            return int.from_bytes(data, "big", signed=True)
        else:
            return super().on_dahai(player)

    # 立直するか
    def on_richi(self, player):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.RICHI)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_richi(player)

    # ツモ和了するか
    def on_tsumo(self, player):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.TSUMO)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_tsumo(player)

    # ロン和了するか
    def on_ron(self, player, target, whose):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.RON)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_ron(player, target, whose)

    # 暗槓するか
    def on_ankan(self, player, target):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.ANKAN)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_ankan(player, target)

    # 明槓するか
    def on_minkan(self, player, hais, target, whose):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.MINKAN)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_minkan(player, hais, target, whose)

    # 加槓するか
    def on_kakan(self, player, target):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.KAKAN)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_kakan(player, target)

    # ポンするか
    def on_pon(self, player, hais, target, whose):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.PON)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_pon(player, hais, target, whose)

    # チーするか
    def on_chi(self, player, hais, target, whose):
        if player.__class__.__name__ == "Human":
            data = self.request(player, EventKind.CHI)
            return bool.from_bytes(data, "big", signed=True)
        else:
            return super().on_chi(player, hais, target, whose)

if __name__ == "__main__":
    # 牌をセット
    hai_set = []

    # 数牌
    for i in range(3):
        for j in range(1, 10):
            hai_set.extend(mj.Hai(i, j, j == 5 and k == 3) for k in range(4))

    # 字牌
    for i in range(1, 8):
        hai_set.extend(mj.Hai(3, i) for j in range(4))

    # プレイヤー
    players = [mp.Human(), mp.AI(), mp.Human(), mp.AI()]

    game = GameServer(hai_set, players, 25000)
    game.connect()
    game.start()
