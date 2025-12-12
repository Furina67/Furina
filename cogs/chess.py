import io
import asyncio
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord import app_commands
import chess
import chess.pgn
import chess.svg
import cairosvg
import traceback

INITIAL_TIME_MS = 600000
SVG_BOARD_SIZE = 700


def render(board: chess.Board) -> discord.File:
    svg = chess.svg.board(
        board,
        size=SVG_BOARD_SIZE,
        coordinates=True,
        colors={"light": "#f0d9b5", "dark": "#b58863"}
    )
    png = cairosvg.svg2png(bytestring=svg.encode())
    buf = io.BytesIO(png)
    buf.seek(0)
    return discord.File(buf, filename="board.png")


def ms_to_str(ms: int) -> str:
    ms = max(0, ms)
    s = (ms + 500) // 1000
    return f"{s//60:02d}:{s%60:02d}"


async def safe_end_game(manager, game, reason, winner_id=None, loser_id=None):
    files = []
    try:
        buf = io.StringIO()
        game["pgn_game"].accept(chess.pgn.FileExporter(buf))
        files.append(discord.File(io.BytesIO(buf.getvalue().encode()), filename="game.pgn"))
    except Exception:
        pass

    try:
        files.append(render(game["board"]))
    except Exception:
        pass

    if winner_id:
        text = f"Game Over — <@{winner_id}> won ({reason})"
    else:
        text = f"Game Over — Draw ({reason})"

    chan = manager.bot.get_channel(game["channel_id"])
    if chan:
        try:
            starter = await chan.fetch_message(game["starter_msg_id"])
            try:
                await starter.edit(content=text, view=None, attachments=[])
            except Exception:
                pass
        except Exception:
            pass

        try:
            await chan.send(content=text, files=files)
        except Exception:
            pass

    manager.cleanup(game["starter_msg_id"])


class ChessManager:
    def __init__(self, bot):
        self.bot = bot
        self.games = {}
        self.active = set()

    async def start(self, interaction: discord.Interaction, challenger: discord.Member, opponent: discord.Member):
        if opponent.bot:
            return await interaction.response.send_message("You cannot challenge a bot.", ephemeral=True)
        if challenger.id == opponent.id:
            return await interaction.response.send_message("You cannot challenge yourself.", ephemeral=True)
        if challenger.id in self.active or opponent.id in self.active:
            return await interaction.response.send_message("A player is already in a game.", ephemeral=True)

        view = ChallengeView(challenger, opponent, self)
        await interaction.response.send_message(f"{opponent.mention}, challenge from {challenger.mention}", view=view)
        try:
            view.msg = await interaction.original_response()
        except Exception:
            view.msg = None

    def cleanup(self, starter_msg_id):
        g = self.games.pop(starter_msg_id, None)
        if g:
            self.active.discard(g.get("w"))
            self.active.discard(g.get("b"))


class ChallengeView(discord.ui.View):
    def __init__(self, challenger, opponent, manager: ChessManager):
        super().__init__(timeout=300)
        self.c = challenger
        self.o = opponent
        self.manager = manager
        self.msg = None

    async def on_timeout(self):
        if self.msg:
            try:
                await self.msg.edit(content="Challenge expired.", view=None)
            except Exception:
                pass
            self.manager.cleanup(self.msg.id)

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.o.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)

        self.manager.active.add(self.c.id)
        self.manager.active.add(self.o.id)

        board = chess.Board()
        pgn = chess.pgn.Game()
        pgn.headers["White"] = self.c.name
        pgn.headers["Black"] = self.o.name
        now = datetime.now(timezone.utc)

        game = {
            "board": board,
            "w": self.c.id,
            "b": self.o.id,
            "pgn_game": pgn,
            "pgn_node": pgn,
            "channel_id": interaction.channel_id,
            "starter_msg_id": None,
            "white_t": INITIAL_TIME_MS,
            "black_t": INITIAL_TIME_MS,
            "last": now,
            "last_action": now,
            "moves_made": 0,
            "early_abort_enabled": True,
            "draw_offer": None
        }

        await interaction.response.defer()

        try:
            file = render(board)
            view = BoardView(game, self.manager, None)
            starter = await interaction.followup.send(
                content=(f"Game start — White: {self.c.mention}\n"
                         f"White {ms_to_str(game['white_t'])} | Black {ms_to_str(game['black_t'])}"),
                file=file,
                view=view
            )
            game["starter_msg_id"] = starter.id
            view.starter_id = starter.id
            self.manager.games[starter.id] = game
        except Exception as e:
            try:
                await interaction.followup.send(f"Failed to start: `{e}`", ephemeral=True)
            except Exception:
                pass
            self.manager.active.discard(self.c.id)
            self.manager.active.discard(self.o.id)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.o.id:
            return await interaction.response.send_message("Not for you.", ephemeral=True)
        await interaction.response.edit_message(content=f"{self.o.mention} declined.", view=None)


