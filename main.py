import math
import time
from typing import List
import discord
from sqlalchemy.orm.attributes import flag_modified
import random
from sqlalchemy import desc
import models
from views import *
import misc
from misc import bitcoin

def prettify_float_num(num):
    num = float(f"{num:.2f}")
    return f"{num:,}"
def prettify_num(num):
    return f"{num:,}"

#comentario para hacer una prueba


intents = discord.Intents.all() # set intents to all
bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

guild_id = YOUR-SERVER-ID-HERE
bancario_id = YOUR-MANAGER-ROLE-ID-HERE
fisher_id = YOUR-FISHER-ROLE-ID-HERE

@bot.event
async def on_member_remove(member: discord.guild.Member):
    user_id = member.id
    models.filter(models.User.user_id == user_id, models.User).delete()
    models.commit()
@bot.event
async def on_member_join(member: discord.guild.Member):
    user_id = member.id
    bank = 2000
    cash = 0
    user = models.User(user_id=user_id,cash=cash,bank=bank,invetory = {}, actions = {})
    models.save(user)
    channel = bot.get_channel(1046624731564081183)
    user = bot.get_user(member.id)
    embed = discord.Embed(description="Welcome to Bitcoin Bank!\n\nAccount Created successfully!")
    embed.set_author(name=str(user), icon_url=user.avatar.url)
    await channel.send(embed=embed)
@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=guild_id))
    print(f"We have loged in as {bot.user}")


def finish_lend(author_id,user_id,amount,timeout):
    session = models.create_session()
    time.sleep(timeout)
    author_bank = user_bank = models.filter(models.User.user_id == author_id, models.User,session=session).first()
    user_bank = models.filter(models.User.user_id == user_id, models.User,session=session).first()
    user_bank.cash -= amount
    author_bank.bank += amount
    models.save(user_bank,session=session)
    models.save(author_bank,session=session)


@tree.command(name="delete-user-account",description = "delete an user account", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
async def delete(interaction: discord.interactions.Interaction,user:discord.member.Member):
    user_id = user.id
    user_account = models.filter(models.User.user_id == user_id, models.User).first()
    if not user_account:
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return 
    models.filter(models.User.user_id == user_id, models.User).delete()
    models.commit()
    embed = discord.Embed(description=f"Account deleted successfully")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@delete.error
async def on_delete_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)

@tree.command(name="sell-action",description = "sell your actions", guild=discord.Object(id=guild_id))
async def sellaction(interaction: discord.interactions.Interaction,company:str, quantity: str = None):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:      
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if quantity is None and company.lower() != "all":
        embed = discord.Embed(description=f"the quantity must be specified")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    elif company.lower() != "all":
        quantity = quantity.lower()
        if not quantity.isdigit() and quantity != "all":
            embed = discord.Embed(description=f"invalid quantity: \"{quantity}\"")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
    company = company.lower()
    if company != "all":
        company = company.upper()

    if company == "all":
        value = 0
        companys = []
        for company, quantity in bank_user.actions.items():
            value += quantity * misc.get_price(company)
            companys.append(company)
        for comp in companys:
            bank_user.actions.pop(comp)
        bank_user.cash += int(math.ceil(value))
        embed = discord.Embed(description=f"all actions were sold successfully")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        if quantity.lower() == "all":
            quantity = bank_user.actions.get(company,0)
            if quantity == 0:
                embed = discord.Embed(description=f"you do not have enough actions")
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
                return
        if bank_user.actions[company] < quantity:
            embed = discord.Embed(description=f"you do not have enough actions")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        value = misc.get_price(company) * quantity
        bank_user.cash += int(math.ceil(value))
        bank_user.actions[company] -= quantity
        if bank_user.actions[company] == 0:
            bank_user.actions.pop(company)
        embed = discord.Embed(description=f"{quantity} {company}'s actions were sold successfully")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

    flag_modified(bank_user, "actions")
    models.save(bank_user)
