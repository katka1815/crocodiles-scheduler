import asyncio
from spond import spond as sp

async def main():
    s = sp.Spond(username='katka1255@seznam.cz', password='MySpondPassWord1')
    group = await s.get_group('DDEC85288D0442F38F280F4420E045DC')
    print('Podskupiny:')
    for sg in group.get('subGroups', []):
        print(' -', sg['name'])
    print('Hotovo')
    await s.clientsession.close()

asyncio.run(main())
