import asyncio
from datetime import datetime
import json
import os
import re

import discord
from discord import app_commands
from discord import ui

from bs4 import BeautifulSoup
import requests

import embed

# testa se a string é "vazia" (só tem espaços e \n?)
def string_nao_vazia(str):
    return re.search(r'[^ \n]', str)

class LeitorAgenda(object):
    def __init__(self):
        self.URL_AGENDA = "http://agendasjc.unifesp.br"
    
    def salvar_agenda(self):
        status_code = 0
        page = ""
        while status_code != 200:
            #if status_code > 0:
                #await asyncio.sleep(300)
            agenda_web = requests.get(self.URL_AGENDA)
            status_code = agenda_web.status_code
            page = agenda_web.content.decode("utf-8")
        
        horarios = []
        for i in range(8, 23):
            horarios.append(f"{i:02d}:00")
            horarios.append(f"{i:02d}:30")

        horarios.append("23:00")

        eventos = []
        soup = BeautifulSoup(page, 'html.parser')
        agendamentos = soup.find_all("table", class_="reservations")

        for table in agendamentos:
            header = table.find("thead")
            dia = header.find("td").decode_contents()
            body = table.find("tbody")
            slots = body.find_all("tr", class_="slots")
            for local in slots:
                sala = re.sub(" - (\d+ lugares|\dº andar)", "", local.find(class_="resourcename").text.strip("\n"))

                agendado = local.find_all("td", class_="slot")
                hora = 0
                for i, agendamento in enumerate(agendado):
                    texto = agendamento.decode_contents().replace("<br/>", "\n").strip()
                    duracao = int(agendamento["colspan"])
                    if texto:
                        dados = {"evento": texto, "sala": sala, "dia": dia, "início": horarios[hora], "fim": horarios[hora+duracao]}
                        eventos.append(dados)
                    hora += duracao
        
        dados = {
            "data": datetime.utcnow().strftime("%d/%m/%Y, %H:%M:%S"),
            "eventos": eventos
        }

        with open("agenda.json", "w", encoding="utf-8") as file:
            file.write(json.dumps(dados, ensure_ascii=False))

        
    def ler_agenda(self):
        update = True
        if os.path.isfile("agenda.json"):
            with open("agenda.json", "r", encoding="utf-8") as file:
                agenda_json = json.load(file)
                data_salva = datetime.strptime(agenda_json["data"], "%d/%m/%Y, %H:%M:%S")
                diff = datetime.utcnow() - data_salva
                if diff.total_seconds() <= 3600:
                    update = False
                    return agenda_json["eventos"]
                
        if update:
            self.salvar_agenda()
            return self.ler_agenda()


    def query_agenda(self, sala="", dia="", hora="", nome_evento=""):
        if not sala and not dia and not hora and not nome_evento:
            return []
        best_matches = []

        max_score = 0
        for evento in self.ler_agenda(): # lê todos os eventos na agenda, compara quais contêm os parâmetros que o usuário pediu
            score = 0
            if sala and (sala in evento["sala"]): score += 1
            if dia and (dia in evento["dia"]): score += 1
            if hora and (hora in evento["inicio"]): score += 1
            if nome_evento and string_nao_vazia(evento["evento"]) and (nome_evento in evento["evento"]): score += 1

            if score > max_score:
                max_score = score
                best_matches = [evento]
            elif score == max_score:
                best_matches.append(evento)
        
        return best_matches

LeitorAgenda().salvar_agenda()

def gerar_embed_agenda(evento):
    template = embed.gerar_embed_template("Agendamento", "http://agendasjc.unifesp.br/class/Web/view-schedule.php", f"**{evento['evento']}**")
    template.add_field(name="Dia", value=evento["dia"], inline=False)
    template.add_field(name="Sala", value=evento["sala"], inline=True)
    template.add_field(name="Início", value=evento["início"], inline=True)
    template.add_field(name="Término", value=evento["fim"], inline=True)
    return template

class AgendaView(ui.View):
    def __init__(self, query):
        super().__init__()
        self.index = 0
        self.query = query

    def atualizar_botoes(self):
        botao_ant = [x for x in self.children if x.custom_id == "agenda_ant"][0] # certeza que tem jeito melhor de fazer isso
        botao_prox = [x for x in self.children if x.custom_id == "agenda_prox"][0]

        botao_ant.disabled = self.index == 0
        
        botao_prox.disabled = self.index == len(self.query) - 1

    async def render_embed(self, idx, interaction: discord.Interaction):
            self.index = idx
            self.atualizar_botoes()
            await interaction.response.edit_message(embed=gerar_embed_agenda(self.query[self.index]), view=self)

    @ui.button(style=discord.ButtonStyle.blurple, label="◄", disabled=True, custom_id="agenda_ant")
    async def ant(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.render_embed(self.index - 1, interaction)
    
    @ui.button(style=discord.ButtonStyle.blurple, label="►", custom_id="agenda_prox")
    async def prox(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.render_embed(self.index + 1, interaction)
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        await self.message.edit(view=self)