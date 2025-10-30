import discord
from discord.ext import commands
import os
import random
from discord import option
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

# .envからトークンを読み込む
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class RecruitmentView(discord.ui.View):
    def __init__(self, author, game, max_participants, timeout=300):
        super().__init__(timeout=timeout)
        self.author = author
        self.game = game
        self.max_participants = max_participants
        self.participants = []

    @discord.ui.button(label="✅ 参加", style=discord.ButtonStyle.success)
    async def join(self, button: discord.ui.Button, interaction: discord.Interaction):
        user = interaction.user
        if user in self.participants:
            await interaction.response.send_message("すでに参加しています！", ephemeral=True)
        elif len(self.participants) >= self.max_participants:
            await interaction.response.send_message("定員に達しています。", ephemeral=True)
        else:
            self.participants.append(user)
            await interaction.response.send_message(f"{user.mention} が参加しました！（{len(self.participants)}/{self.max_participants}）")

    @discord.ui.button(label="🛑 取り消し", style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("この募集を取り消せるのは作成者だけです。", ephemeral=True)
        else:
            await interaction.message.edit(content="❌ 募集は取り消されました。", embed=None, view=None)
            self.stop()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.slash_command(name="募集", description="ゲームの募集を開始します")
async def 募集(ctx, ゲーム: str, 時間: str, 募集人数: int):
    embed = discord.Embed(
        title=f"{ゲーム} の募集",
        description=f"{ctx.author.mention} が {時間} に {ゲーム} を一緒に遊ぶ人を募集！\n定員: {募集人数}人",
        color=discord.Color.green()
    )
    view = RecruitmentView(ctx.author, ゲーム, 募集人数)
    await ctx.respond(embed=embed, view=view)

# ---------------------------
# ✅ 投票機能（5個まで）
# ---------------------------

class VoteView(discord.ui.View):
    def __init__(self, options):
        super().__init__(timeout=None)
        self.votes = {opt: 0 for opt in options}
        self.options = options
        self.message = None
        for opt in options:
            self.add_item(VoteButton(opt, self))

    async def update_message(self):
        description = "\n".join([f"**{opt}**: {count}票" for opt, count in self.votes.items()])
        embed = discord.Embed(title="🗳️ 投票中", description=description, color=discord.Color.blurple())
        if self.message:
            await self.message.edit(embed=embed, view=self)

class VoteButton(discord.ui.Button):
    def __init__(self, label, view):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.view_obj = view

    async def callback(self, interaction: discord.Interaction):
        self.view_obj.votes[self.label] += 1
        await interaction.response.send_message(f"✅ {interaction.user.mention} が **{self.label}** に投票しました！", ephemeral=True)
        await self.view_obj.update_message()

@bot.slash_command(name="投票", description="最大5個の選択肢で投票を作成します")
@option("お題", description="投票のお題")
@option("選択肢1", description="1つ目の選択肢（必須）")
@option("選択肢2", description="2つ目の選択肢（必須）")
@option("選択肢3", description="3つ目の選択肢（任意）", required=False)
@option("選択肢4", description="4つ目の選択肢（任意）", required=False)
@option("選択肢5", description="5つ目の選択肢（任意）", required=False)
async def 投票(ctx, お題: str, 選択肢1: str, 選択肢2: str, 選択肢3=None, 選択肢4=None, 選択肢5=None):
    options = [選択肢1, 選択肢2]
    if 選択肢3: options.append(選択肢3)
    if 選択肢4: options.append(選択肢4)
    if 選択肢5: options.append(選択肢5)

    view = VoteView(options)
    embed = discord.Embed(
        title=f"🗳️ 投票：{お題}",
        description="\n".join([f"**{opt}**: 0票" for opt in options]),
        color=discord.Color.blurple()
    )
    message = await ctx.respond(embed=embed, view=view)
    view.message = await message.original_response()

# ----------------------------------------
# Replit / GitHub Keep-Alive（任意）
# ----------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()
bot.run(TOKEN)
