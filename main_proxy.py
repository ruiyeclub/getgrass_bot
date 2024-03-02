# -*- coding: utf-8 -*-
# @Time     :2023/12/26 17:00
# @Author   :ym
# @File     :main.py
# @Software :PyCharm
import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
import requests


async def connect_to_wss(socks5_proxy, user_id):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"
            server_hostname = "proxy.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(20)

                # asyncio.create_task(send_http_request_every_10_seconds(socks5_proxy, device_id))
                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "extension",
                                "version": "2.5.0"
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)

def get_proxy_list():
    # TODO https://www.juliangip.com/
    url = ''
    response = requests.get(url)
    socks5_proxy_list = []
    if response.status_code == 200:
        # 解析 JSON 字符串
        data = response.json()
        # 从数据中提取 proxy_list
        proxy_list = data['data']['proxy_list']
        # 转换 proxy_list 中的每个元素为所需的格式
        for proxy in proxy_list:
            parts = proxy.split(':')
            socks5_proxy_list.append("socks5://{}:{}@{}:{}".format(parts[2], parts[3], parts[0], parts[1]))
        # 输出结果
        print(socks5_proxy_list)
        return socks5_proxy_list
    else:
        print('请求失败')
        return socks5_proxy_list


async def main():
    # TODO 修改user_id
    _user_id = ''
    # TODO 修改代理列表
    socks5_proxy_list = get_proxy_list()
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in socks5_proxy_list]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    # # 运行主函数
    asyncio.run(main())
