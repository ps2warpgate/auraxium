# type: ignore
# pylint: disable=unused-variable
"""Example for creating custom helper functions via low-level queries.

This script is part of the "Custom Queries" section in the docs and
showcases how to switch between the low-level queries used by the
``auraxium.census`` module, and the high-level object model.
"""

import asyncio
from typing import List

import auraxium


async def get_online_friends(char: auraxium.ps2.Character,
                             client: auraxium.Client
                             ) -> List[auraxium.ps2.Character]:
    """Return the online friends of the given character."""
    query = char.query()

    # Join the characters' friends
    join = query.create_join('characters_friend')
    join.set_inject_at('friends')

    # Join the friends' character
    char_join = join.create_join('character')
    char_join.set_fields('friend_list.character_id', 'character_id')
    char_join.set_inject_at('character')

    data = await client.request(query)
    friends_data = data['character_list'][0]['friends']['friend_list']
    online_friends = [
        f['character'] for f in friends_data if int(f['online']) != 0]

    return [auraxium.ps2.Character(d, client) for d in online_friends]


async def main():
    """Main script method."""
    client = auraxium.Client(service_id='s:MUMSOutfitRoster')
    char = await client.get_by_name(auraxium.ps2.Character, 'Auroram')
    char_query = char.query()

    online_friends = await get_online_friends(char, client)
    print(online_friends)

    await client.close()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
