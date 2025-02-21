import asyncio
import grpc
from concurrent import futures

import proto.control_pb2 as control_pb2
import proto.control_pb2_grpc as control_pb2_grpc

from data.fan_status import FanStatus

class FanControlService(control_pb2_grpc.FanControlServiceServicer):
    def __init__(self, fan_status: FanStatus):
        self.fan_status = fan_status
        self.fan_status.add_update_listener(self._on_updated)
        self.status_update_queue = asyncio.Queue()  # 상태 변경 이벤트를 관리할 큐

    async def StreamFanStatus(self, request, context):
        """ 팬 상태가 변경될 때마다 클라이언트에 스트리밍 전송 """
        while True:
            update = await self.status_update_queue.get()  # 상태 변경이 있을 때까지 대기
            yield control_pb2.FanStatusResponse(
                is_fan_on=self.fan_status.is_fan_on,
                current_temperature=self.fan_status.current_temperature,
                off_temperature=self.fan_status.off_temperature,
                on_temperature=self.fan_status.on_temperature,
                control_off_time=self.fan_status.control_off_time,
                control_on_time=self.fan_status.control_on_time
            )

    async def SetFanConfig(self, request, context):
        """ 클라이언트가 팬 설정을 변경하면 반영 """
        self.fan_status.is_fan_on = request.is_fan_on
        self.fan_status.off_temperature = request.off_temperature
        self.fan_status.on_temperature = request.on_temperature
        self.fan_status.control_off_time = request.control_off_time
        self.fan_status.control_on_time = request.control_on_time

        self.fan_status.update()

        return control_pb2.FanConfigResponse(success=True, message="Fan configuration updated successfully.")

    def _on_updated(self) :
        asyncio.create_task(self.status_update_queue.put(True))

class Server :
    def __init__(self, fan_status: FanStatus) :
        self.fan_status = fan_status

    async def serve(self):
        """ gRPC 서버 실행 """
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
        self.service = FanControlService(self.fan_status)
        control_pb2_grpc.add_FanControlServiceServicer_to_server(self.service, self.server)
        self.server.add_insecure_port('[::]:50051')  # 포트 50051에서 수신
        await self.server.start()
        print("🚀 gRPC 서버가 50051 포트에서 실행 중...")
        await self.server.wait_for_termination()
