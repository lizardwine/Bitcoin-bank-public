import discord
import random
import models
from misc import bitcoin
from main import finish_lend
import threading
def prettify_num(num):
    return f"{num:,}"

class BlackJack(discord.ui.View):
    def __init__(self,the_data):
        super().__init__()
        self.value = None
        self.the_data = the_data
    @discord.ui.button(label="Another", style=discord.ButtonStyle.primary)
    async def another(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["user_id"]:
            return
        card = random.randint(1,11)
        if card == 11 and self.the_data["hand"] <= 10:
            self.the_data["hand"] += card
        elif card != 11:
            self.the_data["hand"] += card
        else:
            self.the_data["hand"] += 1
        
        if self.the_data["hand"] == 21:
            embed = interaction.message.embeds[0]
            embed.title = f"You Win! {bitcoin} {prettify_num(self.the_data['amount']*2)}"
            embed.set_field_at(0,name="Your hand:",value=str(self.the_data['hand']))
            player_bank = models.filter(models.User.user_id == self.the_data['user_id'],models.User).first()
            player_bank.cash += self.the_data['amount']*2
            models.save(player_bank)
            await interaction.response.edit_message(embed=embed)

            self.value = False
            self.stop()
        elif self.the_data['hand'] > 21:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0,name="Your hand:",value=str(self.the_data['hand']))
            embed.title = f"You Lost {bitcoin} {prettify_num(self.the_data['amount'])}"
            await interaction.response.edit_message(embed=embed)

            self.value = False
            self.stop()
        else:
            embed = interaction.message.embeds[0]
            embed.set_field_at(0,name=f"Your hand:",value=f"{self.the_data['hand']}")
            await interaction.response.edit_message(embed=embed)
    @discord.ui.button(label="Stay", style=discord.ButtonStyle.green)
    async def stay(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["user_id"]:
            return
        
        if self.the_data["dhand"] < self.the_data["hand"]:
            dealer_card = random.randint(3,11)
            if dealer_card == 11 and self.the_data["dhand"] <= 10:
                self.the_data["dhand"] += dealer_card
            elif dealer_card != 11:
                self.the_data["dhand"] += dealer_card
            else:
                self.the_data["dhand"] += 1
            while self.the_data["dhand"] < self.the_data["hand"]:
                dealer_card = random.randint(1,10)
                self.the_data["dhand"] += dealer_card


        #Player Wins
        if self.the_data["dhand"] > 21 or (self.the_data["hand"] > self.the_data["dhand"] and self.the_data["hand"] <= 21):
            embed = interaction.message.embeds[0]
            embed.title = f"You Win! {bitcoin} {prettify_num(self.the_data['amount']*2)}"
            embed.set_field_at(1,name=f"Dealer hand:",value=f"{self.the_data['dhand']}")
            player_bank = models.filter(models.User.user_id == self.the_data['user_id'],models.User).first()
            player_bank.cash += self.the_data['amount']*2
            models.save(player_bank)
        #Player Lost
        elif self.the_data["dhand"] > self.the_data["hand"] and self.the_data["dhand"] <= 21:
            embed = interaction.message.embeds[0]
            embed.title = f"You Lost {bitcoin} {prettify_num(self.the_data['amount'])}"
            embed.set_field_at(1,name=f"Dealer hand:",value=f"{self.the_data['dhand']}")
        #Draw
        elif self.the_data["dhand"] == self.the_data["hand"] and self.the_data["dhand"] <= 21 and self.the_data["hand"] <= 21:
            embed = interaction.message.embeds[0]
            embed.title = "Draw"
            embed.set_field_at(1,name=f"Dealer hand:",value=f"{self.the_data['dhand']}")
            player_bank = models.filter(models.User.user_id == self.the_data['user_id'],models.User).first()
            player_bank.cash += self.the_data['amount']
            models.save(player_bank)
        
        await interaction.response.edit_message(embed=embed)
        self.value = False
        self.stop()
        
class AcceptLend(discord.ui.View):
    def __init__(self,the_data):
        super().__init__()
        self.value = None
        self.the_data = the_data 
    @discord.ui.button(label="✔️", style=discord.ButtonStyle.green)
    async def accept(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["user_id"]:
            return
        threading.Thread(target=finish_lend, args= (self.the_data["author_id"],self.the_data["user_id"], self.the_data["amount"], self.the_data["timeout"])).start()
        user_bank = models.filter(models.User.user_id == self.the_data["user_id"], models.User).first()
        author_bank = models.filter(models.User.user_id == self.the_data["author_id"], models.User).first()
        author_bank.cash -= self.the_data["damount"]
        user_bank.cash += self.the_data["damount"]
        models.save(user_bank)
        models.save(author_bank)
        await interaction.response.send_message("Lend accepted successfully")
        self.value = False
        self.stop()
    @discord.ui.button(label="✖️", style=discord.ButtonStyle.red)
    async def decline(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["user_id"]:
            return
        await interaction.response.send_message("Lend declined successfully")
        self.value = False
        self.stop()
class LendView(discord.ui.View):
    def __init__(self,the_data):
        super().__init__()
        self.value = None
        self.the_data = the_data
    @discord.ui.select(
        placeholder="Choose a deadline",  
        options=[
            discord.SelectOption(label="6 hours", description="the lend will be fulfilled in 6 hours"),
            discord.SelectOption(label="12 hours",description="the lend will be fulfilled in 12 hours"),
            discord.SelectOption(label="24 hours",description="the lend will be fulfilled in 24 hours"),
            discord.SelectOption(label="3 days",description="the lend will be fulfilled in 3 days"),
            discord.SelectOption(label="5 days",description="the lend will be fulfilled in 5 days"),
            discord.SelectOption(label="7 days",description="the lend will be fulfilled in 7 days"),
        ], 
        disabled=False
        )
    async def time(self,interaction: discord.Interaction, select):
        if not interaction.user.id == self.the_data["author_id"]:
            return
        if select.values[0] == "6 hours":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] = 3600 * 6
        elif select.values[0] == "12 hours":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] = 3600 * 12
        elif select.values[0] == "24 hours":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] == 3600 * 24
        elif select.values[0] == "3 days":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] = 3600 * 24 * 3
        elif select.values[0] == "5 days":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] = 3600 * 24 * 5
        elif select.values[0] == "7 days":
            self.the_data["dtimeout"] = select.values[0]
            self.the_data["timeout"] = 3600 * 24 * 7
        await interaction.response.send_message(f"set deadline to {self.the_data['dtimeout']}")
    @discord.ui.button(label="Lend Interest 10%", style=discord.ButtonStyle.grey)
    async def lend10(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["author_id"]:
            return
        amount = int(self.the_data["amount"] * 1.10)
        timeout = self.the_data["timeout"] if "timeout" in self.the_data.keys() else 3600 * 12
        dtimeout = self.the_data["dtimeout"] if "dtimeout" in self.the_data.keys() else "12 hours"
        user_id = self.the_data["user_id"]
        embed = self.the_data["embed"]
        embed.description = f"do you want to accept a loan for {bitcoin} {prettify_num(self.the_data['amount'])} bitcoins to be repaid in {dtimeout} with a 10% interest rate?"
        await interaction.response.send_message(embed = embed,view= AcceptLend({
            "damount": self.the_data['amount'],
            "amount":amount,
            "timeout":timeout,
            "user_id":user_id,
            "author_id": self.the_data["author_id"],
        }))
        self.value = False
        self.stop()
    @discord.ui.button(label="Lend Interest 20%", style=discord.ButtonStyle.green)
    async def lend20(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["author_id"]:
            return
        amount = int(self.the_data["amount"] * 1.20)
        timeout = self.the_data["timeout"] if "timeout" in self.the_data.keys() else 3600 * 12
        dtimeout = self.the_data["dtimeout"] if "dtimeout" in self.the_data.keys() else "12 hours"
        user_id = self.the_data["user_id"]
        embed = self.the_data["embed"]
        embed.description = f"do you want to accept a loan for {bitcoin} {prettify_num(self.the_data['amount'])} bitcoins to be repaid in {dtimeout} with a 20% interest rate?"
        await interaction.response.send_message(embed = embed,view= AcceptLend({
            "damount": self.the_data['amount'],
            "amount":amount,
            "timeout":timeout,
            "user_id":user_id,
            "author_id": self.the_data["author_id"],
        }))
        self.value = False
        self.stop()
    @discord.ui.button(label="Lend Interest 30%", style=discord.ButtonStyle.red)
    async def lend30(self,interaction: discord.Interaction, button: discord.ui.button):
        if not interaction.user.id == self.the_data["author_id"]:
            return
        amount = int(self.the_data["amount"] * 1.30)
        timeout = self.the_data["timeout"] if "timeout" in self.the_data.keys() else 3600 * 12
        dtimeout = self.the_data["dtimeout"] if "dtimeout" in self.the_data.keys() else "12 hours"
        user_id = self.the_data["user_id"]
        embed = self.the_data["embed"]
        embed.description = f"do you want to accept a loan for {bitcoin} {prettify_num(self.the_data['amount'])} bitcoins to be repaid in {dtimeout} with a 30% interest rate?"
        await interaction.response.send_message(embed = embed,view= AcceptLend({
            "damount": self.the_data['amount'],
            "amount":amount,
            "timeout":timeout,
            "author_id": self.the_data["author_id"],
            "user_id":user_id,
        }))
        self.value = False
        self.stop()