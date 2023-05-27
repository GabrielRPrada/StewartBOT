import time
import os

import discord
from discord import app_commands

import asyncio

import latex2png


intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

invite_url = ""

@tree.command(name = "ping", description = "Teste se o bot te ouve")
async def ping(interaction):
    await interaction.response.send_message("Pong! ")

@tree.command(name="convidar", description="Gera um link para convidar o bot para o teu servidor")
async def invite(interaction):
    await interaction.response.send_message(invite_url)

async def latex_async(latex, filename, dpi):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, latex2png.latex2png, latex, filename, dpi)
    return filename

@tree.command(name="latex", description="Compila um Latex para uma imagem png")
async def latex(interaction, latex: str, dpi: int=500):
    fn = "temp/" + str(int(time.time()))+".png"
    fn = await latex_async(latex, fn, dpi)
    try:
        f = open(fn, "rb")
        df = discord.File(f)
        await interaction.response.send_message(file=df)
    finally:
        f.close()
        os.remove(fn)

@client.event
async def on_ready():
    await tree.sync()
    global invite_url
    invite_url = discord.utils.oauth_url(client._application.id,permissions=discord.Permissions(35840))
    print("Ready!")
    print(invite_url)

@client.event
async def on_command_error(interaction,err):
    await interaction.response.send_message(f"Opa, algo deu errado! `{err}`\n\nSerá que foi um erro meu? Para dúvidas, fale com Gabriel (refrigerador#8298 no discord) ou crie uma issue: https://github.com/GabrielRPrada/StewartBOT/issues/new/choose")
    

tokenf = open("token.txt", "r")
token = tokenf.readline()
tokenf.close()

client.run(token)
