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
        self.latest_status = None  # 가장 최근 상태를 저장
        self.status_update_event = asyncio.Event()  # 상태 변경 이벤트

    async def StreamFanStatus(self, request, context):
        """ 팬 상태가 변경될 때마다 클라이언트에 스트리밍 전송 """
        if self.latest_status:
            yield self.latest_status  # 연결 시 최신 데이터 1개 전송

        while True:
            await self.status_update_event.wait()  # 상태 변경이 있을 때까지 대기
            self.status_update_event.clear()  # 이벤트 초기화
            yield self.latest_status  # 최신 상태 전송

    async def SetFanConfig(self, request, context):
        """ 클라이언트가 팬 설정을 변경하면 반영 """
        self.fan_status.is_fan_on = request.is_fan_on
        self.fan_status.off_temperature = request.off_temperature
        self.fan_status.on_temperature = request.on_temperature
        self.fan_status.control_off_time = request.control_off_time
        self.fan_status.control_on_time = request.control_on_time

        self.fan_status.update()

        return control_pb2.FanConfigResponse(success=True, message="Fan configuration updated successfully.")

    def _on_updated(self):
        """ 팬 상태가 변경될 때 최신 데이터만 유지하고 이벤트를 트리거 """
        self.latest_status = control_pb2.FanStatusResponse(
            is_fan_on=self.fan_status.is_fan_on,
            current_temperature=self.fan_status.current_temperature,
            off_temperature=self.fan_status.off_temperature,
            on_temperature=self.fan_status.on_temperature,
            control_off_time=self.fan_status.control_off_time,
            control_on_time=self.fan_status.control_on_time
        )
        self.status_update_event.set()  # 대기 중인 클라이언트에 즉시 알림

class Server:
    def __init__(self, fan_status: FanStatus):
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