@tree.command(name="show-actions",description = "show an user actions", guild=discord.Object(id=guild_id))
async def actions(interaction: discord.interactions.Interaction,user:discord.member.Member=None):
    if user is None:
        user_account = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        if not user_account:      
            embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        inv_owner = interaction.user
    else:
        user_account = models.filter(models.User.user_id == user.id, models.User).first()
        if not user_account:
            embed = discord.Embed(description="this user does not have an account")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return 
        inv_owner = user
    the_actions = user_account.actions
    if the_actions == {}:
        embed = discord.Embed(description=f"{inv_owner} does not have any action")
        embed.set_author(name=str(inv_owner), icon_url=inv_owner.avatar.url)
        await interaction.response.send_message(embed=embed)
        return 
    embed = discord.Embed()
    count = 1
    balance = 0
    for company, quantity in the_actions.items():
        price = misc.get_price(company)
        embed.add_field(name = f"`{count}`. {company} - {misc.bitcoin} {prettify_float_num(price)}",value = f"{company}'s actions `x{quantity}`\nvalue: {misc.bitcoin} {prettify_float_num(price*quantity)}",inline=False)
        balance += price*quantity
        count += 1
    embed.description = f"actions balance: {misc.bitcoin} {prettify_float_num(balance)}"
    embed.set_author(name=f"{str(inv_owner)}'s actions", icon_url=inv_owner.avatar.url)
    await interaction.response.send_message(embed=embed)
    

