import discord
import pickledb
import os
from discord.ext import commands
from itertools import combinations
from random import choice

bot = commands.Bot(command_prefix='!', description='10 man game planner')
db = pickledb.load('tenman.db', False)

last_lobby = None
lobby_list = []

# Thresholds for team point differences.
default_threshold = 10
max_threshold = 100

# Number of people needed to form teams.
lobby_size = 10

def get_score(user):
    return db.get(user.id) or 0

def gen_teams(threshold=default_threshold):
    global lobby_list

    players = [(get_score(user), user.display_name) for user in lobby_list]
    options = []

    # Team size is lobby size / 2.
    num_players = len(lobby_list)
    to_choose = max(num_players // 2, 1)

    # Find all possible team setups.
    for choices in combinations(range(num_players), to_choose):
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

        if abs(team_a - team_b) <= threshold:
            options.append((team_a, team_b, team_a_players, team_b_players))

    # Return a random team setup.
    if options:
        return choice(options)

    # wtf lol
    elif threshold <= max_threshold:
        return gen_teams(threshold + 5)
    else:
        return -1, -1, [], []

async def show_teams(ctx):
    global lobby_list, last_lobby

    await ctx.send('Creating teams...')

    team_a, team_b, team_a_players, team_b_players = gen_teams()

    if team_a == -1:
        await ctx.send('Failed to create teams! Report this to Brian 😒')
        return

    last_lobby = lobby_list
    lobby_list = []

    messages = [
        '**TEAM A** ({})'.format(team_a),
        '\n'.join(team_a_players),
        '\n',
        '**TEAM B** ({})'.format(team_b),
        '\n'.join(team_b_players)
    ]

    await ctx.send('\n'.join(messages))

@bot.command()
async def getrank(ctx):
    message = ctx.message
    num_mentions = len(message.mentions)

    # If no one is mentioned, get rank of author. Otherwise, get rank of target.
    if num_mentions == 0:
        user = message.author
    elif num_mentions == 1:
        user = message.mentions[0]
    else:
        await ctx.send('You can only mention at most one user.')
        return
    
    rank = get_score(user)
    await ctx.send('{} is rank {}'.format(user.display_name, rank))

@bot.command()
async def setrank(ctx, mentioned_user, new_rank: int):
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

    if len(lobby_list) >= lobby_size:
        await show_teams(ctx)

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

        for i in range(lobby_size):
            if i >= num_lobby:
                name = ''
            else:
                name = lobby_list[i].display_name

            output.append('{}. {}'.format(i + 1, name))

        await ctx.send('\n'.join(output))
    else:
        await ctx.send('The 10-man lobby is currently empty.')

@bot.command()
async def lobbyadd(ctx):
    added = []

    for user in ctx.message.mentions:
        if len(lobby_list) >= lobby_size:
            break

        if user not in lobby_list:
            lobby_list.append(user)
            added.append(user.display_name)

    if added:
        names = ', '.join(added)
    else:
        names = 'No one'

    await ctx.send('{} has been added to the lobby.'.format(names))

    if len(lobby_list) >= lobby_size:
        await show_teams(ctx)

@bot.command()
async def lobbyremove(ctx):
    global lobby_list

    mentions = ctx.message.mentions
    lobby_list = [user for user in lobby_list if user not in mentions]

    if mentions:
        names = ', '.join([user.display_name for user in mentions])
    else:
        names = 'No one'

    ctx.send('{} has been removed from the lobby.'.format(names))

@bot.command()
async def lobbyreroll(ctx):
    global last_lobby, lobby_list

    if not last_lobby:
       await ctx.send('There is no previous lobby to reroll.') 
    else:
        lobby_list = last_lobby
        await show_teams(ctx)

bot.run(os.environ['DISCORD_TOKEN'])
