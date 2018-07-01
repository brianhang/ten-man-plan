import discord
import pickledb
import os
from discord.ext import commands
from itertools import combinations
from random import choice

bot = commands.Bot(command_prefix='!', description='10 man game planner')
db = pickledb.load('tenman.db', False)
lobby_list = []

threshold = 10
team_size = 10

def get_score(user):
    return db.get(user.id) or 0

def gen_teams():
    players = [(get_score(user), user.display_name) for user in lobby_list]
    options = []
    num_players = len(lobby_list)

    for choices in combinations(range(num_players), num_players // 2):
        team_a = 0
        team_a_players = []
        team_b = 0
        team_b_players = []

        for i in range(num_players):
            if i in choices:
                team_a += players[i][0]
                team_a_players.append(players[i][1])
            else:
                team_b += players[i][0]
                team_b_players.append(players[i][1])

        if abs(team_a - team_b) < threshold:
            options.append((team_a, team_b, team_a_players, team_b_players))

    return choice(options)

@bot.command()
async def getrank(ctx):
    message = ctx.message
    num_mentions = len(message.mentions)

    if num_mentions == 0:
        user = message.author
    elif num_mentions == 1:
        user = message.mentions[0]
    else:
        await ctx.send('You can only mention at most one user.')
        return
    
    user = message.mentions[0]
    rank = get_score(user)

    await ctx.send('{} is rank {}'.format(user.display_name, rank))

@bot.command()
async def setrank(ctx, _, new_rank: int):
    message = ctx.message

    if len(message.mentions) != 1:
        await ctx.send('You must mention a user.')
        return

    user = message.mentions[0]
    db.set(user.id, new_rank)

    await ctx.send('{} is now rank {}'.format(user.display_name, new_rank))

@bot.command()
async def resetlobby(ctx):
    global lobby_list

    lobby_list = []
    await ctx.send('The 10-man lobby has been reset. Type `!joinlobby` to join the lobby for the next 10-man game.')

@bot.command()
async def joinlobby(ctx):
    global lobby_list
    
    user = ctx.message.author

    if user in lobby_list:
        return

    lobby_list.append(user)
    await ctx.send('{} has joined the 10-man lobby.'.format(user.display_name))

    if len(lobby_list) >= team_size:
        await ctx.send('Creating teams...\n\n\n')

        team_a, team_b, team_a_players, team_b_players = gen_teams()
        lobby_list = []

        await ctx.send('**TEAM A** ({})'.format(team_a))
        await ctx.send('\n'.join(team_a_players))
        await ctx.send('**TEAM B** ({})'.format(team_b))
        await ctx.send('\n'.join(team_b_players))

@bot.command()
async def leavelobby(ctx):
    global lobby_list

    user = ctx.message.author

    if user not in lobby_list:
        return

    lobby_list.remove(user)
    await ctx.send('{} has left the 10-man lobby.'.format(user.display_name))

@bot.command()
async def lobby(ctx):
    num_lobby = len(lobby_list)

    if num_lobby > 0:
        await ctx.send('**10-man Lobby:**')

        output = []

        for i in range(team_size):
            if i >= num_lobby:
                name = ''
            else:
                name = lobby_list[i].display_name

            output.append('{}. {}'.format(i + 1, name))

        await ctx.send('\n'.join(output))
    else:
        await ctx.send('The 10-man lobby is currently empty.')

bot.run(os.environ['DISCORD_TOKEN'])