@tree.command(name="price",description = "show a company action price", guild=discord.Object(id=guild_id))
async def price(interaction: discord.interactions.Interaction,company:str):
    company = company.upper()
    price = misc.get_price(company)
    if price is None:
        embed = discord.Embed(description=f"not found company: {company}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(description=f"{misc.bitcoin} {prettify_float_num(price)} per {company}'s action")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)


@tree.command(name="buy-action",description = "buy a company action", guild=discord.Object(id=guild_id))
async def buyaction(interaction: discord.interactions.Interaction,company:str, quantity:str):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:      
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not quantity.isdigit() and quantity.lower() != "all":
        embed = discord.Embed(description=f"invalid quantity: \"{quantity}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    company = company.upper()
    price = misc.get_price(company)
    if price is None:
        embed = discord.Embed(description=f"not found company: {company}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    if quantity.lower() == "all":
        quantity = bank_user.cash // price 
    quantity = int(quantity)
    
    to_pay = price*quantity
    if bank_user.cash < to_pay:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    to_pay = int(to_pay)
    bank_user.cash -= to_pay
    bank_user.actions[company] = (bank_user.actions[company] + quantity if company in bank_user.actions.keys() else quantity)
    flag_modified(bank_user, "actions")
    models.save(bank_user)
    embed = discord.Embed(description=f"{quantity} {company} action{'s' if quantity > 1 else ''} purchased successfully")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="unuse-role",description = "remove a role from your profile", guild=discord.Object(id=guild_id))
async def restore(interaction: discord.interactions.Interaction,roleid:str):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    role = models.filter(models.Item.id == roleid, models.Item).first()
    roles = interaction.user.roles
    roles = [rol.id for rol in roles] 
    role_id = role.role_id
    if not role:
        embed = discord.Embed(description="this role does not exists")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not role_id in roles:
        embed = discord.Embed(description="you do not have this role in your profile")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    role = discord.utils.get(interaction.guild.roles, id = role_id)
    await interaction.user.remove_roles(role)
    await interaction.response.send_message("role removed from your profile successfully")
    
@tree.command(name="use-role",description = "use a role from your inventory", guild=discord.Object(id=guild_id))
async def userole(interaction: discord.interactions.Interaction, roleid:str):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not roleid in bank_user.inventory.keys():
        embed = discord.Embed(description="you do not have this role in your inventory")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    role = models.filter(models.Item.id == roleid, models.Item).first()
    if not role:
        embed = discord.Embed(description="this role does not exists")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not role.is_role:
        embed = discord.Embed(description="this item is not a role")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    items = models.filter(models.Item.id > 0, models.Item)
    roles = [item.role_id for item in items if item.is_role]
    for role_id in [rol.id for rol in interaction.user.roles]:
        if role_id in roles:
            embed = discord.Embed(description="you already have a color role")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return 
    role_id = role.role_id
    role = discord.utils.get(interaction.guild.roles, id = role_id)
    await interaction.user.add_roles(role)
    await interaction.response.send_message("role added successfully")

@tree.command(name="buy",description = "buy a role or item from the store", guild=discord.Object(id=guild_id))
async def buy(interaction: discord.interactions.Interaction,itemid: str):

    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if itemid in bank_user.inventory.keys():
        embed = discord.Embed(description="you already have this item in your inventory")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    item = models.filter(models.Item.id == itemid, models.Item).first()
    if not item:
        embed = discord.Embed(description="this role does not exists")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if bank_user.cash < item.price:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    bank_user.cash -= item.price
    bank_user.inventory[str(itemid)] = str(itemid)
    
    #si el item no es un rol, pero tiene un id de rol, el rol se agrega automaticamente al comprar
    if (not item.role_id is None) and (not item.is_role):
        role = discord.utils.get(interaction.guild.roles, id = item.role_id)
        await interaction.user.add_roles(role)
    
    flag_modified(bank_user, "inventory")
    models.save(bank_user)
    
    embed = discord.Embed(description=f"{'role' if item.is_role else 'item'} purchased successfully!")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)
    

@tree.command(name="remove-from-store",description = "remove a role from the store", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
async def removefromstore(interaction: discord.interactions.Interaction,item_id:str = None):
    if not item_id.isdigit():
        embed = discord.Embed(description=f"invalid role id: {item_id}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    item_id = int(item_id)
    #In case ID:
    if models.filter(models.Item.id == item_id, models.Item).first():
        models.filter(models.Item.id == item_id, models.Item).delete()
        models.commit()
        embed = discord.Embed(description=f"item removed successfully")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    else:
        embed = discord.Embed(description=f"not found item with ID equals to {item_id}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return  
@removefromstore.error
async def on_rfs_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):

    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)

@tree.command(name="add-to-store",description = "add a role to the store", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
async def addtostore(interaction: discord.interactions.Interaction, name: str, description:str, price:int , role_id: str = None, is_role: bool = False):
    if not role_id is None:
        if not role_id.isdigit():
            embed = discord.Embed(description=f"invalid role id: {role_id}")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        role_id = int(role_id)
        if models.filter(models.Item.role_id == role_id,models.Item).first() and is_role:
            embed = discord.Embed(description=f"this role already exists in the shop")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
    if models.filter(models.Item.name == name, models.Item).first():
        embed = discord.Embed(description=f"this item name already exists in the shop")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    role_item = models.Item(price=price,name=name,description=description,role_id=role_id, is_role = is_role)
    models.save(role_item)
    embed = discord.Embed(description=f"{'role' if is_role else 'item'} added successfully")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@addtostore.error
async def on_delete_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)
    
@tree.command(name="store",description = "show the store", guild=discord.Object(id=guild_id))
async def shop(interaction: discord.interactions.Interaction):
    embed = discord.Embed(description="use /buy-role, to buy a role\nuse /use-role, to use a role")
    if models.get_all(models.Item) == []:
        embed.add_field(name=f"Shop is empty", value="if you are an admin, use /add-to-store for add roles and items to the sotre",inline=False)
    count = 1
    for item in models.get_all(models.Item):
        embed.add_field(name=f"`{count}`. {item.name} `[ID {item.id}]({'role' if item.is_role else 'item'})` - {misc.bitcoin} {prettify_num(item.price)}", value=item.description,inline=False)
        count += 1
    await interaction.response.send_message(embed=embed)

@tree.command(name="inventory",description = "show your invetory", guild=discord.Object(id=guild_id))
async def inventory(interaction: discord.interactions.Interaction,user:discord.member.Member=None):
    if user is None:
        user_account = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        if not user_account:      
            embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        inv_owner = interaction.user
    else:
        user_account = models.filter(models.User.user_id == user.id, models.User).first()
        if not user_account:
            embed = discord.Embed(description="this user does not have an account")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return 
        inv_owner = user
    the_inventory = user_account.inventory
    if the_inventory == {}:
        embed = discord.Embed(description=f"{inv_owner}'s inventory is empty")
        embed.set_author(name=str(inv_owner), icon_url=inv_owner.avatar.url)
        await interaction.response.send_message(embed=embed)
        return 
    embed = discord.Embed()
    count = 1
    for id_item in the_inventory.keys():
        item = models.filter(models.Item.id == id_item, models.Item).first()
        if not item:
            user_account.invetory.pop(id_item)
            continue
        embed.add_field(name = f"`{count}`. {item.name} - `[ID {item.id}](is role: {item.is_role})`",value = f"{item.description}",inline=False)
        count += 1
    embed.set_author(name=f"{str(inv_owner)}'s inventory", icon_url=inv_owner.avatar.url)
    await interaction.response.send_message(embed=embed)

@tree.command(name="lend-money",description = "lending money to a user at a 10, 20 or 30 percent interest rate", guild=discord.Object(id=guild_id))
async def lend(interaction: discord.interactions.Interaction, user:discord.member.Member,amount: int):
    lender_bank = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not lender_bank:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    to_lend_bank = models.filter(models.User.user_id == user.id, models.User).first()
    if not to_lend_bank:
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if lender_bank.cash < amount:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if interaction.user.id == user.id:
        embed = discord.Embed(description="you cannot lend money to yourself")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed()
    embed.set_author(name=str(user), icon_url=user.avatar.url)
    await interaction.response.send_message(view=LendView({
        "amount": amount,
        "author_id": interaction.user.id,
        "user_id": user.id,
        "embed": embed
    }))
    
@tree.command(name="rob",description = "steals money from a user if he/she has money in his/her physical wallet", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild_id, i.user.id))
async def rob(interaction: discord.interactions.Interaction,user:discord.member.Member):
    bank_user = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    victim_user = models.filter(models.User.user_id == user.id,models.User).first()
    if not victim_user: 
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if victim_user.cash <= 0: 
        embed = discord.Embed(description="this user does not have bitcoins on his/her physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if victim_user.id == bank_user.id:
        embed = discord.Embed(description="you can't steal from yourself")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    percent = 80
    successfull = random.randint(1,10)
    theft = victim_user.cash * (percent / 100)
    if successfull > 4:    
        bank_user.cash += int(theft)
        victim_user.cash -= int(theft)
        models.save(bank_user)
        models.save(victim_user)
        embed = discord.Embed(description=f"you theft {bitcoin} {prettify_num(int(theft))} bitcoins from {user}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        bank_user.cash -= int(theft)
        models.save(bank_user)
        embed = discord.Embed(description=f"you got caught by the cyber police and had to pay {bitcoin} {prettify_num(int(theft))} bitcoins")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return

@rob.error
async def on_rob_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        rtime = int(error.retry_after // 60 if error.retry_after > 60 else error.retry_after)
        sufix = "m" if error.retry_after > 60 else "s"
        msg = f"you can modify a block and make a theft again in {rtime}{sufix}"
        await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name="slot-machine",description = "play slot machine", guild=discord.Object(id=guild_id))
async def slot(interaction: discord.interactions.Interaction ,amount:str):
    if not amount.isdigit() and amount != "all":
        embed = discord.Embed(description=f"invalid amount: \"{amount}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
        
    
    player_bank = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not player_bank:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if amount.isdigit():
        amount = int(amount)
    else:
        amount = player_bank.cash
    if amount <= 0:
        embed = discord.Embed(description="you may not bet amounts less than or equal to 0")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if (not player_bank.cash >= amount) or amount == 0:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    player_bank.cash -= amount
    models.save(player_bank)
    embed = discord.Embed()
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    win = random.randint(1,10)
    if win%2 == 0:
        embed.title = f"You win! {bitcoin} {prettify_num(amount*2)}"
        embed.description = random.choice(misc.win_slots)
        player_bank.cash += amount*2
        models.save(player_bank)
    else:
        embed.title = f"You lost {bitcoin} {prettify_num(amount)}"
        embed.description = random.choice(misc.lost_slots)
    await interaction.response.send_message(embed=embed)
    
@tree.command(name="blackjack",description = "play blackjack", guild=discord.Object(id=guild_id))
async def blackjack(interaction: discord.interactions.Interaction,amount:str):
    if not amount.isdigit() and amount != "all":
        embed = discord.Embed(description=f"invalid amount: \"{amount}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    player_bank = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if amount.isdigit():
        amount = int(amount)
    else:
        amount = player_bank.cash
    if amount <= 0:
        embed = discord.Embed(description="you may not bet amounts less than or equal to 0")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not player_bank:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if not player_bank.cash >= amount:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    player_bank.cash -= amount
    models.save(player_bank)
    embed = discord.Embed()
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    
    player_hand = random.randint(2,21)
    dealer_hand = random.randint(8,13)
    embed.add_field(name=f"Your hand:",value=f"{player_hand}")
    embed.add_field(name=f"Dealer hand:",value=f"{dealer_hand}")
    
    if player_hand == 21 and dealer_hand == 21:
        embed.title = "Draw"
        user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        user.cash += amount
        models.save(user)
        await interaction.response.send_message(embed=embed)
        return
    elif player_hand == 21:
        embed.title = f"You win! {bitcoin} {amount*2}"
        user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        user.cash += amount*2
        models.save(user)
        await interaction.response.send_message(embed=embed)
        return
    elif dealer_hand == 21:
        embed.title = f"You Lost {bitcoin} {amount}"
        user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        user.cash += amount*2
        models.save(user)
        await interaction.response.send_message(embed=embed)
        return
    await interaction.response.send_message(embed=embed,view=BlackJack(the_data={
        "hand":player_hand,
        "dhand": dealer_hand,
        "user_id":interaction.user.id,
        "amount": amount,
        }))
    

async def places_autocomplete(interaction: discord.Interaction, current: str) -> List[discord.app_commands.Choice[str]]:
        choices = ['cash', 'bank']
        return [
            discord.app_commands.Choice(name=From, value=From)
            for From in choices if current.lower() in From.lower()
        ]


@tree.command(name="leaderboard",description = "show the leaderboard", guild=discord.Object(id=guild_id))
@discord.app_commands.autocomplete(section=places_autocomplete)
async def top(interaction: discord.interactions.Interaction, section: str):
    if section == "bank":
        top_bank = models.filter(models.User.id > 0, models.User).order_by(desc(models.User.bank))
        top_bank = top_bank[:10]
        embed = discord.Embed(title="Top Bank")
        count = 1
        for account_user in top_bank:
            embed.add_field(name=f"#{count}: {bot.get_user(account_user.user_id)}",value=f"{bitcoin} {prettify_num(account_user.bank)}", inline=False)
            count += 1
        await interaction.response.send_message(embed=embed)
    elif section == "cash":
        top_cash = models.filter(models.User.id > 0, models.User).order_by(desc(models.User.cash))
        top_cash = top_cash[:10]
        embed = discord.Embed(title="Top Cash")
        count = 1
        for account_user in top_cash:
            embed.add_field(name=f"#{count}: {bot.get_user(account_user.user_id)}",value=f"{bitcoin} {prettify_num(account_user.cash)}", inline=False)
            count += 1
        await interaction.response.send_message(embed=embed)
    else:
        await interaction.response.send_message(f"not found section: \"{section}\"")

@tree.command(name = "add-money-to-all",description="add bitcoins to all accounts", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
async def addbitcoinsall(interaction: discord.interactions.Interaction, amount: int):
    
    for member in interaction.guild.members:
        account_user = models.filter(models.User.user_id == member.id,models.User).first()
        if account_user:
            account_user.bank += int(amount)
            models.save(account_user)
    embed = discord.Embed(description=f"{bitcoin} {prettify_num(int(amount))} bitcoins added to all accounts successfully!")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)
@addbitcoinsall.error
async def on_aball_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)
 


@tree.command(name = "start-all-user-accounts",description="add bitcoins to all accounts", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
async def startall(interaction: discord.interactions.Interaction):
    count = 0
    for member in interaction.guild.members:
        account_user = models.filter(models.User.user_id == member.id,models.User).first()
        if (not account_user ) and (not member.bot):
            count += 1
            user = models.User(user_id=member.id,cash=0,bank=2000,inventory={},actions={})
            models.save(user)
    embed = discord.Embed(description=f"{count} accounts created successfully!")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@startall.error
async def on_startall_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)

@tree.command(name = "remove-money",description="removes money from an user's account", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
@discord.app_commands.autocomplete(place=places_autocomplete)
async def takebitcoins(interaction: discord.interactions.Interaction,user:discord.member.Member,amount:int,place: str):
    account_user = models.filter(models.User.user_id == user.id,models.User).first()
    if not account_user:
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(user), icon_url=user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    if place == "bank":
        account_user.bank -= amount
    elif place == "cash":
        account_user.cash -= amount
    else:
        embed = discord.Embed(description=f"invalid place: {place}")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoins taken from {user}'s {place}")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)
@takebitcoins.error
async def on_tb_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)  


@tree.command(name = "set-money",description="set money to an user's account", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
@discord.app_commands.autocomplete(place=places_autocomplete)
async def setmoney(interaction: discord.interactions.Interaction,user:discord.member.Member,amount:int,place: str):
    account_user = models.filter(models.User.user_id == user.id,models.User).first()
    if not account_user:
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    if place == "bank":
        account_user.bank = amount
        models.save(account_user)
    elif place == "cash":
        account_user.cash = amount
        models.save(account_user)
    else:
        embed = discord.Embed(description=f"invalid place: \"{place}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoins setted to {user} in {place}")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)
    
@setmoney.error
async def on_sm_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)

@tree.command(name = "add-money",description="add money to an user's account", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(bancario_id)
@discord.app_commands.autocomplete(place=places_autocomplete)
async def addbitcoins(interaction: discord.interactions.Interaction,user:discord.member.Member,amount:int,place:str):
    account_user = models.filter(models.User.user_id == user.id,models.User).first()
    if not account_user:
        embed = discord.Embed(description="this user does not have an account")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return

    if place == "bank":
        account_user.bank += amount
        models.save(account_user)
    elif place == "cash":
        account_user.cash += amount
        models.save(account_user)
    else:
        embed = discord.Embed(description=f"invalid palce: \"{place}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoins added to {user} in {place}")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@addbitcoins.error
async def on_ab_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be bancario to use this command", ephemeral=True)
        
@tree.command(name = "transfer-money",description="transfer money to an user's account", guild=discord.Object(id=guild_id))
async def pay(interaction: discord.interactions.Interaction,user:discord.member.Member, amount:str ):
    
    if amount == "all" or amount.isdigit():
        bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
        account_user = models.filter(models.User.user_id == user.id, models.User).first()
        if not account_user:
            embed = discord.Embed(description="this user does not have an account")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        if not bank_user:
            embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        if interaction.user.id == user.id:
            embed = discord.Embed(description="you cannot transfer money to yourself")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
            return
        if amount == "all":
            cash = bank_user.cash
            bank_user.cash -= cash
            account_user.cash += cash
            models.save(bank_user)
            models.save(account_user)
            embed = discord.Embed(description=f"{bitcoin} {prettify_num(cash)} bitcoin{'s' if cash != 1 else ''} transferred to {user}")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            amount = int(amount)
            if bank_user.cash >= amount:
                bank_user.cash -= amount
                account_user.cash += amount
                models.save(bank_user)
                models.save(account_user)
                embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoin{'s' if amount != 1 else ''} transferred to {user}")
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
                embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description=f"invalid amount: \"{amount}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name = "withdraw",description="transfer money to your physical wallet", guild=discord.Object(id=guild_id))
async def withdraw(interaction: discord.interactions.Interaction, amount: str): 

    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    bank = bank_user.bank
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if amount == "all":
        bank_user.bank -= bank
        bank_user.cash += bank
        embed = discord.Embed(description=f"{bitcoin} {prettify_num(bank)} bitcoin{'s' if bank != 1 else ''} transferred to your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    elif amount.isdigit():
        amount = int(amount)
        if bank >= amount:
            bank_user.bank -= amount
            bank_user.cash += amount
            embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoin{'s' if amount != 1 else ''} transferred to your physical wallet")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(description="you do not have enough bitcoins in your online wallet")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description=f"invalid amount: \"{prettify_num(amount)}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name = "mine",description="make money mining FICTITIOUS bitcoins", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.cooldown(1, 3600, key=lambda i: (i.guild_id, i.user.id))
async def mine(interaction: discord.interactions.Interaction):
    amount = random.randint(400,1000)
    bank_user = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    bank_user.cash += amount
    models.save(bank_user)
    embed = discord.Embed(description=f"you mined {bitcoin} {prettify_num(amount)} bitcoins")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)

@mine.error
async def on_mine_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.CommandOnCooldown):
        rtime = int(error.retry_after // 60 if error.retry_after > 60 else error.retry_after)
        sufix = "m" if error.retry_after > 60 else "s"
        msg = f"next hash discovered in {rtime}{sufix}"
        await interaction.response.send_message(msg, ephemeral=True)

@tree.command(name = "deposit",description="transfer money to your online wallet", guild=discord.Object(id=guild_id))
async def deposit(interaction: discord.interactions.Interaction, amount: str):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if not bank_user:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    cash = bank_user.cash
    if amount == "all":
        bank_user.bank += cash
        bank_user.cash -= cash
        embed = discord.Embed(description=f"{bitcoin} {prettify_num(cash)} bitcoin{'s' if cash != 1 else ''} deposited to your online wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
    elif amount.isdigit():
        amount = int(amount)
        if cash >= amount:
            bank_user.bank += amount
            bank_user.cash -= amount
            embed = discord.Embed(description=f"{bitcoin} {prettify_num(amount)} bitcoin{'s' if amount != 1 else ''} deposited to your online wallet")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(description=f"invalid amount: \"{prettify_num(amount)}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)

@tree.command(name = "balance",description="show your account balance", guild=discord.Object(id=guild_id))
async def balance(interaction: discord.interactions.Interaction,user: discord.Member= None):
    user_id = interaction.user.id if user == None else user.id
    bank_user = models.filter(models.User.user_id == user_id, models.User).first()
    if user_id == interaction.user.id:
        if bank_user:
            top = models.filter(models.User.id > 0, models.User.user_id).order_by(desc(models.User.bank))
            top = list(top).index((interaction.user.id,)) + 1
            embed = discord.Embed()
            embed.add_field(name="Cash",value=f"{bitcoin} {prettify_num(bank_user.cash)}")
            embed.add_field(name="Bank",value=f"{bitcoin} {prettify_num(bank_user.bank)}")
            embed.add_field(name="Total",value=f"{bitcoin} {prettify_num(bank_user.cash + bank_user.bank)}")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
            embed.set_footer(text=f"Top: #{top}")
        else:
            embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
            embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    else:
        if bank_user:
            top = models.filter(models.User.id > 0, models.User.user_id).order_by(desc(models.User.bank))
            top = list(top).index((user.id,)) + 1
            embed = discord.Embed()
            embed.add_field(name="Cash",value=f"{bitcoin} {prettify_num(bank_user.cash)}")
            embed.add_field(name="Bank",value=f"{bitcoin} {prettify_num(bank_user.bank)}")
            embed.add_field(name="Total",value=f"{bitcoin} {prettify_num(bank_user.cash + bank_user.bank)}")
            embed.set_author(name=str(user), icon_url=user.avatar.url)
            embed.set_footer(text=f"Top: #{top}")
        else:
            embed = discord.Embed(description="this user does not have an account")
            embed.set_author(name=str(user), icon_url=user.avatar.url)
    await interaction.response.send_message(embed=embed)
   
@tree.command(name = "start",description="start your account", guild=discord.Object(id=guild_id))
async def start(interaction: discord.interactions.Interaction):
    bank_user = models.filter(models.User.user_id == interaction.user.id, models.User).first()
    if bank_user:
        embed = discord.Embed(description="You already have an account",color=0xdd0000)
        embed.set_author(name=str(user), icon_url=user.avatar.url)
        await interaction.response.send_message(embed=embed)
    else:
        user_id = interaction.user.id
        bank = 2000
        cash = 0
        inventory = {}
        actions = {}
        user = models.User(user_id=user_id,cash=cash,bank=bank,inventory = inventory, actions = actions)
        models.save(user)
        embed = discord.Embed(description="Account created successfully")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)


@tree.command(name = "fish",description="try your luck fishing", guild=discord.Object(id=guild_id))
@discord.app_commands.checks.has_role(fisher_id)
async def fish(interaction: discord.interactions.Interaction,bet: str):
    
    if not bet.isdigit() and bet != "all":
        embed = discord.Embed(description=f"invalid amount: \"{bet}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    player_bank = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not player_bank:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if bet.isdigit():
        bet = int(bet)
    else:
        bet = player_bank.cash
    if bet <= 0:
        embed = discord.Embed(description="you may not bet amounts less than or equal to 0")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    if (not player_bank.cash >= bet) or bet == 0:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    
    
    player_bank.cash -= bet
    models.save(player_bank)
    embed = discord.Embed()
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    win = random.randint(1,100)
    
    v0 = 30
    v1_2 = 25
    v3_4 = 14
    v5_6 = 13
    v7_8 = 8
    v9_10 = 6
    v11_15 = 4
    
    if 1 <= win <= v0:
        fishes = 0
    elif v0 < win <= (v0 + v1_2):
        fishes = random.randint(1,2)
    elif (v0 + v1_2) < win <= (v0 + v1_2 + v3_4):
        fishes = random.randint(3,4)
    elif (v0 + v1_2 + v3_4) < win <= (v0 + v1_2 + v3_4 + v5_6):
        fishes = random.randint(5,6)
    elif (v0 + v1_2 + v3_4 + v5_6) < win <= (v0 + v1_2 + v3_4 + v5_6 + v7_8):
        fishes = random.randint(7,8)
    elif (v0 + v1_2 + v3_4 + v5_6 + v7_8) < win <= (v0 + v1_2 + v3_4 + v5_6 + v7_8 + v9_10):
        fishes = random.randint(9,10)
    elif (v0 + v1_2 + v3_4 + v5_6 + v7_8 + v9_10) < win <= (v0 + v1_2 + v3_4 + v5_6 + v7_8 + v9_10 + v11_15):
        fishes = random.randint(11,15)
    
    percent_per_fish = 12.5
    if fishes == 0:
        embed.title = f"You lose {bitcoin} {prettify_num(bet)}"
        embed.description = "you caught 0 fishes"
    else:
        win_amount = int(math.ceil(bet * (1 + ((percent_per_fish*fishes)/100))))
        embed.title = f"You win! {bitcoin} {prettify_num(win_amount)}"
        embed.description = f"you caught {fishes} fish{'es' if fishes > 1 else ''}"
        player_bank.cash += win_amount
    
    models.save(player_bank)
    await interaction.response.send_message(embed=embed)
@fish.error
async def on_fish_error(interaction: discord.interactions.Interaction, error: discord.app_commands.AppCommandError):

    if isinstance(error, discord.app_commands.errors.MissingRole):
        await interaction.response.send_message("you must be fisherman to use this command\nyou can become a fisherman by buying it in the store.", ephemeral=True)

@tree.command(name = "guess-number",description="guess a number", guild=discord.Object(id=guild_id))
async def guess(interaction: discord.interactions.Interaction,bet: str):
    if not bet.isdigit() and bet != "all":
        embed = discord.Embed(description=f"invalid amount: \"{bet}\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    player_bank = models.filter(models.User.user_id == interaction.user.id,models.User).first()
    if not player_bank:
        embed = discord.Embed(description="you do not have an account\nuse \"/start\"")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    if bet.isdigit():
        bet = int(bet)
    else:
        bet = player_bank.cash
    if bet <= 0:
        embed = discord.Embed(description="you may not bet amounts less than or equal to 0")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    if (not player_bank.cash >= bet) or bet == 0:
        embed = discord.Embed(description="you do not have enough bitcoins in your physical wallet")
        embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
        await interaction.response.send_message(embed=embed)
        return
    
    player_bank.cash -= bet
    models.save(player_bank)
    
    
    number = random.randint(1,100)
    embed = discord.Embed(description="guess a number between 1 and 100\nyou have 5 attemps")
    embed.set_author(name=str(interaction.user), icon_url=interaction.user.avatar.url)
    await interaction.response.send_message(embed=embed)
    channel = interaction.channel
    i = 0
    while i < 5:
        msg: discord.message.Message = await bot.wait_for('message',check=lambda message: message.author.id == interaction.user.id)
        if not msg.content.isdigit():
            await msg.reply('the answer must be a number between 1 and 100')
            continue
        guess = int(msg.content)
        if not 0 < guess <= 100:
            await msg.reply('the answer must be a number between 1 and 100')
            continue
        if guess == number:
            player_bank.cash += bet*2
            models.save(player_bank)
            await msg.reply(f'Congratulations! You won {bitcoin} {bet*2}')
            break
        elif i == 4:
            await msg.reply("You lose :(")
            break
        elif guess > number: 
            await msg.reply(f'the number is less than {guess}')
        else:
            await msg.reply(f'the number is greater than {guess}')
        i += 1




@bot.event
async def on_message(message: discord.message.Message):
    author_id = message.author.id
    if author_id == bot.user.id:
        return
    # add 10 bitcoins to cash per message
    bank_user = models.filter(models.User.user_id == author_id, models.User).first()
    if bank_user:
        bank_user.cash += 10
        models.save(bank_user)
    







token = "YOUR-TOKEN-HERE"
if __name__ == '__main__':
    bot.run(token)