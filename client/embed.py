import discord
def gerar_embed_template(titulo,url,descricao):
    template = discord.Embed(color=discord.Color.from_str("#164E86"), title=titulo, url=url, description=descricao)
    template.set_author(name="StewartBOT")
    template.set_thumbnail(url="https://i.imgur.com/tPjBIKa.png") # placeholder, trocar por uma hospedada direito
    return template