class DrawBtn(discord.ui.Button):
    def __init__(self, game, manager):
        super().__init__(label="Draw", style=discord.ButtonStyle.secondary)
        self.game = game
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        try:
            u = interaction.user.id
            if u not in (self.game["w"], self.game["b"]):
                return await interaction.response.send_message("Not your game.", ephemeral=True)
            offered = self.game.get("draw_offer")
            opp = self.game["b"] if u == self.game["w"] else self.game["w"]
            if offered is None:
                self.game["draw_offer"] = u
                return await interaction.response.send_message(f"Draw offered to <@{opp}>.", ephemeral=True)
            if offered == u:
                return await interaction.response.send_message("Already offered.", ephemeral=True)
            await safe_end_game(self.manager, self.game, "Draw")
            return await interaction.response.send_message("Draw accepted.", ephemeral=True)
        except Exception:
            traceback.print_exc()
            return await interaction.response.send_message("Error.", ephemeral=True)


class ResignBtn(discord.ui.Button):
    def __init__(self, game, manager):
        super().__init__(label="Resign", style=discord.ButtonStyle.red)
        self.game = game
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        try:
            u = interaction.user.id
            if u not in (self.game["w"], self.game["b"]):
                return await interaction.response.send_message("Not your game.", ephemeral=True)
            winner = self.game["b"] if u == self.game["w"] else self.game["w"]
            await safe_end_game(self.manager, self.game, "Resigned", winner, u)
            return await interaction.response.send_message("You resigned.", ephemeral=True)
        except Exception:
            traceback.print_exc()
            return await interaction.response.send_message("Error.", ephemeral=True)


class TimeBtn(discord.ui.Button):
    def __init__(self, game):
        super().__init__(label="Time", style=discord.ButtonStyle.secondary)
        self.game = game

    async def callback(self, interaction: discord.Interaction):
        try:
            return await interaction.response.send_message(
                f"White {ms_to_str(self.game['white_t'])}\nBlack {ms_to_str(self.game['black_t'])}",
                ephemeral=True
            )
        except Exception:
            traceback.print_exc()
            return await interaction.response.send_message("Error.", ephemeral=True)


class PieceBtn(discord.ui.Button):
    def __init__(self, sq, game, manager):
        super().__init__(label=chess.square_name(sq), style=discord.ButtonStyle.blurple)
        self.sq = sq
        self.game = game
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        try:
            b = self.game["board"]
            expected = self.game["w"] if b.turn else self.game["b"]
            if interaction.user.id != expected:
                return await interaction.response.send_message("Not your turn.", ephemeral=True)

            moves = [m for m in b.legal_moves if m.from_square == self.sq]
            if not moves:
                return await interaction.response.send_message("No legal moves.", ephemeral=True)

            await interaction.response.edit_message(
                content=f"Moves from {self.label}",
                view=MoveView(self.game, moves, self.manager, self.game["starter_msg_id"])
            )
        except Exception:
            traceback.print_exc()
            try:
                await interaction.response.send_message("Error.", ephemeral=True)
            except Exception:
                pass


