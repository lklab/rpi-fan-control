if __name__ == "__main__" :
    from pathlib import Path
    import sys

    path_root = Path(__file__).resolve().parent
    while path_root.name != 'rpi-fan-control' :
        path_root = path_root.parent

    sys.path.append(str(path_root))

import asyncio
import grpc
import proto.control_pb2 as control_pb2
import proto.control_pb2_grpc as control_pb2_grpc
import json

async def receive_status_updates(stub, key: str):
    """ 서버에서 상태 변경 스트리밍 받기 """
    async for response in stub.StreamFanStatus(control_pb2.FanStatusRequest(
        key=key,
    )):
        print(f"📢 팬 상태 변경 감지! 현재 상태:")
        print(f"    - 팬 ON: {response.is_fan_on}")
        print(f"    - 현재 온도: {response.current_temperature}°C")
        print(f"    - ON 온도: {response.on_temperature}°C, OFF 온도: {response.off_temperature}°C")
        print(f"    - 제어 ON 시간: {response.control_on_time}, 제어 OFF 시간: {response.control_off_time}")

async def send_fan_config(stub):
    """ 서버에 팬 설정 변경 요청 """
    request = control_pb2.FanConfigRequest(
        is_fan_on=True,
        off_temperature=28.0,
        on_temperature=22.0,
        control_off_time="22:00",
        control_on_time="06:00"
    )
    response = await stub.SetFanConfig(request)
    print(f"✅ 설정 변경 결과: {response.message}")

async def main():
    """ gRPC 클라이언트 실행 """
    with open('config/server_config.json', encoding='utf-8') as f :
        config = json.load(f)
    key: str = config['whitelist'][0]

    async with grpc.aio.insecure_channel('localhost:50051') as channel:
        stub = control_pb2_grpc.FanControlServiceStub(channel)

        # 비동기로 상태 스트리밍 수신 & 설정 변경 요청
        await asyncio.gather(
            receive_status_updates(stub, key),
            # send_fan_config(stub)
        )

if __name__ == '__main__':
    asyncio.run(main())
