# The MIT License (MIT)
#
# Copyright (c) 2015 QuiteQuiet<https://github.com/QuiteQuiet>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import requests
import robot as r
from plugins.games.game import GenericGame


class Workshop(GenericGame):
    def __init__(self, host):
        self.host = host
        self.team = []

    def addPokemon(self, poke):
        if len(self.team) >= 6:
            return 'team is full'
        self.team.append(poke)
        return '{mon} added'.format(mon=poke)

    def removePokemon(self, poke):
        if poke in self.team:
            self.team.remove(poke)
            return '{mon} removed'.format(mon=poke)
        return '{mon} is not in the team'.format(mon=poke)

    def getTeam(self):
        if len(self.team) <= 0:
            return 'team is empty'
        return ' / '.join(self.team)

    def clearTeam(self):
        self.team = []
        return 'team cleared'

    def logSession(self, room, user, message):
        file_path = 'logs/{room}-workshop-{host}.txt'.format(room=room,
                                                             host=self.host)
        with open(file_path, 'a') as log:
            log.write('{name}: {text}\n'.format(name=user, text=message))

    def pasteLog(self, room, apiKey):
        if apiKey == '0':
            return 'No paste for the workshop could be generated'
        file_path = 'logs/{room}-workshop-{host}.txt'.format(room=room,
                                                             host=self.host)
        with open(file_path, 'r') as log:
            r = requests.post('http://pastebin.com/api/api_post.php',
                              data={'api_dev_key': apiKey, 'api_option': 'paste', 'api_paste_code': log.read(),
                                    'api_paste_private': 0, 'api_paste_expire_date': 'N'})
            if 'Bad API request' in r.text:
                return 'Something went wrong ({error})'.format(error=r.text)
            return r.text

    def hasHostingRights(self, user):
        return self.host == user.id or user.hasRank('@')


def handler(bot, cmd, room, msg, user):
    reply = r.ReplyObject('', True)
    if msg.startswith('new'):
        if not user.hasRank('@'):
            return reply.response("You don't have permission to start "
                                  "workshops (Requires @)")
        if room.activity:
            return reply.response('A room.activity is already in progress')
        host = bot.toId(msg[len('new '):]) if msg[len('new '):] else user.id
        room.activity = Workshop(host)
        return reply.response('A new workshop session was created')

    if not (room.activity and room.activity.isThisGame(Workshop)):
        return reply.response('No Workshop in progress right now')
    workshop = room.activity
    if msg.startswith('add'):
        if not workshop.hasHostingRights(user):
            return reply.response('Only the workshop host or a Room Moderator can add Pokemon')
        return reply.response(workshop.addPokemon(msg[4:].strip()))
    elif msg.startswith('remove'):
        if not workshop.hasHostingRights(user):
            return reply.response('Only the workshop host or a Room Moderator can remove Pokemon')
        return reply.response(workshop.removePokemon(msg[7:].strip()))
    elif msg == 'clear':
        if not workshop.hasHostingRights(user):
            return reply.response('Only the workshop host or a Room Moderator can clear the team')
        return reply.response(workshop.clearTeam())
    elif msg == 'team':
        return reply.response(workshop.getTeam())
    elif msg == 'end':
        if not workshop.hasHostingRights(user):
            return reply.response('Only the workshop host or a Room Moderator can end the workshop')
        bot.sendPm(user.id, workshop.pasteLog(room.title, bot.apikeys['pastebin']))
        room.activity = None
        return reply.response('Workshop session ended')
    unreg_cmd = msg if msg else 'nothing'
    return reply.response('Unrecognized command: {cmd}'.format(unreg_cmd))