class MoveBtn(discord.ui.Button):
    def __init__(self, game, move, manager):
        lbl = chess.square_name(move.to_square)
        if move.promotion:
            lbl += "=" + chess.piece_symbol(move.promotion).upper()
        super().__init__(label=lbl, style=discord.ButtonStyle.green)
        self.game = game
        self.move = move
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        try:
            b = self.game["board"]
            expected = self.game["w"] if b.turn else self.game["b"]
            if interaction.user.id != expected:
                return await interaction.response.send_message("Not your turn.", ephemeral=True)

            now = datetime.now(timezone.utc)
            elapsed = int((now - self.game["last"]).total_seconds() * 1000)
            if b.turn == chess.WHITE:
                self.game["white_t"] = max(0, self.game["white_t"] - elapsed)
            else:
                self.game["black_t"] = max(0, self.game["black_t"] - elapsed)
            self.game["last"] = now
            self.game["last_action"] = now

            if self.game["white_t"] <= 0 or self.game["black_t"] <= 0:
                winner = self.game["b"] if self.game["white_t"] <= 0 else self.game["w"]
                loser = self.game["w"] if winner == self.game["b"] else self.game["b"]
                await safe_end_game(self.manager, self.game, "Timeout", winner, loser)
                return await interaction.response.send_message("Timeout.", ephemeral=True)

            piece = b.piece_at(self.move.from_square)
            rank = chess.square_rank(self.move.to_square)
            if piece and piece.piece_type == chess.PAWN and rank in (0, 7) and not self.move.promotion:
                return await interaction.response.edit_message(
                    content="Choose promotion piece:",
                    view=PromotionView(self.game, self.move, self.manager)
                )

            b.push(self.move)
            try:
                self.game["pgn_node"] = self.game["pgn_node"].add_main_variation(self.move)
            except Exception:
                pass

            self.game["moves_made"] += 1
            if self.game["moves_made"] >= 2:
                self.game["early_abort_enabled"] = False

            if b.is_game_over(claim_draw=True):
                r = b.result(claim_draw=True)
                if r == "1-0":
                    await safe_end_game(self.manager, self.game, "Checkmate", self.game["w"], self.game["b"])
                    return await interaction.response.send_message("Checkmate.", ephemeral=True)
                if r == "0-1":
                    await safe_end_game(self.manager, self.game, "Checkmate", self.game["b"], self.game["w"])
                    return await interaction.response.send_message("Checkmate.", ephemeral=True)
                await safe_end_game(self.manager, self.game, "Draw")
                return await interaction.response.send_message("Draw.", ephemeral=True)

            next_player = self.game["w"] if b.turn else self.game["b"]

            try:
                try:
                    await interaction.message.edit(attachments=[])
                except Exception:
                    pass

                await interaction.response.edit_message(
                    content=(f"<@{next_player}> to move\n"
                             f"White {ms_to_str(self.game['white_t'])} | Black {ms_to_str(self.game['black_t'])}"),
                    attachments=[render(b)],
                    view=BoardView(self.game, self.manager, self.game["starter_msg_id"])
                )
            except Exception:
                traceback.print_exc()
                try:
                    await interaction.response.send_message("Failed to update board.", ephemeral=True)
                except Exception:
                    pass

        except Exception:
            traceback.print_exc()
            try:
                await interaction.response.send_message("Error.", ephemeral=True)
            except Exception:
                pass


