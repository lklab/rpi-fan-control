import asyncio

from controller.controller import Controller
from network.server import Server
from data.fan_status import FanStatus

async def main() :
    fan_status = FanStatus()
    controller = Controller(fan_status)
    controller.start()
    server = Server(fan_status)
    await server.serve()

if __name__ == '__main__':
    try :
        asyncio.run(main())
    except KeyboardInterrupt :
        pass