class PromoBtn(discord.ui.Button):
    def __init__(self, pt, label, style, game, base_move, manager):
        super().__init__(label=label, style=style)
        self.pt = pt
        self.game = game
        self.base_move = base_move
        self.manager = manager

    async def callback(self, interaction: discord.Interaction):
        try:
            b = self.game["board"]
            expected = self.game["w"] if b.turn else self.game["b"]
            if interaction.user.id != expected:
                return await interaction.response.send_message("Not your turn.", ephemeral=True)

            now = datetime.now(timezone.utc)
            elapsed = int((now - self.game["last"]).total_seconds() * 1000)
            if b.turn == chess.WHITE:
                self.game["white_t"] = max(0, self.game["white_t"] - elapsed)
            else:
                self.game["black_t"] = max(0, self.game["black_t"] - elapsed)
            self.game["last"] = now
            self.game["last_action"] = now

            mv = chess.Move(self.base_move.from_square, self.base_move.to_square, promotion=self.pt)
            b.push(mv)
            try:
                self.game["pgn_node"] = self.game["pgn_node"].add_main_variation(mv)
            except Exception:
                pass

            self.game["moves_made"] += 1
            if self.game["moves_made"] >= 2:
                self.game["early_abort_enabled"] = False

            if b.is_game_over(claim_draw=True):
                r = b.result(claim_draw=True)
                if r == "1-0":
                    await safe_end_game(self.manager, self.game, "Checkmate", self.game["w"], self.game["b"])
                    return await interaction.response.send_message("Checkmate.", ephemeral=True)
                if r == "0-1":
                    await safe_end_game(self.manager, self.game, "Checkmate", self.game["b"], self.game["w"])
                    return await interaction.response.send_message("Checkmate.", ephemeral=True)
                await safe_end_game(self.manager, self.game, "Draw")
                return await interaction.response.send_message("Draw.", ephemeral=True)

            next_player = self.game["w"] if b.turn else self.game["b"]

            try:
                try:
                    await interaction.message.edit(attachments=[])
                except Exception:
                    pass

                await interaction.response.edit_message(
                    content=(f"<@{next_player}> to move\n"
                             f"White {ms_to_str(self.game['white_t'])} | Black {ms_to_str(self.game['black_t'])}"),
                    attachments=[render(b)],
                    view=BoardView(self.game, self.manager, self.game["starter_msg_id"])
                )
            except Exception:
                traceback.print_exc()
                try:
                    await interaction.response.send_message("Error.", ephemeral=True)
                except Exception:
                    pass

        except Exception:
            traceback.print_exc()
            try:
                await interaction.response.send_message("Error.", ephemeral=True)
            except Exception:
                pass


class MoveView(discord.ui.View):
    def __init__(self, game, moves, manager, starter_id):
        super().__init__(timeout=None)
        self.game = game
        self.manager = manager
        self.starter_id = starter_id
        for m in moves:
            self.add_item(MoveBtn(game, m, manager))
        self.add_item(DrawBtn(game, manager))
        self.add_item(TimeBtn(game))
        self.add_item(ResignBtn(game, manager))


class BoardView(discord.ui.View):
    def __init__(self, game, manager, starter_id):
        super().__init__(timeout=None)
        self.game = game
        self.manager = manager
        self.starter_id = starter_id

        b = game["board"]
        legal_from = sorted({m.from_square for m in b.legal_moves})
        count = 0
        for sq in legal_from:
            if count >= 20:
                break
            if not b.piece_at(sq):
                continue
            self.add_item(PieceBtn(sq, game, manager))
            count += 1

        self.add_item(DrawBtn(game, manager))
        self.add_item(TimeBtn(game))
        self.add_item(ResignBtn(game, manager))


class PromotionView(discord.ui.View):
    def __init__(self, game, base_move, manager):
        super().__init__(timeout=None)
        options = [
            (chess.QUEEN, "Queen", discord.ButtonStyle.green),
            (chess.ROOK, "Rook", discord.ButtonStyle.blurple),
            (chess.BISHOP, "Bishop", discord.ButtonStyle.secondary),
            (chess.KNIGHT, "Knight", discord.ButtonStyle.secondary)
        ]
        for pt, lbl, st in options:
            self.add_item(PromoBtn(pt, lbl, st, game, base_move, manager))


class ChessCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.manager = ChessManager(bot)
        bot.loop.create_task(self.inactivity_check())

    async def inactivity_check(self):
        await self.bot.wait_until_ready()
        while True:
            now = datetime.now(timezone.utc)
            for msgid, g in list(self.bot.manager.games.items()):
                try:
                    if g.get("early_abort_enabled") and (now - g.get("last_action", now)).total_seconds() > 120:
                        await safe_end_game(self.bot.manager, g, "Inactivity")
                except Exception:
                    traceback.print_exc()
            await asyncio.sleep(10)

    @commands.Cog.listener()
    async def on_ready(self):
        try:
            await self.bot.tree.sync()
        except Exception:
            pass

    @app_commands.command(name="chess", description="Challenge a player to chess.")
    async def chess_cmd(self, interaction: discord.Interaction, opponent: discord.Member):
        await self.bot.manager.start(interaction, interaction.user, opponent)


async def setup(bot):
    await bot.add_cog(ChessCog(bot))
